import os
import cp
import lxml
import arrow
import superdesk
import lxml.etree as etree
import cp.ingest.parser.globenewswire as globenewswire
import superdesk.etree as sd_etree

from num2words import num2words
from collections import OrderedDict
from celery.utils.functional import uniq
from superdesk.utc import utc_to_local
from superdesk.text_utils import get_text, get_word_count
from superdesk.publish.formatters import Formatter
from superdesk.media.renditions import get_rendition_file_name
from superdesk.metadata.item import SCHEDULE_SETTINGS
from apps.publish.enqueue import get_enqueue_service

from cp.utils import format_maxlength


DEFAULT_DATETIME = "0001-01-01T00:00:00"

DATELINE_MAPPING = OrderedDict(
    (
        ("city", "City"),
        ("state", "Province"),
        ("country", "Country"),
    )
)

OUTPUT_LENGTH_LIMIT = 128

PICTURE_TYPES = {
    "picture",
    "graphic",
}

PICTURE_CATEGORY_MAPPING = {
    cp.PHOTO_CATEGORIES: "Category",
    cp.PHOTO_SUPPCATEGORIES: "SupplementalCategories",
}

PLACELINE_REPLACE = {
    "Washington, D.C.": "District of Columbia",
}

INLINE_ELEMENTS = {
    "strong",
    "em",
    "a",
}


def slug(item) -> str:
    """Item slugline.

    This should stay the same for updates/corrections,
    thus using id from AP if available.

    Slug must be 32-36 characters long, check that for
    external ids and use internal one if it's too short.
    """
    try:
        _guid = item["extra"][cp.ORIG_ID]
        if is_french(item) and item.get("type") == "text":
            _guid = _guid[:30] + "fa"
    except KeyError:
        _guid = ""
    if len(_guid) < cp.SLUG_LEN:
        _guid = guid(item)
    return str(_guid)


def guid(item) -> str:
    """Get superdesk item guid."""
    return item["guid"].split("_")[0]


def media_ref(item, split=True) -> str:
    """Media item reference based on original rendition."""
    try:
        original = item["renditions"]["original"]
        filename = get_rendition_file_name(original)
        return os.path.splitext(filename)[0] if split else filename
    except KeyError:
        return guid(item)


def filename(item) -> str:
    """Get filename for item.

    For images it's is based on original rendition filename
    to match the binary filename.

    For other items it's superdesk guid.
    """
    if item["type"] == "picture":
        return media_ref(item)
    return guid(item)


def is_french(item) -> bool:
    return "fr" in item.get("language", "en")


