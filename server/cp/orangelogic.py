import math
import logging
import mimetypes
import aiohttp
import io

import superdesk
import cp
import yarl

from pytz import UTC
from datetime import datetime
from urllib.parse import urljoin
from quart import current_app as app, json
from aiohttp.client_exceptions import ClientResponseError
from superdesk.utils import ListCursor
from superdesk.errors import AlreadyExistsError
from superdesk.timer import timer
from superdesk.utc import local_to_utc
from superdesk.types.search_providers import SearchProvider
from superdesk.io.commands.update_ingest import update_renditions
from superdesk.media.image import get_meta_iptc

from cp.utils import parse_xmp
from cp.ingest.parser.ap import append_matching_subject


AUTH_API = "/API/Authentication/v1.0/Login"
SEARCH_API = "/API/Search/v3.0/search"
DOWNLOAD_API = "/htm/GetDocumentAPI.aspx"

TIMEOUT = aiohttp.ClientTimeout(total=10, connect=5)
DATE_FORMAT = "u"

IPTC_SOURCE_MAPPING = {
    "AP Third Party": "Unknown AP",
}

COUNTRY_MAPPING = {
    "CHN": "China",
}

# iptc keys
FIXTURE_ID = "Fixture Identifier"
ORIGINAL_TRANSMISSION_REF = "Original Transmission Reference"


tokens = {}
logger = logging.getLogger(__name__)


def get_api_sort(sort):
    if sort == {"versioncreated": "asc"}:
        return "Oldest first"
    else:
        return "Newest first"


class OrangelogicListCursor(ListCursor):
    def __init__(self, docs, count):
        super().__init__(docs)
        self._count = count

    def __len__(self):
        return len(self.docs)

    def count(self, **kwargs):
        return self._count


