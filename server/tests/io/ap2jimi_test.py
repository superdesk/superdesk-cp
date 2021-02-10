import re
import cp
import flask
import os.path
import unittest
import superdesk
import requests_mock
import settings

from lxml import etree
from flask import json
from unittest.mock import MagicMock, patch

from tests.mock import SEQUENCE_NUMBER, resources
from tests.ingest.parser import get_fixture_path

from cp.ingest import CP_APMediaFeedParser
from cp.output.formatter.jimi import JimiFormatter


parser = CP_APMediaFeedParser()
formatter = JimiFormatter()


def fixture(filename):
    return os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        filename,
    )


class AP2JimiTestCase(unittest.TestCase):

    app = flask.Flask(__name__)
    app.locators = MagicMock()
    app.config.update({"AP_TAGS_MAPPING": settings.AP_TAGS_MAPPING})

    provider = {}
    subscriber = {}

    maxDiff = None

    def parse_format(self, source, binary=None, service=None):
        with open(get_fixture_path(source, "ap")) as fp:
            data = json.load(fp)

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                with requests_mock.mock() as mock:
                    if binary:
                        with open(get_fixture_path(binary, "ap"), "rb") as f:
                            mock.get(
                                data["data"]["item"]["renditions"]["preview"]["href"],
                                content=f.read(),
                            )
                    parsed = parser.parse(data, self.provider)
                parsed["_id"] = "superdesk-id"
                parsed["guid"] = "superdesk-guid"
                parsed["unique_id"] = 1
                parsed["family_id"] = parsed["_id"]
                parsed["renditions"] = {
                    "original": {"media": "abcd-media", "mimetype": "image/jpeg"}
                }
                if service:
                    parsed.setdefault("subject", []).append(
                        {
                            "name": service,
                            "qcode": service,
                            "scheme": cp.DISTRIBUTION,
                        }
                    )
                jimi = formatter.format(parsed, self.subscriber)[0][1]

        root = etree.fromstring(jimi.encode(formatter.ENCODING))
        return root.find("ContentItem")

    def test_getty_picture(self):
        """
        ref: tests/io/fixtures/6dd9971f75c24ce59865879cf315d7fe-6dd9971f75c24ce59.xml
        """
        item = self.parse_format("ap-getty-picture.json", "preview.jpg")
        self.assertEqual("Stuart Franklin", item.find("Byline").text)
        self.assertEqual("S", item.find("Category").text)
        self.assertEqual("THE ASSOCIATED PRESS", item.find("Credit").text)
        self.assertEqual(
            "Virus-Outbreak-Germany-Soccer-Bundesliga", item.find("SlugProper").text
        )
        self.assertEqual("Unknown AP", item.find("Source").text)
        self.assertEqual("Bremen", item.find("City").text)
        self.assertEqual("Germany", item.find("Country").text)
        self.assertEqual("Bremen;;Germany", item.find("Placeline").text)
        self.assertEqual("DMSC113", item.find("OrigTransRef").text)
        self.assertEqual("POOL", item.find("BylineTitle").text)
        self.assertEqual("bl", item.find("CaptionWriter").text)
        self.assertEqual("(c) Getty Images Europe/Pool", item.find("Copyright").text)
        self.assertEqual(
            "Frankfurt's Stefan IIsanker, right, celebrates after he scores his side second goal during "
            "the German Bundesliga soccer match between SV Werder Bremen and Eintracht Frankfurt "
            "in Bremen, Germany, Wednesday, June 3, 2020. Because of the coronavirus outbreak all soccer "
            "matches of the German Bundesliga take place without spectators. "
            "(Stuart Franklin/Pool via AP)",
            item.find("EnglishCaption").text,
        )
        self.assertEqual("2020-06-03T20:22:03", item.find("DateTaken").text)
        self.assertEqual("SOC", item.find("SupplementalCategories").text)
        self.assertEqual(
            "POOL PHOTO, THE DEUTSCHE FUSSBALL LIGA DFL DOES NOT ALLOW THE IMAGES TO BE USED AS "
            "SEQUENCES TO EMULATE VIDEO.",
            item.find("SpecialInstructions").text,
        )
        self.assertEqual("Unknown AP", item.find("ArchiveSources").text)
        self.assertEqual(
            "6dd9971f75c24ce59865879cf315d7fe", item.find("CustomField1").text
        )
        self.assertEqual("POOL Getty Images", item.find("CustomField6").text)

    def test_ap_picture(self):
        """
        ref: tests/io/fixtures/AB101-65_2020_101001.xml
        """
        item = self.parse_format("ap-picture.json", "preview-keywords.jpg")
        self.assertEqual(
            "PhotoContentItem",
            item.get("{http://www.w3.org/2001/XMLSchema-instance}type"),
        )
        self.assertIsNone(item.find("Name").text)
        self.assertEqual("false", item.find("Cachable").text)
        self.assertIsNotNone(item.find("NewsCompID").text)
        self.assertEqual("0", item.find("AutoSaveID").text)
        self.assertEqual("0", item.find("Type").text)
        self.assertEqual("0", item.find("MediaType").text)
        self.assertEqual("0", item.find("Status").text)
        self.assertIsNotNone(item.find("SystemSlug").text)
        self.assertEqual("abcd-media", item.find("FileName").text)  # using guid
        self.assertEqual("Alvaro Barrientos", item.find("Byline").text)
        self.assertEqual("false", item.find("HeadlineService").text)
        self.assertEqual("None", item.find("VideoType").text)
        self.assertEqual("I", item.find("Category").text)
        self.assertEqual("News - Optional", item.find("Ranking").text)
        self.assertEqual("5", item.find("RankingValue").text)
        self.assertEqual("None", item.find("PhotoType").text)
        self.assertEqual("None", item.find("GraphicType").text)
        self.assertEqual("true", item.find("ReadOnlyFlag").text)
        self.assertEqual("false", item.find("HoldFlag").text)
        self.assertEqual("false", item.find("OpenFlag").text)
        self.assertEqual("false", item.find("TransmittedToWire").text)
        self.assertEqual("false", item.find("TrashFlag").text)
        self.assertEqual("false", item.find("TopStory").text)
        self.assertEqual("abcd-media.jpg", item.find("ContentRef").text)
        self.assertEqual("Santos Munoz", item.find("Headline").text)
        self.assertEqual("THE ASSOCIATED PRESS", item.find("Credit").text)
        self.assertEqual("Photo", item.find("ContentType").text)
        self.assertEqual("Virus-Outbreak-Spain", item.find("SlugProper").text)
        self.assertEqual("The Associated Press", item.find("Source").text)
        self.assertEqual("0", item.find("AuthorVersion").text)
        self.assertEqual("0", item.find("BreakWordCount").text)
        self.assertIsNotNone(item.find("ContentItemID").text)
        self.assertEqual("204", item.find("ProfileID").text)
        self.assertEqual("0", item.find("SysContentType").text)
        self.assertEqual("0", item.find("WordCount").text)
        self.assertEqual("0001-01-01T00:00:00", item.find("EmbargoTime").text)
        self.assertEqual("1", item.find("Language").text)
        self.assertEqual("2020-06-05T13:09:39-04:00", item.find("UpdatedDateTime").text)
        self.assertEqual("2020-06-05T17:09:39", item.find("CreatedDateTime").text)
        self.assertEqual("0", item.find("HandledByUserID").text)
        self.assertIsNone(item.find("ContentText").text)
        self.assertEqual("Coronavirus, COVID-19", item.find("Keyword").text)
        self.assertEqual("0", item.find("Length").text)
        self.assertEqual("0", item.find("WritethruValue").text)
        self.assertEqual("Pamplona", item.find("City").text)
        self.assertEqual("Spain", item.find("Country").text)
        self.assertEqual(
            "42.81687", item.find("Latitude").text
        )  # using data from ap, jimi has it wrong
        self.assertEqual("-1.64323", item.find("Longitude").text)
        self.assertEqual("Pamplona;;Spain", item.find("Placeline").text)
        self.assertEqual("false", item.find("Published").text)
        self.assertEqual("0", item.find("PhotoLinkCount").text)
        self.assertEqual("0", item.find("VideoLinkCount").text)
        self.assertEqual("0", item.find("AudioLinkCount").text)
        self.assertEqual("false", item.find("IsPublishedAsTopStory").text)
        self.assertIsNotNone(item.find("PhotoContentItemID").text)
        self.assertEqual("AB101", item.find("OrigTransRef").text)
        self.assertEqual("STR", item.find("BylineTitle").text)
        self.assertEqual("AB", item.find("CaptionWriter").text)
        self.assertEqual(
            "Copyright 2019 The Associated Press. All rights re",
            item.find("Copyright").text,
        )
        self.assertEqual(
            "Santo Munoz, left, wearing a face mask to protect against the coronavirus, moves a robot "
            'known as "Alexia" to wait on customers at his bar at Plaza del Castillo square, in Pamplona, '
            "northern Spain, Friday, June 5, 2020. (AP Photo/Alvaro Barrientos)",
            item.find("EnglishCaption").text,
        )
        self.assertEqual("2020-06-05T10:10:01", item.find("DateTaken").text)
        self.assertEqual("abcd-media.jpg", item.find("ViewFile").text)
        self.assertEqual("AP", item.find("ArchiveSources").text)
        self.assertEqual("Coronavirus, COVID-19", item.find("XmpKeywords").text)
        self.assertEqual(
            "de1bb822362146388852c8b7eee93c76", item.find("CustomField1").text
        )
        self.assertEqual("abcd-media", item.find("CustomField2").text)
        self.assertEqual("AP", item.find("CustomField6").text)

        self.assertIsNone(item.find("Headline2"))

        root = item.getparent()
        self.assertEqual("Publish", root.tag)
        self.assertEqual("false", root.find("Reschedule").text)
        self.assertEqual("true", root.find("CanAutoRoute").text)
        self.assertEqual(str(SEQUENCE_NUMBER), root.find("PublishID").text)
        self.assertEqual("Pictures", root.find("Services").text)
        self.assertIsNone(root.find("Username").text)
        self.assertEqual("false", root.find("UseLocalsOut").text)
        self.assertEqual("Online", root.find("PscCodes").text)
        self.assertEqual("0", root.find("UserProfileID").text)
        self.assertEqual("0", root.find("PublishOrder").text)
        self.assertEqual("2020-06-05T17:09:39", root.find("PublishDateTime").text)
        self.assertEqual("false", root.find("NewCycle").text)
        self.assertEqual("false", root.find("OnlineResend").text)

    def test_ap_text(self):
        """
        ref: tests/io/fixtures/5d846ed8-96b6-4adc-a028-017b0fa5e2c1.xml
        """
        item = self.parse_format("ap-text.json")
        self.assertEqual(
            "f14dd246c9b5efeb56de0141aa50c4fd", item.find("SystemSlug").text
        )
        self.assertIn("superdesk-guid", item.find("FileName").text)
        self.assertEqual("Mark Kennedy", item.find("Byline").text)
        self.assertEqual(
            "Review: Documentary about electric racing holds little spark",
            item.find("Headline").text,
        )
        self.assertIn("Entertainment", item.find("Category").text)
        self.assertIn("Entertainment", item.find("IndexCode").text)
        self.assertEqual("Feature - Regular", item.find("Ranking").text)
        self.assertEqual("6", item.find("RankingValue").text)
        self.assertEqual(
            "Review: Documentary about electric racing holds little spark",
            item.find("Headline2").text,
        )
        self.assertEqual("THE ASSOCIATED PRESS", item.find("Credit").text)
        self.assertEqual("Text", item.find("ContentType").text)
        self.assertEqual("US-Film-Review-And-We-Go-Green", item.find("SlugProper").text)
        self.assertEqual("The Associated Press", item.find("Source").text)
        self.assertEqual("UPDATES: With AP Photos.", item.find("UpdateNote").text)
        self.assertEqual("533", item.find("BreakWordCount").text)
        self.assertEqual("533", item.find("WordCount").text)
        self.assertEqual("1", item.find("Language").text)
        self.assertEqual(
            "For proof that Leonardo DiCaprio can't save every film he touches, look no further than "
            "“And We Go Green,” a languid documentary about the electric car racing circuit. DiCaprio, "
            "who is a producer of",
            item.find("DirectoryText").text,
        )
        self.assertEqual(
            "2020-06-02T19:13:57", item.find("CreatedDateTime").text
        )  # using api data
        self.assertIn(
            "Arts and entertainment,Movies,Entertainment,Automotive technology,Industrial "
            "technology,Technology,Automobile racing,Sports,Form",
            item.find("Keyword").text,
        )
        self.assertEqual("3", item.find("WritethruValue").text)
        self.assertEqual("3rd", item.find("WritethruNum").text)

    def test_ap_broadcast(self):
        """
        ref: tests/io/fixtures/0c828d30-d250-4aec-9739-b04961eb36fc.xml
        """
        item = self.parse_format("ap-broadcast.json", service=cp.BROADCAST)
        expected = etree.parse(
            fixture("0c828d30-d250-4aec-9739-b04961eb36fc.xml")
        ).find("ContentItem")
        self.assertEqual(cp.BROADCAST, item.getparent().find("Services").text)
        self.assertEqual(
            re.sub(r"[\W]+", " ", item.find("ContentText").text),
            re.sub(r"[\W]+", " ", expected.find("ContentText").text),
        )
        self.assertEqual(
            re.sub(r"[\W]+", " ", item.find("DirectoryText").text)[:190],
            re.sub(r"[\W]+", " ", expected.find("DirectoryText").text)[:190],
        )
        self.assertEqual(
            "41148a074e2caa8190926b25a2a940f8", item.find("SystemSlug").text
        )
        self.assertEqual("superdesk-guid", item.find("FileName").text)

    def test_ap_category(self):
        item = self.parse_format("ap-category.json", service=cp.BROADCAST)
        self.assertEqual("Business,International", item.find("Category").text)