class Jimi2Formatter(Formatter):

    ENCODING = "utf-8"

    type = "jimi_2"
    name = "Jimi XML 2"

    def can_format(self, format_type, article):
        return format_type == self.type

    def format(self, article, subscriber, codes=None):
        output = []
        services = [
            s.get("name")
            for s in article.get("subject") or []
            if s.get("scheme") == cp.SERVICE
        ]
        if not services:
            services.append(None)
        for service in services:
            pub_seq_num = superdesk.get_resource_service(
                "subscribers"
            ).generate_sequence_number(subscriber)
            root = etree.Element("Publish")
            self._format_item(root, article, pub_seq_num, service, services)
            xml = etree.tostring(
                root, pretty_print=True, encoding=self.ENCODING, xml_declaration=True
            )
            output.append((pub_seq_num, xml.decode(self.ENCODING)))
        return output

    def _format_subject_code(self, root, item, elem, scheme) -> None:
        subject = item.get("subject") or []
        for subj in subject:
            if subj.get("scheme") == scheme and subj.get("qcode"):
                etree.SubElement(root, elem).text = subj["qcode"]

    def _format_item(self, root, item, pub_seq_num, service, services) -> None:

        # Added Fix here to fetch Parents of Manual Tags.

        item = self._add_parent_manual_tags(item)

        if is_picture(item):
            D2P1 = "http://www.w3.org/2001/XMLSchema-instance"
            content = etree.SubElement(
                root,
                "ContentItem",
                {"{%s}type" % D2P1: "PhotoContentItem"},
                nsmap={
                    "d2p1": D2P1,
                },
            )
        else:
            content = etree.SubElement(root, "ContentItem")
        extra = item.get("extra") or {}

        # root system fields
        etree.SubElement(root, "Reschedule").text = "false"
        etree.SubElement(root, "IsRegional").text = "false"
        etree.SubElement(root, "CanAutoRoute").text = "true"
        etree.SubElement(root, "PublishID").text = str(pub_seq_num)
        etree.SubElement(root, "Username")
        etree.SubElement(root, "UseLocalsOut").text = "false"
        etree.SubElement(root, "UserProfileID").text = "0"
        etree.SubElement(root, "PublishOrder").text = "0"
        etree.SubElement(root, "NewCycle").text = "false"
        etree.SubElement(root, "OnlineResend").text = "false"

        # item system fields
        etree.SubElement(content, "AutoSaveID").text = "0"
        etree.SubElement(content, "Type").text = "0"
        etree.SubElement(content, "MediaType").text = "0"
        etree.SubElement(content, "Status").text = "0"

        if is_picture(item):
            etree.SubElement(root, "Services").text = "Pictures"
            self._format_subject_code(root, item, "PscCodes", cp.DESTINATIONS)
            if root.find("PscCodes") is None:
                etree.SubElement(root, "PscCodes").text = "Online"
        elif service:
            etree.SubElement(root, "Services").text = "Écrit" if is_french(item) else "Print"
            etree.SubElement(root, "PscCodes").text = service
        else:
            self._format_subject_code(root, item, "PscCodes", cp.DESTINATIONS)
            self._format_services(root, item)

        is_broadcast = cp.is_broadcast(item)

        # content system fields
        orig = self._get_original_item(item)
        seq_id = "{:08d}".format(pub_seq_num % 100000000)
        item_id = "{:08d}".format(self.get_item_id(orig) % 100000000)
        etree.SubElement(content, "Name")
        etree.SubElement(content, "Cachable").text = "false"
        etree.SubElement(content, "FileName").text = filename(orig)
        etree.SubElement(content, "NewsCompID").text = item_id
        etree.SubElement(content, "SystemSlug").text = slug(orig)
        etree.SubElement(content, "ContentItemID").text = seq_id
        etree.SubElement(content, "ProfileID").text = "204"
        etree.SubElement(content, "SysContentType").text = "0"

        if is_picture(item):
            etree.SubElement(content, "PhotoContentItemID").text = item_id

        if extra.get(cp.FILENAME):
            etree.SubElement(content, "OrigTransRef").text = extra[cp.FILENAME]

        if service:
            etree.SubElement(content, "Note").text = ",".join(services)

        # timestamps
        firstpublished = item.get("firstpublished") or item["versioncreated"]
        etree.SubElement(root, "PublishDateTime").text = self._format_datetime(
            firstpublished
        )
        try:
            etree.SubElement(content, "EmbargoTime").text = self._format_datetime(
                item[SCHEDULE_SETTINGS]["utc_embargo"],
                local=True,
            )
        except KeyError:
            etree.SubElement(content, "EmbargoTime").text = self._format_datetime(
                item.get("embargoed"), local=True
            )
        etree.SubElement(content, "CreatedDateTime").text = self._format_datetime(
            firstpublished
        )  # SDCP-380
        etree.SubElement(content, "UpdatedDateTime").text = self._format_datetime(
            item["versioncreated"], rel=True
        )

        # obvious
        etree.SubElement(content, "ContentType").text = (
            "Photo" if is_picture(item) else item["type"].capitalize()
        )

        # SDCP-309
        etree.SubElement(content, "Headline").text = format_maxlength(
            extra.get(cp.HEADLINE2) or item.get("headline"), OUTPUT_LENGTH_LIMIT
        )
        if not is_picture(item):
            etree.SubElement(content, "Headline2").text = format_maxlength(
                item.get("headline"), OUTPUT_LENGTH_LIMIT
            )

        etree.SubElement(content, "SlugProper").text = item.get("slugline")
        etree.SubElement(content, "Credit").text = self._format_credit(item)
        etree.SubElement(content, "Source").text = item.get("source")

        content_html = self._format_content(item, is_broadcast)
        etree.SubElement(content, "DirectoryText").text = self._format_text(
            item.get("abstract")
        )
        etree.SubElement(content, "ContentText").text = self._format_html(content_html)
        etree.SubElement(content, "Language").text = (
            "2" if is_french(item) else "1"
        )

        if item["type"] == "text" and content_html:
            content.find("DirectoryText").text = format_maxlength(
                get_text(content_html, "html", lf_on_block=False).replace("\n", " "),
                200,
            )
            word_count = str(get_word_count(content_html))
            etree.SubElement(content, "Length").text = word_count
            etree.SubElement(content, "WordCount").text = word_count
            etree.SubElement(content, "BreakWordCount").text = word_count

        if item.get("keywords") and item.get("source") == globenewswire.SOURCE:
            etree.SubElement(content, "Stocks").text = ",".join(item["keywords"])

        #  IndexCodes are set here
        
        self._format_category_index(content, item)
        self._format_genre(content, item)
        self._format_urgency(content, item.get("urgency"), item["language"])
        self._format_keyword(
            content,
            item.get("keywords"),
            ", " if item.get("type") == "picture" else ",",
        )
        self._format_dateline(content, item.get("dateline"))
        self._format_writethru(content, item)

        if item.get("byline"):
            etree.SubElement(content, "Byline").text = item["byline"]

        if is_picture(item):
            self._format_picture_metadata(content, item)
        else:
            etree.SubElement(content, "EditorNote").text = item.get("ednote")
            if extra.get(cp.UPDATE):
                etree.SubElement(content, "UpdateNote").text = extra[cp.UPDATE]
            if extra.get(cp.CORRECTION):
                etree.SubElement(content, "Corrections").text = extra[cp.CORRECTION]

        if item.get("associations"):
            self._format_associations(content, item)
        

    def get_item_id(self, item):
        if item.get("family_id"):
            ingest_item = superdesk.get_resource_service("ingest").find_one(req=None, _id=item["family_id"])
            if ingest_item and ingest_item.get("unique_id"):
                return ingest_item["unique_id"]
        return item["unique_id"]

    def _format_credit(self, item):
        credit = item.get("creditline")
        if credit == "ASSOCIATED PRESS" or item.get("original_source") == "AP":
            return "THE ASSOCIATED PRESS"
        elif not credit and item.get("source") == "CP":
            return "THE CANADIAN PRESS"
        return credit or item.get("source") or ""

    def _format_urgency(self, content, urgency, language):
        if urgency is None:
            urgency = 3
        etree.SubElement(content, "RankingValue").text = str(urgency)
        cv = superdesk.get_resource_service("vocabularies").find_one(
            req=None, _id="urgency"
        )
        items = [item for item in cv["items"] if str(item.get("qcode")) == str(urgency)]
        if items:
            name = _get_name(items[0], language)
            etree.SubElement(content, "Ranking").text = name

    def _format_keyword(self, content, keywords, glue):
        if keywords:
            etree.SubElement(content, "Keyword").text = format_maxlength(
                glue.join(keywords), 150
            )

    def _format_writethru(self, content, item):
        try:
            num = item["extra"]["ap_version"]
        except KeyError:
            num = 0
        num += item.get("rewrite_sequence") or 0
        etree.SubElement(content, "WritethruValue").text = str(num or 0)
        if not num:
            return
        etree.SubElement(content, "WritethruNum").text = num2words(
            num, to="ordinal_num", lang=item["language"].replace("-", "_")
        ).replace(
            "me", "ème"
        )  # stick with jimi
        etree.SubElement(content, "WriteThruType").text = (
            "Lead" if "fr" in item["language"] else "Writethru"
        )

    def _format_datetime(self, datetime, rel=False, local=False):
        if not datetime:
            return DEFAULT_DATETIME
        datetime = to_datetime(datetime)
        if rel or local:
            datetime = utc_to_local(cp.TZ, datetime)
        fmt = "%Y-%m-%dT%H:%M:%S{}".format(
            "%z" if rel else "",
        )
        formatted = datetime.strftime(fmt)
        if rel:
            return formatted[:-2] + ":" + formatted[-2:]  # add : to timezone offset
        return formatted

    def _format_text(self, value):
        return get_text(self._format_html(value), "html", True, True).strip()

    def _format_html(self, value):
        html = value or ""
        html = html.replace("<br>", "<br />")
        return html

    def _format_dateline(self, content, dateline):
        if dateline and dateline.get("located"):
            pieces = []
            located = dateline["located"]
            for src, dest in DATELINE_MAPPING.items():
                text = located.get(src) or ""
                text = PLACELINE_REPLACE.get(text, text)
                etree.SubElement(content, dest).text = text
                pieces.append(text)
            placeline = ";".join(pieces)
            etree.SubElement(content, "Placeline").text = placeline
            try:
                etree.SubElement(content, "Latitude").text = str(
                    located["location"]["lat"]
                )
                etree.SubElement(content, "Longitude").text = str(
                    located["location"]["lon"]
                )
            except KeyError:
                pass
        else:
            etree.SubElement(content, "Placeline")

    # Creating a new Method FOr adding Parents in Manually added Index Codes
    def _add_parent_manual_tags(self, item):
        cv = superdesk.get_resource_service("vocabularies").find_one(req=None, _id="subject_custom")
        vocab_items = cv.get("items", [])
        vocab_mapping = {v['qcode']: v for v in vocab_items}

        def find_oldest_parent(qcode):
            parent_qcode = vocab_mapping[qcode]['parent']
            while parent_qcode:
                if vocab_mapping[parent_qcode]['in_jimi'] and vocab_mapping[parent_qcode]['parent'] is None:
                    return vocab_mapping[parent_qcode]
                parent_qcode = vocab_mapping.get(parent_qcode, {}).get('parent', None)
            return None

        updated_subjects = item.get('subject', []).copy()  # Copy the current subjects to avoid direct modification

        for subject in item.get('subject', []):
            if 'qcode' in subject and subject['qcode'] in vocab_mapping:
                oldest_parent = find_oldest_parent(subject['qcode'])
                if oldest_parent and oldest_parent['qcode'] not in [s['qcode'] for s in updated_subjects]:
                    # Add the entire oldest parent tag to the item's subjects
                    updated_subjects.append(oldest_parent)

        item['subject'] = updated_subjects
        return item





    def _format_category_index(self, content, item):
        categories = self._get_categories(item)
        indexes = uniq(categories + self._get_indexes(item))

        

        #  Add code here to remove the small case letters from here
        filtered_indexes = [index for index in indexes if not index[0].islower()]
        # Remove empty strings from the filtered list
        indexes = [index for index in filtered_indexes if index]
        

        if categories:
            etree.SubElement(content, "Category").text = ",".join(categories)
        if indexes:
            etree.SubElement(content, "IndexCode").text = ",".join(indexes)
        else:
            etree.SubElement(content, "IndexCode")

    def _resolve_names(self, selected_items, language, cv_id, jimi_only=True):
        cv = superdesk.get_resource_service("vocabularies").find_one(
            req=None, _id=cv_id
        )
        names = []

        filtered_items = filter_items_by_jimi(cv["items"], jimi_only=True)

        if not cv:
            return names
        for selected_item in selected_items:
            item = _find_qcode_item(selected_item["qcode"], filtered_items, jimi_only)
            
            if item:
                name = _get_name(item, language)
                
            else:
                name = None

            if name is not None and name not in names:
                names.append(name)
        
        
        return names
    

    def _resolve_names_categories(self, selected_items, language, cv_id, jimi_only=True):
        cv = superdesk.get_resource_service("vocabularies").find_one(
            req=None, _id=cv_id
        )
        names = []
        if not cv:
            return names
        for selected_item in selected_items:
            item = _find_qcode_item(selected_item["qcode"], cv["items"], jimi_only)
            name = (
                _get_name(item, language)
                if item
                else _get_name(selected_item, language)
            )
            if name and name not in names:
                names.append(name)
        return names
    


    def _get_categories(self, item):
        if not item.get("anpa_category"):
            return []
        names = self._resolve_names_categories(
            item["anpa_category"], item["language"], "categories", False
        )
        return names

    #  This was changed for IndeCodes Updates
    def _get_indexes(self, item):
        SUBJECTS_ID = "subject_custom"

        SUBJECTS_ID_2 = "subject"

        SUBJECTS_ID_3 = "http://cv.iptc.org/newscodes/mediatopic/"


        subject = [
            s
            for s in item.get("subject", [])
            if s.get("name") and s.get("scheme") in (None, SUBJECTS_ID, SUBJECTS_ID_2, SUBJECTS_ID_3)
        ]

        return self._resolve_names(subject, item["language"], SUBJECTS_ID)

    def _format_genre(self, content, item):
        version_type = etree.SubElement(content, "VersionType")
        if item.get("genre"):
            names = self._resolve_names_categories(item["genre"], item["language"], "genre", False)
            if names:
                version_type.text = names[0]

    def _format_services(self, root, item):
        try:
            services = [
                s for s in item["subject"] if s.get("scheme") == cp.DISTRIBUTION
            ]
        except KeyError:
            return
        names = self._resolve_names_categories(services, item["language"], cp.DISTRIBUTION, False)
        if names:
            etree.SubElement(root, "Services").text = names[0]

    def _format_picture_metadata(self, content, item):
        # no idea how to populate these
        etree.SubElement(content, "HeadlineService").text = "false"
        etree.SubElement(content, "VideoType").text = "None"
        etree.SubElement(content, "PhotoType").text = "None"
        etree.SubElement(content, "GraphicType").text = "None"
        etree.SubElement(content, "ReadOnlyFlag").text = "true"
        etree.SubElement(content, "HoldFlag").text = "false"
        etree.SubElement(content, "OpenFlag").text = "false"
        etree.SubElement(content, "TransmittedToWire").text = "false"
        etree.SubElement(content, "TrashFlag").text = "false"
        etree.SubElement(content, "TopStory").text = "false"
        etree.SubElement(content, "AuthorVersion").text = "0"
        etree.SubElement(content, "BreakWordCount").text = "0"
        etree.SubElement(content, "WordCount").text = "0"
        etree.SubElement(content, "HandledByUserID").text = "0"
        etree.SubElement(content, "Length").text = "0"
        etree.SubElement(content, "Published").text = "false"
        etree.SubElement(content, "PhotoLinkCount").text = "0"
        etree.SubElement(content, "VideoLinkCount").text = "0"
        etree.SubElement(content, "AudioLinkCount").text = "0"
        etree.SubElement(content, "IsPublishedAsTopStory").text = "false"

        extra = item.get("extra") or {}
        etree.SubElement(content, "DateTaken").text = self._format_datetime(
            item.get("firstcreated")
        )

        for scheme, elem in PICTURE_CATEGORY_MAPPING.items():
            code = [
                subj["qcode"]
                for subj in item.get("subject", [])
                if subj.get("scheme") == scheme
            ]
            if code:
                dest = (
                    content.find(elem)
                    if content.find(elem) is not None
                    else etree.SubElement(content, elem)
                )
                dest.text = code[0]

        pic_filename = self._format_picture_filename(item)
        if pic_filename:
            etree.SubElement(content, "ViewFile").text = pic_filename
            etree.SubElement(content, "ContentRef").text = pic_filename

        if item.get("headline") and not item.get("slugline"):
            content.find("SlugProper").text = item["headline"]

        if item.get("original_source"):
            content.find("Source").text = item["original_source"]

        if extra.get(cp.ARCHIVE_SOURCE):
            etree.SubElement(content, "ArchiveSources").text = extra[cp.ARCHIVE_SOURCE]

        if extra.get(cp.PHOTOGRAPHER_CODE):
            etree.SubElement(content, "BylineTitle").text = extra[
                cp.PHOTOGRAPHER_CODE
            ].upper()

        if item.get("copyrightnotice"):
            etree.SubElement(content, "Copyright").text = item["copyrightnotice"][:50]

        if item.get("description_text"):
            etree.SubElement(content, "EnglishCaption").text = item[
                "description_text"
            ].replace("  ", " ")

        if extra.get(cp.CAPTION_WRITER):
            etree.SubElement(content, "CaptionWriter").text = extra[cp.CAPTION_WRITER]

        if item.get("ednote"):
            etree.SubElement(content, "SpecialInstructions").text = item["ednote"]

        if extra.get("itemid"):
            etree.SubElement(content, "CustomField1").text = extra["itemid"]

        if pic_filename:
            etree.SubElement(content, "CustomField2").text = content.find(
                "FileName"
            ).text

        if extra.get(cp.INFOSOURCE):
            etree.SubElement(content, "CustomField6").text = extra[cp.INFOSOURCE]

        if extra.get(cp.XMP_KEYWORDS):
            etree.SubElement(content, "XmpKeywords").text = extra[cp.XMP_KEYWORDS]

        if extra.get("container"):
            etree.SubElement(content, "ContainerIDs").text = extra["container"]
        else:
            self._format_refs(content, item)

    def _format_refs(self, content, item):
        """ContainerIDs shoud link to SystemSlug of story."""
        refs = set(
            [
                slug(self._get_original_item(ref))
                for ref in superdesk.get_resource_service("news").get(
                    req=None, lookup={"refs.guid": item["guid"]}
                )
                if ref.get("pubstatus") == "usable"
            ]
        )

        if refs:
            etree.SubElement(content, "ContainerIDs").text = ", ".join(sorted(refs))

    def _format_picture_filename(self, item):
        ref = media_ref(item, split=False)
        if ref:
            return ref
        if item.get("extra") and item["extra"].get(cp.FILENAME):
            created = to_datetime(item["firstcreated"])
            return "{transref}-{date}_{year}_{time}.jpg".format(
                transref=item["extra"][cp.FILENAME],
                year=created.strftime("%Y"),
                date="{}{}".format(created.month, created.day),
                time=created.strftime("%H%M%S"),
            )

    def _format_associations(self, content, item):
        """When association is already published we need to resend it again
        with link to text item.
        """
        guids = set()
        photos = []
        for assoc in item["associations"].values():
            if assoc:
                published = superdesk.get_resource_service(
                    "published"
                ).get_last_published_version(assoc["_id"])
                if (
                    published and published["pubstatus"] == "usable" and False
                ):  # disable for the time being
                    published.setdefault("extra", {})["container"] = item["guid"]
                    publish_service = get_enqueue_service("publish")
                    subscribers = [
                        subs
                        for subs in publish_service.get_subscribers(published, None)[0]
                        if any(
                            [
                                dest["format"] == "jimi"
                                for dest in subs.get(cp.DESTINATIONS, [])
                            ]
                        )
                    ]
                    publish_service.resend(published, subscribers)
                if (
                    assoc.get("type") == "picture"
                    and assoc.get("guid")
                    and assoc["guid"] not in guids
                ):
                    guids.add(assoc["guid"])
                    photos.append(assoc)
        etree.SubElement(content, "PhotoType").text = get_count_label(
            len(photos), item["language"]
        )
        if photos:
            etree.SubElement(content, "PhotoReference").text = ",".join(
                filter(None, [media_ref(photo) for photo in photos])
            )

    def _get_original_item(self, item):
        orig = item
        for i in range(100):
            if not orig.get("rewrite_of"):
                return orig
            next_orig = superdesk.get_resource_service("archive").find_one(
                req=None, _id=orig["rewrite_of"]
            )
            if next_orig is not None:
                orig = next_orig
                continue
            break
        return orig

    def _format_filename(self, item):
        """Get filename for item.

        For images it's is based on original rendition filename
        to match the binary filename.

        For other items it's superdesk guid.
        """
        if item["type"] == "picture":
            return media_ref(item)
        return guid(item)

    def _format_content(self, item, is_broadcast):
        if is_broadcast and item.get("abstract"):
            content = item["abstract"]
            if "<p>" not in content:
                content = "<p>{}</p>".format(content)
        else:
            content = item.get("body_html")
        if not content:
            return ""
        tree = lxml.html.fromstring(content)
        for elem in tree.iter():
            if elem.tag == "b":
                elem.tag = "strong"
            elif elem.tag == "i":
                elem.tag = "em"

            # Remove whitespace and empty tags
            if elem.tag in INLINE_ELEMENTS and elem.text is not None and not elem.text.strip():
                elem.drop_tree()

        return sd_etree.to_string(tree, encoding="unicode", method="html")


