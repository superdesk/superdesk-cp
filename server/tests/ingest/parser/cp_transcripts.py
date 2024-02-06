import unittest
from unittest.mock import patch

import flask
import superdesk

from cp.ingest import CPTranscriptsFeedParser

from tests.ingest.parser import get_fixture_path
from tests.mock import resources


provider = {}
parser = CPTranscriptsFeedParser()


class CP_Transcripts_ParseTestCase(unittest.TestCase):
    app = flask.Flask(__name__)

    def test_parse(self):
        with self.app.app_context(), patch.dict(superdesk.resources, resources):
            superdesk.resources["archive"].service.find_one.side_effect = [
                {"ingest_id": "d3c8487a-1757-4dde-8bb5-22ca166c1e67.0", "version": 0, "extra": {"ap_version": 999}},
            ]
            items = parser.parse(get_fixture_path("cp_transcripts.json", "cp_transcripts"), provider)
            superdesk.resources["archive"].service.find_one.side_effect = None

        item = items[0]
        self.assertEqual("text", item["type"])
        self.assertEqual("transcript", item["extra"]["type"])
        self.assertEqual(True, item["extra"]["publish_ingest_id_as_guid"])
        self.assertEqual(1, item["extra"]["cp_version"])
        self.assertEqual("d3c8487a-1757-4dde-8bb5-22ca166c1e67.1", item["guid"])
        self.assertEqual(1, item["version"])
        self.assertEqual("d3c8487a-1757-4dde-8bb5-22ca166c1e67.0", item["rewrite_of"])
        self.assertTrue(item["body_html"].startswith("<p>laying around"))
