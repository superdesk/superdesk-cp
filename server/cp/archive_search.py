import logging
import time
import random
from datetime import datetime, timedelta, timezone, date
from typing import Any, Dict

import requests
from flask import current_app as app
import superdesk
from superdesk.utils import ListCursor
from superdesk.search_provider import SearchProvider
from superdesk.utc import utc_to_local

logger = logging.getLogger(__name__)


class ArchiveListCursor(ListCursor):
    def __init__(self, docs, count):
        super().__init__(docs)
        self._count = count

    def __len__(self):
        return len(self.docs)

    def count(self, **kwargs):
        return self._count


class ArchiveSearchProvider(SearchProvider):
    label = "Archive Search"

    TZ = "UTC"

    DATETIME_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]

    SORT_KEYS = ["versioncreated", "firstcreated"]

    QUERY_KEYS = [
        "query_text",
        "headline",
        "story_text",
        "slugline",
        "slugline_exact",
    ]

    SELECT_KEYS = ["categories", "distribution", "languages", "source"]

    SEARCH_RETRY_CODES = [429, 502, 503, 504]

    def __init__(self, provider):
        super().__init__(provider)
        self.config = provider.get("config") or {}

        self.api_base = app.config.get("ARCHIVE_SEARCH_API_BASE_URL", "").rstrip("/")
        self.api_path = app.config.get("ARCHIVE_SEARCH_API_SEARCH_PATH", "/search")
        self.api_key = app.config.get("ARCHIVE_SEARCH_API_KEY", "")
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "cp-archive-search-provider/1.0",
            **({"x-api-key": self.api_key} if self.api_key else {}),
        }

        if not self.api_base:
            raise RuntimeError("ARCHIVE_SEARCH_API_BASE_URL is not configured")

        self.timeout_seconds = int(
            app.config.get("ARCHIVE_SEARCH_API_TIMEOUT_SECONDS", 15)
        )
        self.max_retries = int(app.config.get("ARCHIVE_SEARCH_API_MAX_RETRIES", 3))
        self.retry_min_sleep = float(
            app.config.get("ARCHIVE_SEARCH_API_RETRY_MIN", 0.2)
        )
        self.retry_max_sleep = float(
            app.config.get("ARCHIVE_SEARCH_API_RETRY_MAX", 0.8)
        )

        self.search_profile = app.config.get("ARCHIVE_SEARCH_PROFILE", None)

        self.default_sort = app.config.get(
            "ARCHIVE_SEARCH_DEFAULT_SORT", "versioncreated:desc"
        ).strip()

        self.default_recent_days = int(
            app.config.get("ARCHIVE_SEARCH_DEFAULT_RECENT_DAYS", 30)
        )

        logger.info(
            "ArchiveSearchProvider using API: %s%s (timeout=%ss, retries=%d)",
            self.api_base,
            self.api_path,
            self.timeout_seconds,
            self.max_retries,
        )

    def _parse_datetime(self, value):
        for fmt in self.DATETIME_FORMATS:
            try:
                dt = datetime.strptime(str(value).strip(), fmt)

                return utc_to_local(self.TZ, dt)
            except ValueError:
                continue

        return None

    def _parse_date(self, value):
        try:
            return date.fromisoformat(str(value).strip())
        except (ValueError, TypeError):
            return None

    def find(self, query=None, params=None):
        logger.info("Frontend query=%s params=%s", query, params)

        if query is None:
            query = {}

        if params is None:
            params = {}

        size = int(query.get("size", 50))
        frm = int(query.get("from", 0))

        try:
            sort = query.get("sort")[0]
        except (IndexError, AttributeError, TypeError):
            sort = {"versioncreated": "desc"}

        if any(k in sort for k in self.SORT_KEYS):
            params["sort"] = sort

        has_query = any(bool(params.get(k, "").strip()) for k in self.QUERY_KEYS)

        if not has_query:
            query_text = self._extract_query_text_from_es(query)
            if query_text:
                params["query_text"] = query_text

        try:
            api_params = self._build_api_params(params, size, frm)

            logger.info("Final API params: %s", api_params)

            items, total = self._api_search(api_params)
            logger.info("API returned %d items of total %s", len(items), total)

            return ArchiveListCursor(self._transform_items(items), total)
        except Exception:
            logger.exception("Archive API search failed")
            return ArchiveListCursor([], 0)

    @staticmethod
    def _extract_query_text_from_es(es_query: dict) -> str | None:
        try:
            query = es_query.get("query", {}).get("filtered", {}).get("query", {})
            query_string = query.get("query_string") or query.get("simple_query_string")
            if not query_string:
                return None

            return query_string.get("query").strip()
        except (AttributeError, TypeError):
            return None

    def _build_api_params(self, params: Dict[str, Any], size: int, frm: int):
        qtext = (params.get("query_text") or "").strip()
        headline = (params.get("headline") or "").strip()
        story_text = (params.get("story_text") or "").strip()
        slugline_exact = (params.get("slugline_exact") or "").strip()
        slugline = (params.get("slugline") or "").strip()
        byline = (params.get("byline") or "").strip()
        use_phrase = bool(params.get("use_phrase", False))
        date = self._parse_date(params.get("date"))
        from_date = params.get("from_date")
        to_date = params.get("to_date")
        raw_from_date = params.get("from")
        raw_to_date = params.get("to")

        logger.info(
            "Provider received date-ish from/to? from=%r to=%r",
            raw_from_date,
            raw_to_date,
        )

        sort = params.get("sort")
        if isinstance(sort, dict):
            sort = ",".join(f"{k}:{v}" for k, v in sort.items())

        out: Dict[str, Any] = {
            "limit": size,
            "from": max(0, int(frm)),
            "types": "text",
            **({"sort": sort} if sort else {"sort": self.default_sort}),
            **({"text": qtext} if qtext else {}),
            **({"text": story_text} if not qtext and story_text else {}),
            **({"headline": headline} if headline else {}),
            **({"slugline": slugline_exact, "phrase": True} if slugline_exact else {}),
            **({"slugline": slugline} if not slugline_exact and slugline else {}),
            **({"phrase": True} if use_phrase else {}),
            **({"byline": byline} if byline else {}),
            **(
                {"from_date": from_date, "to_date": to_date}
                if self._parse_date(date)
                else {}
            ),
            **({"from_date": from_date} if self._parse_date(from_date) else {}),
            **({"to_date": to_date} if self._parse_date(to_date) else {}),
            **({"from_date": raw_from_date} if self._parse_date(raw_from_date) else {}),
            **({"to_date": raw_to_date} if self._parse_date(raw_to_date) else {}),
            **{
                key: ",".join(params[key] or [])
                for key in self.SELECT_KEYS
                if key in params
            },
        }

        no_text = not any(
            [qtext, headline, story_text, slugline_exact, slugline, byline]
        )
        no_dates = not any([out.get("from_date"), out.get("to_date")])
        if no_text and no_dates:
            today = datetime.now(timezone.utc).date()
            out["from_date"] = (
                today - timedelta(days=self.default_recent_days)
            ).isoformat()
            out["to_date"] = (today + timedelta(days=1)).isoformat()

        return out

    def _api_search(self, api_params: Dict[str, Any]):
        last_err: Any = None

        with requests.Session() as session:
            url = f"{self.api_base}{self.api_path}"

            for attempt in range(1, self.max_retries + 1):
                try:
                    req = requests.Request(
                        "GET", url, headers=self.headers, params=api_params
                    )
                    prepared = req.prepare()
                    logger.info("API call (attempt %d): %s", attempt, prepared.url)

                    resp = session.send(prepared, timeout=self.timeout_seconds)

                    if 200 <= resp.status_code < 300:
                        data = resp.json() if resp.content else {}
                        return self._normalize_api_response(data)

                    if resp.status_code in self.SEARCH_RETRY_CODES:
                        last_err = RuntimeError(
                            f"Retryable status {resp.status_code}: {resp.text[:200]}"
                        )
                        self._handle_search_retry(
                            f"Retryable API error {resp.status_code}", attempt
                        )
                        continue

                    raise RuntimeError(
                        f"Archive API error {resp.status_code}: {resp.text[:500]}"
                    )
                except (requests.Timeout, requests.ConnectionError) as e:
                    last_err = e
                    self._handle_search_retry(
                        f"Retryable API error res:{resp} err:{e}", attempt
                    )
                    continue
                except Exception as e:
                    if attempt < self.max_retries:
                        last_err = e
                        self._handle_search_retry(
                            f"Retryable API error res:{resp} err:{e}", attempt
                        )
                        continue
                    raise

        if last_err:
            raise last_err
        return [], 0

    def _normalize_api_response(self, data: Dict[str, Any]):
        if not isinstance(data, dict):
            return [], 0

        items = data.get("items") or data.get("hits") or data.get("results") or []
        if not isinstance(items, list):
            items = []

        total: int = data.get("total", {})
        total = (
            total
            if isinstance(total, int)
            else total.get("value")
            if isinstance(total, dict) and isinstance(total.get("value"), int)
            else data.get("total_count")
            if isinstance(data.get("total_count"), int)
            else len(items)
        )

        normalized_items = []
        for it in items:
            if "item" in it and isinstance(it["item"], dict):
                normalized_items.append(it)
                continue

            if isinstance(it, dict) and any(
                k in it for k in ("uri", "type", "headlines", "bodies")
            ):
                normalized_items.append({"item": it})
            else:
                normalized_items.append(it)

        return normalized_items, int(total)

    def _handle_search_retry(self, msg: str, attempt: int):
        sleep_s = self._jitter_sleep(attempt)
        logger.warning("%s; sleeping %.2fs", msg, sleep_s)
        time.sleep(sleep_s)

    def _jitter_sleep(self, attempt: int) -> float:
        base = min(self.retry_max_sleep, self.retry_min_sleep * (2 ** (attempt - 1)))
        return random.uniform(self.retry_min_sleep, base)

    def _transform_items(self, items):
        def get_nested(obj, path, default=""):
            try:
                for key in path:
                    obj = obj[key]
                return obj
            except (KeyError, IndexError, TypeError):
                return default

        def pick_headline_from_arrays(headlines, role):
            if not isinstance(headlines, list):
                return ""
            return next(
                (h.get("value", "") for h in headlines if h.get("role") == role), ""
            )

        def pick_any_headline(headlines):
            if not isinstance(headlines, list):
                return ""
            return next((h.get("value", "") for h in headlines if "value" in h), "")

        def pick_body_from_arrays(bodies):
            if not isinstance(bodies, list):
                return ""
            html = next(
                (b.get("value") for b in bodies if b.get("role") == "html"), None
            )
            if html:
                return html
            return next(
                (b.get("value") for b in bodies if b.get("role") == "text"), ""
            )  # fallback

        def prefer_top_level(whole: dict, data: dict, key: str, default=""):
            v = whole.get(key)
            if v is None or v == "":
                v = data.get(key, default)
            return v if v is not None else default

        transformed = []
        for whole in items:
            data = whole.get("item", {}) if isinstance(whole, dict) else {}

            hl_ext = (
                whole.get("headline_extended") or data.get("headline_extended") or ""
            )
            hl_main = whole.get("headline_main") or data.get("headline_main") or ""
            body_html = whole.get("body_html") or data.get("body_html") or ""

            if not hl_ext or not hl_main or not body_html:
                headlines = data.get("headlines", []) or []
                bodies = data.get("bodies", []) or []
                if not hl_ext:
                    hl_ext = pick_headline_from_arrays(headlines, "extended") or ""
                if not hl_main:
                    hl_main = (
                        pick_headline_from_arrays(headlines, "main")
                        or pick_any_headline(headlines)
                        or ""
                    )
                if not body_html:
                    body_html = pick_body_from_arrays(bodies) or ""

            legacy_headline = hl_ext or hl_main

            descriptions = data.get("descriptions", [])
            description = ""
            if isinstance(descriptions, list) and descriptions:
                description = descriptions[0].get("value", "")

            source = get_nested(data, ["infosources", 0, "name"])
            byline = data.get("by") or whole.get("by") or ""
            wordcount = whole.get("wordcount")
            if not isinstance(wordcount, int):
                wordcount = data.get("wordcount")
            if not isinstance(wordcount, int):
                wordcount = 0
            language = prefer_top_level(whole, data, "language", "")
            located = prefer_top_level(whole, data, "located", "")
            wire = whole.get("wire") or data.get("wire")

            transformed.append(
                {
                    "guid": data.get("uri", ""),
                    "type": data.get("type", ""),
                    "headline": legacy_headline or "",
                    "headline_extended": hl_ext or "",
                    "headline_main": hl_main or "",
                    "description_text": (description[:200] + "...")
                    if description
                    else "",
                    "versioncreated": self._parse_datetime(data.get("versioncreated")),
                    "slugline": data.get("slugline", ""),
                    "firstcreated": data.get("firstcreated"),
                    "urgency": data.get("urgency"),
                    "version": data.get("version", ""),
                    "body_html": body_html or "",
                    "source": source,
                    "state": "published",
                    "language": language,
                    "byline": byline or "",
                    "located": located,
                    "wordcount": wordcount,
                    **(
                        {"anpa_category": [{"name": w} for w in wire]}
                        if isinstance(wire, list)
                        else {"anpa_category": [{"name": wire}]}
                        if wire
                        else {}
                    ),
                }
            )
        return transformed


def init_app(app):
    logger.info("=== Initializing Archive Search Provider===")
    try:
        superdesk.register_search_provider(
            "archive_search", provider_class=ArchiveSearchProvider
        )
        logger.info("Archive Search Provider registered successfully")
    except Exception:
        logger.exception("Failed to register Archive Search Provider")
    logger.info("=== End Archive Search Provider Initialization ===")