def get_count_label(count, lang):
    is_fr = "fr" in (lang or "")
    if count == 0:
        return "None" if not is_fr else "Aucun"
    elif count == 1:
        return "One"
    else:
        return "Many"


def to_datetime(value):
    if value and isinstance(value, str):
        return arrow.get(value)
    return value

def filter_items_by_jimi(items, jimi_only=True):
    """Filter items where 'in_jimi' is true."""
    if jimi_only:
        return [item for item in items if item.get("in_jimi", False)]
    return items

def _find_qcode_item(code, items, jimi_only=True):
    for item in items:
        if item.get("qcode") == code:
            if not jimi_only:               
                pass
            if item.get("in_jimi"):
                
                return item
            elif item.get("parent"):
                return _find_qcode_item(item["parent"], items, jimi_only)
            break

        elif item.get("semaphore_id") == code:
            
            if not jimi_only:
                pass
            if item.get("in_jimi"):
                
                return item
            elif item.get("parent"):
                return _find_qcode_item(item["parent"], items, jimi_only)
            break



def _get_name(item, language):

    
    lang = language.replace("_", "-")
    if "-CA" not in lang:
        lang = "{}-CA".format(lang)
    try:
        
        return item["translations"]["name"][lang]
    except (KeyError,):
        pass
    try:
        
        return item["translations"]["name"][lang.split("-")[0]]
    except (KeyError,):
        pass
    return item["name"]


def _is_same_news_cycle(a, b):
    return True  # not sure if we will need this cycle thing so keeping it for now
    CYCLE_TZ = "America/New_York"
    CYCLE_START_HOUR = 2

    edt_time_a = utc_to_local(CYCLE_TZ, a["firstcreated"])
    edt_time_b = utc_to_local(CYCLE_TZ, b["firstcreated"])

    min_dt = min(edt_time_a, edt_time_b)
    max_dt = max(edt_time_a, edt_time_b)

    if min_dt.hour < CYCLE_START_HOUR and max_dt.hour >= CYCLE_START_HOUR:
        return False

    return min_dt.date() == max_dt.date()


def is_picture(item):
    return item.get("type") in PICTURE_TYPES
