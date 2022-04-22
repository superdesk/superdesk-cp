import cp
import flask
import unittest
import superdesk

from unittest.mock import patch
from tests.mock import resources
from cp.macros.auto_routing import callback
from superdesk.utils import ListCursor


class AutoRoutingMacroTestCase(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)

    def test_auto_routing_matches_service_destination(self):
        item = {
            "associations": {"foo": {}},
            "body_html": "body",
            "abstract": "abstract",
            "uri": "uri",
            "slugline": "foo",
        }
        rule = {"name": "Broadcast: The Associated Press (APR)"}

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                callback(item, rule=rule)

        self.assertIn("subject", item)
        self.assertIn(
            {
                "name": "Broadcast",
                "qcode": cp.BROADCAST,
                "scheme": cp.DISTRIBUTION,
                "translations": {"name": {"en-CA": "Broadcast", "fr-CA": "Radio"}},
            },
            item["subject"],
        )
        self.assertIn(
            {
                "name": "The Associated Press",
                "qcode": "ap---",
                "scheme": cp.DESTINATIONS,
                "translations": None,
            },
            item["subject"],
        )

        self.assertEqual({"foo": None}, item["associations"])
        self.assertEqual("abstract", item["body_html"])
        self.assertFalse(item.get("abstract"))

    def test_auto_routing_not_matching_service_or_dest_logs_error(self):
        item = {"uri": "uri", "slugline": "foo"}
        rule = {"name": "Foo: Bar"}

        LOG_PREFIX = "ERROR:cp.macros.auto_routing:"

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                with self.assertLogs("cp.macros.auto_routing", "ERROR") as log:
                    callback(item, rule=rule)
                    self.assertIsNone(item.get("subject"))
                    self.assertEqual(
                        log.output,
                        [
                            "{}no item found in vocabulary distribution with name Foo".format(
                                LOG_PREFIX
                            ),
                            "{}no item found in vocabulary destinations with name Bar".format(
                                LOG_PREFIX
                            ),
                        ],
                    )

    def test_auto_previous_item_control_stop(self):
        item = {"uri": "uri", "slugline": "foo", "urgency": 5}
        _resources = {
            "archive": ArchiveMock(
                [
                    {
                        "subject": [{"qcode": "stop", "scheme": cp.AP_INGEST_CONTROL}],
                        "urgency": 3,
                    }
                ]
            )
        }
        with patch.dict(superdesk.resources, _resources):
            callback(item)
        self.assertFalse(item["auto_publish"])
        self.assertEqual(5, item["urgency"])

    def test_auto_previous_item_control_ranking(self):
        item = {"uri": "uri", "slugline": "foo", "urgency": 5}
        _resources = {
            "archive": ArchiveMock(
                [
                    {
                        "subject": [
                            {"qcode": "ranking", "scheme": cp.AP_INGEST_CONTROL}
                        ],
                        "urgency": 3,
                    }
                ]
            )
        }
        with patch.dict(superdesk.resources, _resources):
            callback(item)
        self.assertNotIn("auto_publish", item)
        self.assertEqual(3, item["urgency"])


class ArchiveServiceMock:
    def __init__(self, data):
        self.data = data

    def find(self, where, max_results):
        return self

    def sort(self, key, direction):
        return ListCursor(self.data)


class ArchiveMock:
    def __init__(self, data):
        self.service = ArchiveServiceMock(data)
