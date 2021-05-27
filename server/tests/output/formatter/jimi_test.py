import os
import cp
import cp.ingest.parser.globenewswire as globenewswire

from pytz import UTC
from datetime import datetime, timedelta

from cp.output.formatter.jimi import JimiFormatter
from superdesk.metadata.item import SCHEDULE_SETTINGS

from tests.mock import resources, SEQUENCE_NUMBER

from . import BaseXmlFormatterTestCase


class JimiFormatterTestCase(BaseXmlFormatterTestCase):

    formatter = JimiFormatter()
    article = {
        "_id": "id",
        "guid": "id",
        "family_id": "famid",
        "type": "text",
        "headline": "Headline",
        "slugline": "slug",
        "creditline": "Credit",
        "source": "Source",
        "ednote": "Ednote",
        "word_count": 123,
        "abstract": "<p>Abstract</p>",
        "body_html": "<p>Body HTML<br>test <b>bold</b> and <i>idiom</i></p>",
        "keywords": ["Foo bar", "baz"],
        "anpa_category": [{"name": "National", "qcode": "n"}],
        "subject": [
            {"name": "health", "qcode": "07000000", "scheme": "subject_custom"},
            {"name": "citizens", "qcode": "20000575", "scheme": "subject_custom"},
            {"name": "Foo", "qcode": "1231245", "scheme": "foo"},
            {"name": "Print", "qcode": "Print", "scheme": cp.DISTRIBUTION},
            {
                "name": "The Associated Press",
                "qcode": "ap---",
                "scheme": cp.DESTINATIONS,
            },
        ],
        "urgency": 2,
        "language": "en-CA",
        "unique_id": 123,
        "firstcreated": datetime(2020, 4, 1, 11, 13, 12, 25, tzinfo=UTC),
        "versioncreated": datetime(2020, 4, 1, 11, 23, 12, 25, tzinfo=UTC),
        "firstpublished": datetime(2020, 4, 1, 11, 33, 12, 25, tzinfo=UTC),
        "genre": [
            {"name": "NewsAlert", "qcode": "NewsAlert"},
        ],
        "extra": {
            cp.HEADLINE2: "headline2",
            cp.FILENAME: "filename",
        },
    }

    def format_item(self, updates=None, return_root=False):
        xml = self.format(updates)
        root = self.parse(xml)
        if return_root:
            return root
        return root.find("ContentItem")

    def test_can_format(self):
        self.assertTrue(self.formatter.can_format("jimi", {}))

    def test_format(self):
        xml = self.format()
        self.assertIn("<?xml version='1.0' encoding='utf-8'?>", xml)
        self.assertIn("<ContentText>&lt;p&gt;Body HTML&lt;br /&gt;test", xml)

        root = self.parse(xml)
        self.assertEqual("Publish", root.tag)
        self.assertEqual("false", root.find("Reschedule").text)
        self.assertEqual("false", root.find("IsRegional").text)
        self.assertEqual("true", root.find("CanAutoRoute").text)
        self.assertEqual(str(SEQUENCE_NUMBER), root.find("PublishID").text)
        self.assertEqual("Print", root.find("Services").text)
        self.assertEqual(None, root.find("Username").text)
        self.assertEqual("false", root.find("UseLocalsOut").text)
        self.assertEqual("ap---", root.find("PscCodes").text)
        self.assertEqual("2020-04-01T11:33:12", root.find("PublishDateTime").text)

        item = root.find("ContentItem")
        self.assertEqual(None, item.find("Name").text)
        self.assertEqual("false", item.find("Cachable").text)

        # ids
        self.assertEqual("00000100", item.find("ContentItemID").text)
        self.assertEqual("00000123", item.find("NewsCompID").text)
        self.assertEqual(self.article["guid"], item.find("SystemSlug").text)
        self.assertEqual(self.article["guid"], item.find("FileName").text)
        self.assertEqual(
            self.article["extra"][cp.FILENAME], item.find("OrigTransRef").text
        )

        # obvious
        self.assertEqual("Text", item.find("ContentType").text)

        # SDCP-309
        self.assertEqual(self.article["headline"], item.find("Headline2").text)
        self.assertEqual("headline2", item.find("Headline").text)

        self.assertEqual(self.article["creditline"], item.find("Credit").text)
        self.assertEqual(self.article["slugline"], item.find("SlugProper").text)
        self.assertEqual(self.article["source"], item.find("Source").text)
        self.assertEqual(self.article["ednote"], item.find("EditorNote").text)
        self.assertEqual("6", item.find("WordCount").text)
        self.assertEqual("6", item.find("BreakWordCount").text)
        self.assertEqual("6", item.find("Length").text)
        self.assertEqual(
            "Body HTMLtest bold and idiom", item.find("DirectoryText").text
        )
        self.assertEqual(
            "<p>Body HTML<br />test <strong>bold</strong> and <em>idiom</em></p>",
            item.find("ContentText").text,
        )
        self.assertEqual(None, item.find("Placeline").text)
        self.assertEqual("0", item.find("WritethruValue").text)
        self.assertEqual("Foo bar,baz", item.find("Keyword").text)
        self.assertEqual("National", item.find("Category").text)
        self.assertEqual("National,Health,Politics", item.find("IndexCode").text)
        self.assertEqual(str(self.article["urgency"]), item.find("RankingValue").text)
        self.assertEqual("News - Need to Know", item.find("Ranking").text)
        self.assertEqual("1", item.find("Language").text)

        # timestamps
        self.assertEqual("0001-01-01T00:00:00", item.find("EmbargoTime").text)
        self.assertEqual("2020-04-01T11:33:12", item.find("CreatedDateTime").text)
        self.assertEqual("2020-04-01T07:23:12-04:00", item.find("UpdatedDateTime").text)

        # etc
        self.assertEqual("NewsAlert", item.find("VersionType").text)

    def test_writethru(self):
        expected_data = {
            1: "1st",
            2: "2nd",
            3: "3rd",
            4: "4th",
            5: "5th",
            10: "10th",
            100: "100th",
            101: "101st",
        }

        for val, num in expected_data.items():
            item = self.format_item({"rewrite_sequence": val})
            self.assertEqual(num, item.find("WritethruNum").text)
            self.assertEqual(str(val), item.find("WritethruValue").text)
            self.assertEqual("Writethru", item.find("WriteThruType").text)

    def test_dateline(self):
        item = self.format_item(
            {
                "dateline": {
                    "source": "AAP",
                    "text": "sample dateline",
                    "located": {
                        "alt_name": "",
                        "state": "California",
                        "city_code": "Los Angeles",
                        "city": "Los Angeles",
                        "dateline": "city",
                        "country_code": "US",
                        "country": "USA",
                        "tz": "America/Los_Angeles",
                        "state_code": "CA",
                        "location": {
                            "lat": 34.0522,
                            "lon": -118.2347,
                        },
                    },
                },
            }
        )
        self.assertEqual("Los Angeles", item.find("City").text)
        self.assertEqual("California", item.find("Province").text)
        self.assertEqual("USA", item.find("Country").text)
        self.assertEqual("Los Angeles;California;USA", item.find("Placeline").text)
        self.assertEqual("34.0522", item.find("Latitude").text)
        self.assertEqual("-118.2347", item.find("Longitude").text)

    def test_globenewswire(self):
        output = self.format(
            {
                "source": globenewswire.SOURCE,
                "headline": "Foo",
                "keywords": ["TSX VENTURE:AXL", "OTC:NTGSF"],
                "anpa_category": [
                    {
                        "name": globenewswire.DESCRIPTION["en"],
                        "qcode": "p",
                    }
                ],
                "subject": [
                    {"name": "FOO", "qcode": "FOO", "scheme": cp.SERVICE},
                    {"name": "BAR", "qcode": "BAR", "scheme": cp.SERVICE},
                ],
                "extra": {},
            },
            _all=True,
        )

        self.assertEqual(2, len(output))

        root = self.parse(output[0][1])
        item = root.find("ContentItem")

        self.assertEqual("Print", root.find("Services").text)
        self.assertEqual("FOO", root.find("PscCodes").text)

        self.assertEqual("Press Release", item.find("Category").text)
        self.assertEqual("Press Release", item.find("IndexCode").text)
        self.assertEqual("FOO,BAR", item.find("Note").text)
        self.assertEqual("TSX VENTURE:AXL,OTC:NTGSF", item.find("Stocks").text)
        self.assertEqual("Foo", item.find("Headline").text)
        self.assertEqual("Foo", item.find("Headline2").text)

    def test_limits(self):
        long = "foo bar {}".format("x" * 200)
        item = self.format_item(
            {
                "headline": long,
                "extra": {
                    "headline2": long,
                },
                "keywords": ["foo", "bar", long],
            }
        )

        self.assertEqual("foo bar", item.find("Headline").text)
        self.assertEqual("foo bar", item.find("Headline2").text)
        self.assertEqual("foo,bar,foo bar", item.find("Keyword").text)

    def test_picture(self):
        updates = {
            "type": "picture",
            "guid": "urn:picture",
            "urgency": 5,
            "byline": "photographer",
            "headline": "some headline",
            "slugline": "slug",
            "firstcreated": datetime(2020, 6, 3, 17, 0, 56, tzinfo=UTC),
            "extra": {
                cp.FILENAME: "NY538",
                "photographer_code": "stf",
            },
            "subject": [
                {"name": "Americas", "qcode": "A", "scheme": "photo_categories"},
            ],
            "creditline": "THE ASSOCIATED PRESS",
            "original_source": "The Associated Press",
            "copyrightnotice": "Copyright 2020 The Associated Press. All rights reserved.",
            "description_text": "Pedestrians are silhouetted",
            "renditions": {
                "original": {
                    "media": "media_id",
                    "mimetype": "image/jpeg",
                },
            },
        }
        root = self.format_item(updates, True)

        self.assertEqual("Pictures", root.find("Services").text)
        self.assertEqual("Online", root.find("PscCodes").text)

        item = root.find("ContentItem")

        self.assertEqual(updates["byline"], item.find("Byline").text)
        self.assertEqual("false", item.find("HeadlineService").text)
        self.assertEqual("A", item.find("Category").text)
        self.assertEqual("None", item.find("VideoType").text)
        self.assertEqual("None", item.find("PhotoType").text)
        self.assertEqual("None", item.find("GraphicType").text)
        self.assertEqual("News - Optional", item.find("Ranking").text)
        self.assertEqual("5", item.find("RankingValue").text)
        self.assertEqual(updates["creditline"], item.find("Credit").text)
        self.assertEqual("Photo", item.find("ContentType").text)
        self.assertEqual(updates["slugline"], item.find("SlugProper").text)
        self.assertEqual(updates["original_source"], item.find("Source").text)
        self.assertEqual(updates["extra"][cp.FILENAME], item.find("OrigTransRef").text)
        self.assertEqual("STF", item.find("BylineTitle").text)
        self.assertEqual(updates["copyrightnotice"][:50], item.find("Copyright").text)
        self.assertEqual(updates["description_text"], item.find("EnglishCaption").text)
        self.assertEqual("2020-06-03T17:00:56", item.find("DateTaken").text)

        self.assertEqual("media_id", item.find("FileName").text)
        self.assertEqual("media_id.jpg", item.find("ViewFile").text)
        self.assertEqual("media_id.jpg", item.find("ContentRef").text)
        self.assertEqual(updates["guid"], item.find("SystemSlug").text)

        self.assertEqual(1, len(item.findall("FileName")))

    def test_picture_amazon(self):
        updates = {
            "type": "picture",
            "renditions": {
                "original": {
                    "media": "20200807100836/5f2d12c8ced0b19f31ea318ajpeg.jpg",
                },
            },
        }
        item = self.format_item(updates)
        filename = updates["renditions"]["original"]["media"].replace("/", "-")
        self.assertEqual(os.path.splitext(filename)[0], item.find("FileName").text)
        self.assertEqual(filename, item.find("ViewFile").text)
        self.assertEqual(filename, item.find("ContentRef").text)

    def test_embargo(self):
        embargo = datetime(2020, 7, 22, 13, 10, 5, tzinfo=UTC)
        updates = {
            SCHEDULE_SETTINGS: {
                "utc_embargo": embargo,
            },
        }

        item = self.format_item(updates)
        self.assertEqual("2020-07-22T09:10:05", item.find("EmbargoTime").text)

        item = self.format_item({"embargoed": embargo})
        self.assertEqual("2020-07-22T09:10:05", item.find("EmbargoTime").text)

    def test_format_credit(self):
        item = self.format_item({"source": "CP", "creditline": None})
        self.assertEqual("THE CANADIAN PRESS", item.find("Credit").text)

    def test_item_with_picture(self):
        updates = {
            "source": "CP",
            "associations": {
                "gallery--1": {
                    "_id": "foo",
                    "type": "picture",
                    "guid": "foo:guid",
                    "renditions": {
                        "original": {
                            "media": "foo",
                            "mimetype": "image/jpeg",
                        },
                    },
                },
                "gallery--2": {
                    "_id": "bar",
                    "type": "picture",
                    "guid": "bar:guid",
                    "renditions": {
                        "original": {
                            "media": "bar",
                            "mimetype": "image/jpeg",
                        },
                    },
                },
                "gallery--3": {  # same picture twice
                    "_id": "bar",
                    "type": "picture",
                    "guid": "bar:guid",
                    "renditions": {
                        "original": {
                            "media": "bar",
                            "mimetype": "image/jpeg",
                        },
                    },
                },
            },
        }

        item = self.format_item(updates)

        self.assertEqual("Many", item.find("PhotoType").text)
        self.assertEqual("foo,bar", item.find("PhotoReference").text)

    def test_format_filename_rewrite(self):
        date_1am_et = datetime(2020, 8, 12, 5, tzinfo=UTC)
        date_2am_et = date_1am_et + timedelta(hours=1)
        date_3am_et = date_1am_et + timedelta(hours=2)

        resources["archive"].service.find_one.side_effect = [
            {
                "guid": "same-cycle",
                "rewrite_of": "prev-cycle",
                "firstcreated": date_2am_et,
                "unique_id": 2,
                "type": "text",
            },
            {
                "guid": "prev-cycle",
                "firstcreated": date_1am_et,
                "unique_id": 1,
                "type": "text",
            },
        ]

        item = self.format_item(
            {
                "guid": "last",
                "rewrite_of": "same-cycle",
                "extra": {},
                "firstcreated": date_3am_et,
                "type": "text",
            }
        )
        self.assertEqual("prev-cycle", item.find("FileName").text)
        self.assertEqual("prev-cycle", item.find("SystemSlug").text)

    def test_format_fr_CA(self):
        updates = {
            "language": "fr-CA",
            "anpa_category": [{"name": "National", "qcode": "g"}],
            "rewrite_sequence": 2,
            "subject": [
                {"name": "Broadcast", "qcode": cp.BROADCAST, "scheme": cp.DISTRIBUTION},
            ],
        }

        item = self.format_item(updates)

        self.assertEqual("2", item.find("Language").text)
        self.assertEqual("Nouvelles Générales", item.find("Category").text)
        self.assertEqual("Nouvelles Générales", item.find("IndexCode").text)
        self.assertEqual("Alerte", item.find("VersionType").text)
        self.assertEqual("Nouvelle - Majeur", item.find("Ranking").text)
        self.assertEqual("Radio", item.find("..").find("Services").text)

        self.assertEqual("2", item.find("WritethruValue").text)
        self.assertEqual("2ème", item.find("WritethruNum").text)
        self.assertEqual("Lead", item.find("WriteThruType").text)

    def test_correction_update(self):
        item = self.format_item(
            {
                "extra": {
                    cp.UPDATE: "update text",
                    cp.CORRECTION: "correction text",
                }
            }
        )
        self.assertEqual("update text", item.find("UpdateNote").text)
        self.assertEqual("correction text", item.find("Corrections").text)

    def test_writethru_keeps_newscompid(self):
        resources["archive"].service.find_one.side_effect = [
            {
                "guid": "same-cycle",
                "rewrite_of": "prev-cycle",
                "unique_id": 2,
                "type": "text",
            },
            {"guid": "prev-cycle", "unique_id": 1, "type": "text"},
        ]

        item = self.format_item(
            {
                "type": "text",
                "rewrite_of": "same-cycle",
                "unique_id": 3,
            }
        )

        self.assertEqual("00000001", item.find("NewsCompID").text)

    def test_picture_container_ids(self):
        resources["news"].service.get.side_effect = [
            [
                {"guid": "canceled", "pubstatus": "canceled", "type": "text"},
                {"guid": "usable", "pubstatus": "usable", "type": "text"},
                {
                    "guid": "usable2",
                    "pubstatus": "usable",
                    "type": "text",
                    "extra": {
                        cp.ORIG_ID: 32 * "a",  # slug constraints
                    },
                },
            ]
        ]

        item = self.format_item(
            {
                "type": "picture",
                "unique_id": 3,
            }
        )

        resources["news"].service.get.side_effect = None
        self.assertEqual("{}, usable".format(32 * "a"), item.find("ContainerIDs").text)

    def test_placeline_washington(self):
        item = self.format_item(
            {
                "dateline": {
                    "source": "AAP",
                    "text": "sample dateline",
                    "located": {
                        "dateline": "city",
                        "country_code": "US",
                        "tz": "America/New_York",
                        "city_code": "Washington",
                        "state_code": "DC",
                        "state": "Washington, D.C.",
                        "city": "Washington",
                        "country": "United States",
                        "code": "4140963",
                        "scheme": "geonames",
                    },
                },
            }
        )
        self.assertEqual(
            "Washington;District of Columbia;United States", item.find("Placeline").text
        )
        self.assertEqual("District of Columbia", item.find("Province").text)

    def test_format_content(self):
        item = self.format_item(
            {
                "body_html": "<p>Body HTML<br>test remove bold<b>  </b> and <b>bold1</b> and <i>idiom</i> and removed empty bold <b> </b></p>"
            }
        )
        self.assertEqual("<p>Body HTML<br />test remove bold and <strong>bold1</strong> and <em>idiom</em> and removed empty bold </p>", item.find("ContentText").text)