class OrangelogicSearchProvider(SearchProvider):
    label = "Orange Logic"

    TZ = "America/Toronto"
    URL = "https://canadianpress3227prod.orangelogic.com/"

    MEDIA_TYPE_MAP = {
        "image": "picture",
        "video": "video",
        "audio": "audio",
        "package": "composite",
        "graphic": "graphic",
        "story": "composite",
    }

    RENDITIONS_MAP = {
        "original": "Path_TR1",
        "baseImage": "Path_TR1",
        "viewImage": "Path_TR7",
        "thumbnail": "Path_TR7",
        "webHigh": "Path_WebHigh",
    }

    FIELDS = [
        "Title",
        "SystemIdentifier",
        "MediaNumber",
        "Caption",
        "CaptionShort",
        "EditDate",
        "MediaDate",
        "CreateDate",
        "GlobalEditDate",
        "MediaType",
        "Path_TR1",
        "Path_TR4",
        "Path_TR7",
        "Path_WebHigh",
        "Photographer",
        "PhotographerFastId",
        "copyright",
        "MediaEncryptedIdentifier",
    ]

    def __init__(self, provider):
        super().__init__(provider)
        self.config = provider.get("config") or {}
        self.url = app.config.get("ORANGELOGIC_URL") or self.URL
        self.session = None

    async def ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    def _url(self, path):
        return urljoin(self.url, path)

    async def _request(self, api, method="GET", **kwargs):
        await self.ensure_session()
        url = self._url(api)
        params = kwargs.pop("params", None)
        data = kwargs.pop("data", None)

        async with self.session.request(
            method, url, params=params, data=data, timeout=TIMEOUT
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _login(self):
        with timer("orange.login"):
            resp = await self._request(
                AUTH_API,
                method="POST",
                data={
                    "Login": self.config.get("username"),
                    "Password": self.config.get("password"),
                    "format": "json",
                },
            )
        tokens[self.config["username"]] = resp["APIResponse"]["Token"]

    async def _auth_request(self, api, **kwargs):
        repeats = 2
        while repeats > 0:
            if not self.token:
                await self._login()
            try:
                kwargs["params"] = kwargs.get("params", {})
                kwargs["params"]["token"] = self.token
                with timer("orange.request"):
                    return await self._request(api, **kwargs)
            except ClientResponseError as err:
                logger.error(err)
                await self._login()  # auth error
                repeats -= 1
                if repeats == 0:
                    raise

    @property
    def token(self):
        try:
            key = self.config["username"]
            return tokens[key]
        except KeyError:
            return

    async def find_async(
        self, query: dict, params: dict | None = None
    ) -> OrangelogicListCursor:
        if params is None:
            params = {}

        size = 25  # int(query.get('size', 25))
        page = math.ceil((int(query.get("from", 0)) + 1) / size)
        try:
            sort = query["sort"][0]
        except (IndexError, AttributeError, TypeError, KeyError):
            sort = {"versioncreated": "desc"}

        kwargs = {
            "params": {
                "pagenumber": page,
                "countperpage": size,
                "fields": ",".join(self.FIELDS),
                "Sort": get_api_sort(sort),
                "format": "json",
                "DateFormat": "u",
            }
        }

        query_components = {
            "MediaType": "(Image OR Video)",
        }

        try:
            query_components["Text"] = query["query"]["filtered"]["query"][
                "query_string"
            ]["query"]
        except (KeyError, TypeError):
            pass

        if params:
            if params.get("mediaTypes"):
                selected = [k for k, v in params["mediaTypes"].items() if v]
                if selected:
                    query_components["MediaType"] = "({})".format(" OR ".join(selected))

        kwargs["params"]["query"] = " ".join(
            ["{}:{}".format(key, val) for key, val in query_components.items() if val]
        )

        if params:
            for param, op in (("from", ">:"), ("to", "<:")):
                if params.get(param):
                    kwargs["params"]["query"] = "{} MediaDate{}{}".format(
                        kwargs["params"]["query"], op, params[param]
                    ).strip()

        data = await self._auth_request(SEARCH_API, **kwargs)
        assert data is not None

        # FIXME-ASYNC: File access should be made async (with `aiofiles?`).
        with open("/tmp/resp.json", mode="w") as out:
            out.write(json.dumps(data, indent=2))

        items = self._parse_items(data)
        return OrangelogicListCursor(
            items, data["APIResponse"]["GlobalInfo"]["TotalCount"]
        )

    def _parse_items(self, data):
        items = []
        for item in data["APIResponse"]["Items"]:
            guid = item["SystemIdentifier"]
            items.append(
                {
                    "_id": guid,
                    "_fetchable": True,
                    "guid": guid,
                    "type": self.MEDIA_TYPE_MAP[item["MediaType"].lower()],
                    "media": item["MediaEncryptedIdentifier"],
                    "source": item["PhotographerFastId"],
                    "slugline": item["Title"],
                    "headline": item["CaptionShort"],
                    "byline": item["Photographer"],
                    "copyrightholder": item["copyright"],
                    "description_text": item["Caption"],
                    "firstcreated": self.parse_datetime(item["CreateDate"]),
                    "versioncreated": self.parse_datetime(item["MediaDate"])
                    or self.parse_datetime(item["CreateDate"]),
                    "renditions": {
                        key: rendition(item[path])
                        for key, path in self.RENDITIONS_MAP.items()
                        if item.get(path) and item[path].get("URI")
                    },
                }
            )
        return items

    def parse_datetime(self, value):
        if not value:
            return None
        local = datetime.strptime(value, "%m/%d/%Y %H:%M:%S %p")
        return local_to_utc(self.TZ, local)

    async def fetch_async(self, guid: str):
        kwargs = {
            "params": {
                "query": "SystemIdentifier:{}".format(guid),
                "fields": ",".join(self.FIELDS),
                "format": "json",
                "DateFormat": "u",
            }
        }
        data = await self._auth_request(SEARCH_API, **kwargs)
        item = self._parse_items(data)[0]

        url = self._url(DOWNLOAD_API)
        params = {
            "F": "TRX",
            "DocID": item.pop("media"),
            "token": self.token,
        }

        await self.ensure_session()
        href = str(yarl.URL(url).with_query(params))
        update_renditions(item, href, None)

        if item["type"] == "picture":
            await _parse_binary_async(item)

        # it's in superdesk now, so make it ignore the api
        item["fetch_endpoint"] = ""

        item.setdefault("language", "en")

        return item


async def _parse_binary_async(item):
    file_obj = await app.media.get_async(item["renditions"]["original"]["media"])
    binary = io.BytesIO(await file_obj.read())
    iptc = get_meta_iptc(binary)
    if not iptc:
        return

    item.setdefault("extra", {})

    if iptc.get("By-line"):
        item["byline"] = iptc["By-line"]

    if iptc.get("Category"):
        await append_matching_subject(item, cp.PHOTO_CATEGORIES, iptc["Category"])

    if iptc.get("Credit"):
        item["creditline"] = (
            "THE ASSOCIATED PRESS" if iptc["Credit"] == "AP" else iptc["Credit"]
        )

    if iptc.get("Source"):
        item["original_source"] = IPTC_SOURCE_MAPPING.get(
            iptc["Source"], iptc["Source"]
        )
        item["extra"][cp.ARCHIVE_SOURCE] = item["original_source"]

    if iptc.get("City") or item.get("Country/Primary Location Name"):
        country = iptc.get("Country/Primary Location Name")
        item["dateline"] = {
            "located": {
                "city": iptc.get("City"),
                "country": COUNTRY_MAPPING.get(country, country) if country else None,
            }
        }

    if iptc.get("By-line Title"):
        item["extra"][cp.PHOTOGRAPHER_CODE] = iptc["By-line Title"]

    if iptc.get("Writer/Editor"):
        item["extra"][cp.CAPTION_WRITER] = iptc["Writer/Editor"]

    if iptc.get("Copyright Notice"):
        item["copyrightnotice"] = iptc["Copyright Notice"]

    if iptc.get("Caption/Abstract"):
        item["description_text"] = iptc["Caption/Abstract"]

    if iptc.get("Special Instructions"):
        item["ednote"] = iptc["Special Instructions"]

    if iptc.get(ORIGINAL_TRANSMISSION_REF):
        if len(iptc[ORIGINAL_TRANSMISSION_REF]) == cp.SLUG_LEN:
            item["extra"][cp.ORIG_ID] = iptc[ORIGINAL_TRANSMISSION_REF]
        else:
            item["extra"][cp.FILENAME] = iptc[ORIGINAL_TRANSMISSION_REF]

    if iptc.get(FIXTURE_ID) and len(iptc[FIXTURE_ID]) == cp.SLUG_LEN:
        item["extra"][cp.ORIG_ID] = iptc[FIXTURE_ID]

    binary.seek(0)
    xmp = parse_xmp(binary)
    if not xmp:
        return

    if xmp.get("http://ns.adobe.com/photoshop/1.0/"):
        for key, val, _ in xmp["http://ns.adobe.com/photoshop/1.0/"]:
            if key == "photoshop:Urgency":
                item["urgency"] = int(val)
            elif key == "photoshop:DateCreated":
                item["firstcreated"] = _parse_xmp_datetime(val)

    if xmp.get("http://purl.org/dc/elements/1.1/"):
        for key, val, _ in xmp["http://purl.org/dc/elements/1.1/"]:
            if key == "dc:rights" and val:
                item["extra"][cp.INFOSOURCE] = val
            elif key == "dc:rights[1]" and val:
                item["extra"][cp.INFOSOURCE] = val


def _parse_xmp_datetime(val):
    try:
        return datetime.strptime(val[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return datetime.strptime(val[:19], "%Y-%m-%d").replace(tzinfo=UTC)


def rendition(data):
    rend = {
        "href": data["URI"],
        "mimetype": mimetypes.guess_type(data["URI"])[0],
    }

    if data.get("Width"):
        rend["width"] = int(data["Width"])

    if data.get("Height"):
        rend["height"] = int(data["Height"])

    return rend


def init_app(app):
    try:
        superdesk.register_search_provider(
            "orangelogic", provider_class=OrangelogicSearchProvider
        )
    except AlreadyExistsError:
        # No need to raise an error here
        pass
