import json
import superdesk
import logging
import re
from typing import Tuple, Dict

from flask import current_app as app
from eve.utils import config
from superdesk.publish.formatters import Formatter
from superdesk.errors import FormatterError
from superdesk.metadata.item import (
    ITEM_TYPE,
    CONTENT_TYPE,
)
from superdesk.utils import json_serialize_datetime_objectId
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def format_datetime(dt):
    """Format a datetime object as 'YYYY-MM-DDTHH:MM:SS.mmm+00:00'"""
    if not isinstance(dt, datetime):
        raise ValueError("Input must be a datetime object")
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.isoformat(timespec="milliseconds")


class NINJS21Formatter(Formatter):
    name = "NINJS2.1"
    type = "ninjs2.1"

    direct_copy_properties: Tuple[str, ...] = (
        "urgency",
        "pubstatus",
        "slugline",
    )

    def __init__(self):
        self._uri_schemes_cache = None
        self._infosources_cache = None
        self._jimi_subjects_cache = None

    def get_locale_name(self, item, language):
        """Get localized name from item based on language, with fallbacks.

        Args:
            item: Dictionary containing translations and name
            language: Language code to look up

        Returns:
            Localized name string or empty string if no name found
        """
        if not item or not isinstance(item, dict):
            return ""

        translations = (item.get("translations") or {}).get("name") or {}

        # Try exact language match
        if translations.get(language):
            return translations[language]

        # Try language with -CA suffix
        if translations.get(f"{language}-CA"):
            return translations[f"{language}-CA"]

        # Fall back to default name
        return item.get("name", "")

    def sanitize_text(self, text: str, remove_p_tags=False) -> str:
        """Remove invisible/control chars and optionally strip <p> tags."""
        if not isinstance(text, (str, bytes)):
            return text

        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")

        # Remove ASCII control chars except \t, \n, \r
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)

        # Remove Unicode invisible/zero-width chars (BOM, ZWSP, etc.)
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

        if remove_p_tags:
            text = re.sub(r"</?p>", "", text, flags=re.IGNORECASE)

        return text.strip()

    def _get_jimi_subjects_mapping(self) -> Dict[str, str]:
        """Get URI schemes mapping from vocabulary."""
        if self._jimi_subjects_cache is None:
            try:
                cv = superdesk.get_resource_service("vocabularies").find_one(
                    req=None, _id="subject_custom"
                )
                if cv and cv.get("items"):
                    self._jimi_subjects_cache = {
                        item["qcode"]: item
                        for item in cv["items"]
                        if item.get("in_jimi", False)
                    }
                else:
                    self._jimi_subjects_cache = {}
            except Exception as e:
                logger.error(f"Error loading jimi subjects vocabulary: {e}")
                self._jimi_subjects_cache = {}

        return self._jimi_subjects_cache

    def _get_uri_schemes_mapping(self) -> Dict[str, str]:
        """Get URI schemes mapping from vocabulary."""
        fallback_mapping = {
            "person": "http://cv.cp.org/People/",
            "place": "http://cv.cp.org/Places/",
            "organisation": "http://cv.cp.org/Organizations/",
            "event": "http://cv.cp.org/Events/",
            "subject": "http://cv.iptc.org/newscodes/mediatopic/",
            "subject_custom": "http://cv.cp.org/Subjects/",
            "distribution": "http://cv.cp.org/distribution/",
            "destinations": "http://cv.cp.org/destination/",
        }
        if self._uri_schemes_cache is None:
            try:
                cv = superdesk.get_resource_service("vocabularies").find_one(
                    req=None, _id="ninjs_uri_schemes"
                )
                if cv and cv.get("items"):
                    self._uri_schemes_cache = {
                        item["qcode"]: item.get("uri_base", "")
                        for item in cv["items"]
                        if item.get("is_active", True)
                    }
                else:
                    self._uri_schemes_cache = fallback_mapping
            except Exception as e:
                logger.error(f"Error loading URI schemes vocabulary: {e}")
                self._uri_schemes_cache = fallback_mapping

        return self._uri_schemes_cache

    def _get_infosources_mapping(self) -> Dict[str, Dict]:
        """Get infosources mapping from vocabulary."""
        if self._infosources_cache is None:
            try:
                cv = superdesk.get_resource_service("vocabularies").find_one(
                    req=None, _id="ninjs_infosources"
                )
                if cv and cv.get("items"):
                    self._infosources_cache = {}
                    for item in cv.get("items", []):
                        if not item.get("is_active", True):
                            continue

                        info_source = {
                            "name": item.get("name", ""),
                            "literal": item.get("literal", ""),
                            "uri": item.get("uri", ""),
                        }

                        if item.get("is_distributor", False):
                            self._infosources_cache["distributor"] = info_source
                        self._infosources_cache[item["qcode"]] = info_source
                else:
                    # Fallback to default mappings if vocabulary not found
                    self._infosources_cache = {
                        "Globenewswire": {
                            "name": "Globenewswire",
                            "literal": "globenewswire.com",
                            "uri": "http://globenewswire.com",
                            "is_distributor": False,
                        },
                        "The Associated Press": {
                            "name": "The Associated Press",
                            "literal": "ap.org",
                            "uri": "http://ap.org",
                            "is_distributor": False,
                        },
                        "The Canadian Press": {
                            "name": "The Canadian Press",
                            "literal": "cp.org",
                            "uri": "http://cp.org",
                            "is_distributor": True,
                        },
                    }
            except Exception as e:
                logger.error(f"Error loading infosources vocabulary: {e}")
                self._infosources_cache = {}

        return self._infosources_cache

    def format(self, article, subscriber, codes=None):
        try:
            pub_seq_num = superdesk.get_resource_service(
                "subscribers"
            ).generate_sequence_number(subscriber)

            ninjs = self._transform_to_ninjs(article, subscriber)
            return [
                (
                    pub_seq_num,
                    json.dumps(ninjs, default=json_serialize_datetime_objectId),
                )
            ]
        except Exception as ex:
            raise FormatterError.ninjsFormatterError(ex, subscriber)

    def _format_cv_item_base(self, item, language="en-CA"):
        result = {}

        if not item or not isinstance(item, dict):
            return result

        if name := self.get_locale_name(item, language):
            result["name"] = name

        if qcode := item.get("qcode"):
            result["qcode"] = qcode

        if scheme := item.get("scheme"):
            result["scheme"] = scheme

        if creator := item.get("creator"):
            result["creator"] = creator.lower()

        if relevance := item.get("relevance"):
            result["relevance"] = relevance

        return result

    def construct_uri(self, scheme, literal, key=None):
        """Construct URI using vocabulary-based scheme mapping."""
        uri_schemes = self._get_uri_schemes_mapping()

        if scheme.startswith("http://"):
            uri = f"{scheme}{literal}" if literal else scheme
        elif scheme in ["subject", "subject_custom"] and literal.isdigit():
            uri = uri_schemes.get("subject", f"http://cv.cp.org/{scheme}/") + literal
        else:
            uri_base = uri_schemes.get(scheme, f"http://cv.cp.org/{scheme}/")
            uri = f"{uri_base}{literal}" if literal else f"{uri_base}"

        if not scheme and key and literal:
            uri = uri_schemes.get(key, f"http://cv.cp.org/{key}/") + literal

        # Remove any spaces from URI before returning
        return uri.replace(" ", "")

    def is_custom_subject(self, qcode, scheme):
        if qcode.isdigit() and scheme in ["subject", "subject_custom"]:
            return False
        return (
            qcode
            and "-" in qcode
            and not scheme.startswith("http://")
            and scheme not in ["destinations", "distribution", "destination"]
        )

    def format_cv_items(self, article, items_key):
        formatted_items = []
        items = article.get(items_key, [])
        if not items:
            logger.warning(f"No {items_key} found in article")
            return []

        language = article.get("language", "en-CA")

        for item in items:
            if not item:
                continue
            base_item = self._format_cv_item_base(item, language)
            scheme = base_item.get("scheme", "")
            qcode = base_item.get("qcode", "")

            if self.is_custom_subject(qcode, scheme):
                scheme = "subject_custom"

            uri = self.construct_uri(scheme, qcode, items_key)
            rel = self.determine_rel(scheme, qcode)

            item = {
                "name": base_item.get("name", ""),
                "uri": uri,
                "literal": qcode,
                "rel": rel,
                "creator": base_item.get("creator", ""),
                "relevance": base_item.get("relevance", 50),
            }

            if self.should_remove_creator_relevance(item, items_key, scheme):
                for field in ["creator", "relevance"]:
                    item.pop(field, None)
            # Remove any empty fields from the item
            item = {k: v for k, v in item.items() if v not in [None, "", [], {}]}

            # Only add item if uri does not contain 'regions'
            if "regions" not in item.get("uri", ""):
                formatted_items.append(item)

        return formatted_items

    def determine_rel(self, scheme, qcode):
        rel_mapping = {
            "destinations": "destination",
            "destination": "destination",
            "distribution": "distribution",
            "tag": "tag",
            "ap_product": "product",
        }
        return rel_mapping.get(scheme, "about")

    def should_remove_creator_relevance(self, item, items_key, scheme):
        if items_key == "subject" and item.get("rel") != "about":
            return True
        elif scheme in ["tag", "ap_product"]:
            return True
        return False

    def _transform_to_ninjs(self, article, subscriber, recursive=True):

        ninjs = {}
        guid = article.get("guid", "")
        if not guid:
            logger.warning("No guid found in article")
            return None
        ninjs["uri"] = f"http://cp.org/{guid}"
        ninjs["version"] = str(article.get("rewrite_sequence", 1))
        ninjs["type"] = self._get_type(article)
        ninjs["by"] = article.get("byline", "")
        ninjs["language"] = self._get_language(article)

        now_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        try:
            if article.get("firstcreated"):
                ninjs["firstcreated"] = format_datetime(article["firstcreated"])
            else:
                ninjs["firstcreated"] = format_datetime(now_dt)
        except (AttributeError, ValueError) as e:
            logger.warning(f"Could not format firstcreated date: {e}")
            ninjs["firstcreated"] = format_datetime(now_dt)
        try:
            if article.get("versioncreated"):
                ninjs["versioncreated"] = format_datetime(article["versioncreated"])
                ninjs["contentcreated"] = ninjs["versioncreated"]
            else:
                ninjs["versioncreated"] = format_datetime(now_dt)
                ninjs["contentcreated"] = ninjs["versioncreated"]
        except (AttributeError, ValueError) as e:
            logger.warning(f"Could not format versioncreated date: {e}")
            ninjs["versioncreated"] = format_datetime(now_dt)
            ninjs["contentcreated"] = ninjs["versioncreated"]

        located = article.get("dateline", {}).get("located", {})
        if located:
            ninjs["located"] = located.get("city", "")

        for copy_property in self.direct_copy_properties:
            if article.get(copy_property) is not None:
                ninjs[copy_property] = article[copy_property]

        ninjs["descriptions"] = self._build_descriptions(article)
        ninjs["bodies"] = self._build_bodies(article)
        ninjs["headlines"] = self._build_headlines(article)
        ninjs["infosources"] = self._build_infosources(article)
        ninjs["altids"] = self._build_altids(article)
        ninjs["places"] = self.build_places(article)
        ninjs["genres"] = self._build_genres(article)

        subjects, objects = self.build_subjects_and_objects(article)
        ninjs["subjects"] = subjects
        ninjs["objects"] = objects
        ninjs["people"] = self.format_cv_items(article, "person")
        ninjs["organisations"] = self.format_cv_items(article, "organisation")
        ninjs["events"] = self.format_cv_items(article, "event")
        ninjs["copyrightholder"] = self._build_copyrights(article).get(
            "copyrightholder", ""
        )
        ninjs["copyrightnotice"] = self._build_copyrights(article).get(
            "copyrightnotice", ""
        )

        ninjs["ednote"] = article.get("ednote", "")
        ninjs["associations"] = self._build_associations(article)
        ninjs["renditions"] = self._build_renditions_list(article)
        ninjs = {k: v for k, v in ninjs.items() if v not in (None, "", [], {})}
        return ninjs

    def _get_language(self, article):
        return article.get("language", "en-CA")

    def _split_combined_subjects(self, subjects):
        updated_subjects = []

        for subject in subjects:
            if "/" in subject.get("name", "") and subject.get("name") in [
                "Print / Broadcast"
            ]:
                names = [name.strip() for name in subject["name"].split("/")]
                scheme = subject.get("rel", "")

                for name in names:
                    updated_subjects.append(
                        {
                            "name": name,
                            "uri": f"http://cv.cp.org/{scheme}/{name}",
                            "literal": name,
                            "rel": scheme,
                        }
                    )
            else:
                updated_subjects.append(subject)

        return updated_subjects

    def _add_anpa_categories(self, subjects, article):
        is_ap = article.get("source", "") in ["The Associated Press", "AP"]
        uri_base = "http://cv.cp.org/anpa/ap/" if is_ap else "http://cv.cp.org/anpa/"

        for category in article.get("anpa_category", []) or []:
            if qcode := category.get("qcode"):
                subjects.append(
                    {
                        "literal": qcode,
                        "uri": f"{uri_base}{qcode}",
                        "name": self.get_locale_name(
                            category, article.get("language", "en-CA")
                        ),
                        "rel": "category",
                    }
                )
        return subjects

    def build_subjects_and_objects(self, article):
        """Build subjects list and separate product subjects into objects list."""

        subjects = self.format_cv_items(article, "subject")
        subjects = self._split_combined_subjects(subjects)
        subjects = self._add_anpa_categories(subjects, article)
        jimi_subjects = self._get_jimi_subjects_mapping()
        language = article.get("language", "en-CA")

        non_product_subjects = []
        product_objects = []

        for subject in subjects:
            if subject.get("rel") == "product":
                product_object = self._create_product_object(subject)
                product_objects.append(product_object)
            else:
                if "mediatopic" in subject.get("uri", ""):
                    non_product_subjects.append(
                        {**subject, "name": subject.get("name", "").lower()}
                    )
                else:
                    non_product_subjects.append(subject)

            if subject.get("literal") in jimi_subjects:
                jimi_subject = self._create_jimi_subject(
                    subject, jimi_subjects[subject.get("literal")], language
                )
                non_product_subjects.append(jimi_subject)

        return non_product_subjects, product_objects

    def _create_product_object(self, subject):
        return {
            "name": subject.get("name", ""),
            "uri": subject.get("uri", ""),
            "literal": subject.get("literal", ""),
            "rel": subject.get("rel", "product"),
        }

    def _create_jimi_subject(self, subject, jimi_subject, language):
        name = self.get_locale_name(jimi_subject, language)
        return {
            "uri": f"http://cv.cp.org/cp-subject-legacy/{subject.get('literal')}",
            "name": name,
        }

    def build_places(self, article):
        places = self.format_cv_items(article, "place")
        dateline_place = self.get_dateline_place(article)
        if dateline_place.get("name"):
            places.append(dateline_place)
        return places

    def get_dateline_place(self, article):
        dateline = article.get("dateline")
        if not dateline:
            return {}
        located = dateline.get("located")
        if located is None:
            return {}

        city = located.get("city", "")
        state = located.get("state", "")
        country = located.get("country", "")
        code = located.get("code", "")
        lon = located.get("location", {}).get("lon")
        lat = located.get("location", {}).get("lat")

        # Place is seen in some AP objects without this the lon and lat are empty sometimes
        place = located.get("place")
        if place is not None:
            if not city:
                city = place.get("city", "")
            if not state:
                state = place.get("state", "")
            if not country:
                country = place.get("country", "")
            if not code:
                code = place.get("code", "")
            if lon is None:
                lon = place.get("location", {}).get("lon")
            if lat is None:
                lat = place.get("location", {}).get("lat")

        return {
            "uri": f"urn:geonames:{code}",
            "literal": code,
            "name": city,
            "rel": "placeline",
            "contactinfo": [
                {
                    "type": "physical",
                    "address": {"locality": city, "area": state, "country": country},
                }
            ],
            "geojson": {"type": "Point", "coordinates": [lon, lat]},
        }

    def _get_type(self, article):
        if article[ITEM_TYPE] == CONTENT_TYPE.PREFORMATTED:
            return CONTENT_TYPE.TEXT
        return article[ITEM_TYPE]

    def _build_descriptions(self, article):
        """Build descriptions list with roles from extra and description fields."""
        descriptions = []

        # Map of extra fields to roles
        extra_field_roles = {
            "update": "update",
            "correction": "correction",
            "caption_writer": "caption_writer",
        }

        # Process extra fields that map to descriptions
        extra_fields = article.get("extra", {})
        for field, role in extra_field_roles.items():
            if value := extra_fields.get(field):
                descriptions.append(
                    {
                        "role": role,
                        "value": self.sanitize_text(value, remove_p_tags=True),
                    }
                )

        if abstract := article.get("abstract"):
            descriptions.append(
                {
                    "role": "abstract",
                    "value": self.sanitize_text(abstract, remove_p_tags=True),
                }
            )

        # Map content types to description roles
        type_role_mapping = {
            "video": "summary",
            "audio": "summary",
            "picture": "caption",
        }

        if description_text := article.get("description_text"):
            if role := type_role_mapping.get(article.get("type", "")):
                descriptions.append(
                    {
                        "role": role,
                        "value": self.sanitize_text(
                            description_text, remove_p_tags=True
                        ),
                    }
                )

        # Add HTML descriptions if present
        if description_html := article.get(f"description_html"):
            descriptions.append(
                {
                    "role": "html",
                    "value": self.sanitize_text(description_html, remove_p_tags=False),
                }
            )

        return descriptions

    def _build_bodies(self, article):
        """Build bodies list with role, charcount, wordcount, contenttype, value."""
        bodies = []
        body_html = article.get("body_html", "")

        # Ensure body_html is properly encoded as UTF-8
        if body_html:
            if isinstance(body_html, bytes):
                body_html = body_html.decode("utf-8", errors="replace")

            # Normalize to ensure proper UTF-8 encoding
            body_html = body_html.encode("utf-8", errors="replace").decode("utf-8")

            body_html = self.sanitize_text(body_html, remove_p_tags=False)
            wordcount = article.get("word_count", 0)

            if body_html:
                charcount = len(body_html)
                bodies.append(
                    {
                        "role": "html",
                        "charcount": charcount,
                        "wordcount": wordcount,
                        "contenttype": "text/html",
                        "value": body_html,
                    }
                )

        return bodies

    def _build_headlines(self, article):
        """Build headlines list with roles from headline and extra fields."""
        headlines = []
        # Add main headline
        if headline := article.get("headline", ""):
            headlines.append(
                {
                    "role": "main",
                    "value": self.sanitize_text(headline, remove_p_tags=True),
                }
            )

        # Add extended headline from extra
        if headline_extended := article.get("extra", {}).get("headline_extended", ""):
            headlines.append(
                {
                    "role": "extended",
                    "value": self.sanitize_text(headline_extended, remove_p_tags=True),
                }
            )

        if headline_short := article.get("extra", {}).get("short_headline", ""):
            headlines.append(
                {
                    "role": "short",
                    "value": self.sanitize_text(headline_short, remove_p_tags=True),
                }
            )

        return headlines

    def _build_copyrights(self, article):
        if source := article.get("source", "The Canadian Press"):
            return {
                "copyrightholder": source,
                "copyrightnotice": f"Copyright {datetime.now().year}, {source}. All rights reserved.",
            }
        return None

    def _build_infosources(self, article):
        """Build infosources list from source field using vocabulary mapping."""
        infosources = []
        source = article.get("source", "The Canadian Press")
        original_source = article.get("original_source", "")
        infosources_mapping = self._get_infosources_mapping()

        # Always add The Canadian Press as distributor
        if distributor := infosources_mapping.get("distributor"):
            infosources.append({**distributor, "role": "distributor"})

        # Add source as originator if mapping exists
        if source in infosources_mapping:
            infosources.append({**infosources_mapping[source], "role": "originator"})
        else:
            logger.warning(f"No infosource mapping found for source {source}")
            infosources.append(
                {"name": source, "literal": source, "role": "originator"}
            )

        # Add original source as third-party originator if exists and has mapping
        if original_source and original_source in infosources_mapping:
            infosources.append(
                {
                    **infosources_mapping[original_source],
                    "role": "originator-third-party",
                }
            )
        elif original_source:
            logger.warning(
                f"No infosource mapping found for original source {original_source}"
            )
            infosources.append(
                {
                    "name": original_source,
                    "literal": original_source,
                    "role": "originator-third-party",
                }
            )

        return infosources

    def _get_original_id_for_article(self, article):
        """Get the original ID for an article by following the rewrite chain using Superdesk's archive service.

        This method uses Superdesk's built-in archive service to traverse the rewrite chain
        and find the original article that this item was rewritten from.

        Args:
            article: Superdesk article dictionary

        Returns:
            str: Original article GUID, or empty string if not found
        """
        try:
            # Check if this article has a rewrite_of field
            article_id = article.get("guid", "")
            rewrite_of = article.get("rewrite_of")

            if not rewrite_of:
                # No rewrite chain, this is the original
                return article_id

            # Use Superdesk's archive service to find the original article
            original_guid = self._get_original_item_guid(article)
            return original_guid

        except Exception as e:
            logger.error(
                f"_get_original_id_for_article: Error getting original ID: {str(e)}"
            )
            return article.get("guid", "")

    def _get_original_item_guid(self, item):
        """Recursively find the original article GUID by following the rewrite_of chain.

        This method uses Superdesk's archive service to traverse the rewrite chain
        and find the original article. It follows the same pattern as other Superdesk formatters.

        Args:
            item: Superdesk article dictionary

        Returns:
            str: The GUID of the original article, or current article's GUID if not found
        """
        orig = item
        archive_service = superdesk.get_resource_service("archive")

        # Limit to 100 iterations to prevent infinite loops
        for i in range(100):
            if not orig.get("rewrite_of"):
                # Found the original article
                return orig.get("guid", "")

            rewrite_of = orig.get("rewrite_of")

            # Use Superdesk's archive service to find the parent article
            next_orig = archive_service.find_one(req=None, _id=rewrite_of)
            if next_orig is not None:
                orig = next_orig
                continue
            else:
                logger.warning(
                    f"_get_original_item_guid: Could not find parent article {rewrite_of}"
                )
                break

        # Return the current article's GUID if we couldn't find the original
        logger.warning(
            f"_get_original_item_guid: Could not find original article, returning current GUID {orig.get('guid', '')}"
        )
        return orig.get("guid", "")

    def _build_altids(self, article):
        altids = []

        relationships = {
            "rewrite_of": "rewrite_of",
            "rewritten_by": "rewritten_by",
            "translated_from": "translation_of",
            "anpa_take_key": "take_key",
        }

        for field, role in relationships.items():
            if value := article.get(field):
                altids.append({"role": role, "value": value.strip()})

        for author in article.get("authors", []):
            if name := author.get("name"):
                altids.append({"role": "writer", "value": name})

        extra_mappings = {
            "photographer_code": "photographer_code",
            "ap_version": "ap_version",
            "filename": "TransRef",
            "itemid": "source_id",
        }
        extra_fields = article.get("extra", {})
        for field, role in extra_mappings.items():
            if value := extra_fields.get(field):
                altids.append({"role": role, "value": str(value)})

        # Add original ID by following rewrite chain
        original_id = self._get_original_id_for_article(article)
        if original_id:
            altids.append({"role": "original_id", "value": original_id})

        return altids

    def _build_genres(self, article):
        """Build genres list with uri and name."""
        genres = []
        genre_list = article.get("genre") or []
        for genre in genre_list:
            qcode = genre.get("qcode", "")
            name = genre.get("name", "")
            qcode_without_spaces = "".join(qcode.split())
            if qcode_without_spaces and name:
                genres.append(
                    {
                        "uri": f"http://cv.cp.org/genre/{qcode_without_spaces}",
                        "name": name,
                        "literal": qcode,
                    }
                )
        return genres

    def _build_associations(self, article):
        """Build associations list with full objects for associated items."""
        associations = []
        article_associations = article.get("associations", {})
        new_associations = self.check_new_associations(article)

        for key, value in article_associations.items():
            if not value or not isinstance(value, dict):
                continue

            association_item = {}

            # Basic fields
            guid = value.get("guid", "")
            if guid:
                association_item["uri"] = f"http://cp.org/{guid}"
                association_item["name"] = key
                association_item["type"] = value.get("type", "text")

            association_item["headlines"] = self._build_headlines(value)

            descriptions = self._build_descriptions(value)

            if (order := value.get("order")) is not None:
                descriptions.append({"role": "sortorder", "value": str(order)})

            new_assoc = new_associations.get(guid)
            if (
                isinstance(new_assoc, dict)
                and "role" in new_assoc
                and "value" in new_assoc
            ):
                descriptions.append(new_assoc)

            association_item["descriptions"] = descriptions
            association_item["altids"] = self._build_altids(value)

            association_item["renditions"] = self._build_renditions_list(value)
            associations.append(association_item)

        return associations

    def check_new_associations(self, article):
        """
        Returns a dict mapping association guids to their isNew status.
        An association is 'new' if it does not exist in the previous (rewrite_of) article.
        """
        result = {}
        article_associations = article.get("associations", {})
        parent_article_id = article.get("rewrite_of", article.get("translated_from"))

        # If no rewrite_of or translated_from, all associations are new
        if not parent_article_id:
            for assoc in article_associations.values():
                if assoc and isinstance(assoc, dict):
                    guid = assoc.get("guid")
                    if guid:
                        result[guid] = {"role": "isNew", "value": "Yes"}
            return result

        # Get previous article from archive
        archive_service = superdesk.get_resource_service("archive")
        previous_article = archive_service.find_one(req=None, _id=parent_article_id)
        previous_guids = set()

        if previous_article:
            previous_associations = previous_article.get("associations", {})
            for prev_assoc in previous_associations.values():
                if prev_assoc and isinstance(prev_assoc, dict):
                    prev_guid = prev_assoc.get("guid")
                    if prev_guid:
                        previous_guids.add(prev_guid)

        # Compare current associations with previous ones
        for assoc in article_associations.values():
            if assoc and isinstance(assoc, dict):
                guid = assoc.get("guid")
                if guid:
                    is_new = guid not in previous_guids
                    result[guid] = {"role": "isNew", "value": "Yes" if is_new else "No"}

        return result

    def _handle_images(self, name, rendition, guid, item_type):
        """Handle image renditions similar to Lambda function but without S3 upload."""
        try:
            href = rendition.get("href", "")
            if not href:
                return None

            # For formatter, we keep the original href (no S3 transformation)
            return {
                "name": name,
                "href": href,
                "contenttype": "image/jpeg",
                "height": int(rendition.get("height", 0)),
                "width": int(rendition.get("width", 0)),
            }
        except Exception as e:
            logger.error(f"Error handling image rendition: {str(e)}")
            return None

    def _handle_audios(self, name, mimetype, rendition, guid):
        """Handle audio renditions similar to Lambda function but without S3 upload."""
        try:
            href = rendition.get("href", "")
            if not href:
                return None

            # For formatter, we keep the original href (no S3 transformation)
            return {"name": name, "href": href, "contenttype": mimetype}
        except Exception as e:
            logger.error(f"Error handling audio rendition: {str(e)}")
            return None

    def _handle_videos(self, name, rendition, guid, article):
        """Handle video renditions similar to Lambda function but without S3 upload."""
        try:
            href = rendition.get("href", "")
            if not href:
                return None

            # Get filemeta_json from the article
            filemeta_json = article.get("filemeta_json", {})
            if isinstance(filemeta_json, str):
                try:
                    filemeta_json = json.loads(filemeta_json)
                except Exception as e:
                    logger.error(f"Error parsing filemeta_json: {str(e)}")
                    filemeta_json = {}

            # Use 'main' instead of 'original' for video name
            if name == "original":
                name = "main"

            width = int(filemeta_json.get("width", 0))
            height = int(filemeta_json.get("height", 0))
            duration = self._parse_duration(filemeta_json.get("duration", 0))
            sizeinbytes = int(filemeta_json.get("length", 0))

            return {
                "name": name,
                "title": f"Full Resolution (MP4 {height}x{width})",
                "format": "mp4",
                "href": href,
                "sizeinbytes": sizeinbytes,
                "width": width,
                "height": height,
                "duration": duration,
                "contenttype": filemeta_json.get("mime_type", "video/mp4"),
            }
        except Exception as e:
            logger.error(f"Error handling video rendition: {str(e)}")
            return None

    def _parse_duration(self, duration_value):
        """Convert duration value to integer seconds."""
        if not duration_value:
            return 0

        if isinstance(duration_value, int):
            return duration_value

        if isinstance(duration_value, str):
            # Try parsing as timestamp (HH:MM:SS.ms)
            if ":" in duration_value:
                try:
                    parts = duration_value.split(":")
                    if len(parts) == 3:
                        hours = int(parts[0])
                        minutes = int(parts[1])
                        seconds = float(parts[2])
                        return int(hours * 3600 + minutes * 60 + seconds)
                except (ValueError, IndexError):
                    pass

            # Try parsing as number string
            try:
                return int(float(duration_value))
            except (ValueError, TypeError):
                pass

        return 0

    def _build_renditions_list(self, article):
        """Build renditions list similar to Lambda function logic."""
        renditions = []
        guid = article.get("guid", "")
        item_type = article.get("type", "")

        for key, value in article.get("renditions", {}).items():
            if not value:
                continue

            mimetype = value.get("mimetype", "")

            if "image" in mimetype and (item_type == "picture" or item_type == "video"):
                rendition = self._handle_images(key, value, guid, item_type)
                if rendition:
                    renditions.append(rendition)
            elif "audio" in mimetype and item_type == "audio":
                rendition = self._handle_audios(key, mimetype, value, guid)
                if rendition:
                    renditions.append(rendition)
            elif "video" in mimetype and item_type == "video":
                rendition = self._handle_videos(key, value, guid, article)
                if rendition:
                    renditions.append(rendition)

        return renditions
