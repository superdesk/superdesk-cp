import json
from cp.ingest.parser.cp_onclusive import CPOnclusiveFeedParser
import datetime
from dateutil.tz import tzutc
from . import ParserTestCase
from superdesk.metadata.item import (
    ITEM_TYPE,
    CONTENT_TYPE,
    GUID_FIELD,
    CONTENT_STATE,
)
import flask
import superdesk
from tests.ingest.parser import get_fixture_path
from tests.mock import resources
from unittest.mock import patch


with open(get_fixture_path("cp_onclusive.json", "cp_onclusive")) as fp:
    data = json.load(fp)


class OnclusiveFeedParserTestCase(ParserTestCase):
    parser = CPOnclusiveFeedParser()
    provider = "Test_CP_Onclusive"
    app = flask.Flask(__name__)

    maxDiff = None

    def test_content(self):
        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                item = self.parser.parse(data)[0]
                item["subject"].sort(key=lambda i: i["name"])
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
                        "name": "Conference",
                        "qcode": "Conference",
                        "scheme": "event_types",
                        "parent": None,
                        "translations": {
                            "name": {
                                "en-CA": "Conference",
                                "fr-CA": "Conférence",
                            },
                        },
                    },
                    {
                        "name": "Trade show",
                        "qcode": "Trade show",
                        "scheme": "event_types",
                        "parent": None,
                        "translations": {
                            "name": {
                                "en-CA": "Trade show",
                                "fr-CA": "Salon professionnel"
                            }
                        },
                    },
                    {
                        "name": "Official visit",
                        "parent": "Political event",
                        "qcode": "Official visit",
                        "scheme": "event_types",
                        "translations": {
                            "name": {
                                "en-CA": "Official visit",
                                "fr-CA": "Visite officielle"
                            }
                        },
                    },
                    {
                        "name": "economy, business and finance",
                        "qcode": "04000000",
                        "scheme": "subject_custom",
                        "parent": None,
                        "iptc_subject": "04000000",
                        "ap_subject": "c8e409f8858510048872ff2260dd383e",
                        "in_jimi": True,
                        "translations": {
                            "name": {
                                "en-CA": "Business",
                                "fr-CA": "Affaires"
                            }
                        }
                    },
                    {
                        "name": "international relations",
                        "qcode": "20000638",
                        "parent": "11000000",
                        "scheme": "subject_custom",
                        "iptc_subject": "11002002",
                        "ap_subject": None,
                        "in_jimi": False,
                        "translations": {
                            "name": {
                                "en-CA": "international relations",
                                "fr-CA": "Relations internationales"
                            }
                        }
                    },
                ]
                expected_subjects.sort(key=lambda i: i["name"])
                self.assertEqual(item["subject"], expected_subjects)
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
                self.assertEqual(
                    item[GUID_FIELD], "urn:onclusive:4112034"
                )
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
