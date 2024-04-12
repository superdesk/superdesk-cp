import json
from cp.ingest.parser.cp_onclusive import CPOnclusiveFeedParser
import datetime
from dateutil.tz import tzutc
from superdesk.metadata.item import (
    ITEM_TYPE,
    CONTENT_TYPE,
    CONTENT_STATE,
)
import flask
import superdesk
from tests.ingest.parser import get_fixture_path
from tests.mock import resources
from unittest.mock import patch
from superdesk import get_resource_service
from superdesk.io.commands.update_ingest import ingest_item
from superdesk.tests import TestCase as _TestCase


with open(get_fixture_path("cp_onclusive.json", "cp_onclusive")) as fp:
    data = json.load(fp)


def qcode(subject):
    return "{}:{}".format(subject.get("scheme"), subject.get("qcode"))


class OnclusiveFeedParserTestCase(_TestCase):
    parser = CPOnclusiveFeedParser()
    provider = "Test_CP_Onclusive"

    maxDiff = None

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_content(self):
        with patch.dict(superdesk.resources, resources):
            item = self.parser.parse(data)[0]
            expected_subjects = [
                {
                    "name": "Conflict / Terrorism / Security",
                    "qcode": "133",
                    "scheme": "onclusive_categories",
                },
                {
                    "name": "UK Regional Elections",
                    "qcode": "148",
                    "scheme": "onclusive_event_types",
                },
                {
                    "name": "Testing",
                    "qcode": "149",
                    "scheme": "onclusive_event_types",
                },
                {
                    "name": "Banking",
                    "qcode": "159",
                    "scheme": "onclusive_categories",
                },
                {
                    "name": "Music Festivals",
                    "qcode": "228",
                    "scheme": "onclusive_event_types",
                },
                {
                    "name": "Testing2",
                    "qcode": "129",
                    "scheme": "onclusive_event_types",
                },
                {
                    "name": "Finance General",
                    "qcode": "35",
                    "scheme": "onclusive_categories",
                },
                {
                    "name": "Tech - Internet, software & new media",
                    "qcode": "50",
                    "scheme": "onclusive_categories",
                },
                {
                    "name": "Law & Order",
                    "qcode": "88",
                    "scheme": "onclusive_categories",
                },
                {
                    "name": "Trade Conferences",
                    "qcode": "97",
                    "scheme": "onclusive_categories",
                },
                {
                    "qcode": "Conference",
                    "scheme": "event_types",
                },
                {
                    "qcode": "Conference and trade show",
                    "scheme": "event_types",
                },
                {
                    "qcode": "Official visit",
                    "scheme": "event_types",
                },
                {
                    "qcode": "04000000",
                    "scheme": "subject_custom",
                },
                {
                    "qcode": "20000638",
                    "scheme": "subject_custom",
                },
                {
                    "qcode": "11000000",
                    "scheme": "subject_custom",
                },
            ]
            self.assertEqual(
                sorted(map(qcode, item["subject"])),
                sorted(map(qcode, expected_subjects)),
            )
            item["anpa_category"].sort(key=lambda i: i["name"])
            expected_categories = [
                {
                    "name": "National",
                    "qcode": "g",
                    "translations": {
                        "name": {
                            "en-CA": "National",
                            "fr-CA": "Nouvelles Générales",
                        }
                    },
                },
                {
                    "name": "International",
                    "qcode": "w",
                    "translations": {
                        "name": {"en-CA": "International", "fr-CA": "International"}
                    },
                },
                {
                    "name": "Business",
                    "qcode": "b",
                    "translations": {
                        "name": {"en-CA": "Business", "fr-CA": "Affaires"}
                    },
                },
            ]
            expected_categories.sort(key=lambda i: i["name"])
            self.assertEqual(item["anpa_category"], expected_categories)
            self.assertEqual(item[ITEM_TYPE], CONTENT_TYPE.EVENT)
            self.assertEqual(item["state"], CONTENT_STATE.INGESTED)

            self.assertEqual(item["occur_status"]["qcode"], "eocstat:eos5")

            self.assertIn(
                "https://www.canadianinstitute.com/anti-money-laundering-financial-crime/",
                item["links"],
            )

            self.assertEqual(
                item["dates"]["start"],
                datetime.datetime(2022, 6, 15, 0, 0, tzinfo=tzutc()),
            )
            self.assertEqual(
                item["dates"]["end"],
                datetime.datetime(2022, 6, 16, 0, 0, tzinfo=tzutc()),
            )

            self.assertEqual(
                item["name"],
                "Annual Forum on Anti-Money Laundering and Financial Crime",
            )
            self.assertEqual(item["definition_short"], "")

            self.assertEqual(
                item["location"][0]["name"],
                "One King West Hotel & Residence, 1 King St W, Toronto",
            )

    def test_item_update(self):
        # add a user
        flask.g.user = {"_id": "current_user_id"}
        event_service = get_resource_service("events")
        provider = {
            "_id": "abcd",
            "source": "sf",
            "name": "CP_Onclusive",
        }
        source = self.parser.parse(data)[0]

        # Ingest first version
        ingested, ids = ingest_item(source, provider=provider, feeding_service={})
        self.assertTrue(ingested)
        self.assertIn(source["guid"], ids)

        dest = list(
            event_service.get_from_mongo(req=None, lookup={"guid": source["guid"]})
        )[0]
        self.assertEqual(
            dest["name"], "Annual Forum on Anti-Money Laundering and Financial Crime"
        )
        self.assertEqual(dest["state"], "ingested")
        self.assertEqual(dest.get("version_creator"), None)

        event_service.patch(
            dest["_id"], {"name": "Edit event Name", "update_method": "single"}
        )
        dest = list(
            event_service.get_from_mongo(req=None, lookup={"guid": source["guid"]})
        )[0]
        self.assertEqual(dest.get("version_creator"), "current_user_id")

        # parser check version_creator, if it is there then cancel the update and return []
        source = self.parser.parse(data)
        self.assertEqual(source, [])
