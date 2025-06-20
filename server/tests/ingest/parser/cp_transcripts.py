import unittest
from unittest.mock import patch

from superdesk.tests import TestCase
import superdesk

from cp.ingest import CPTranscriptsFeedParser

from tests.ingest.parser import get_fixture_path
from tests.mock import resources


provider = {}
parser = CPTranscriptsFeedParser()


class CP_Transcripts_ParseTestCase(TestCase):
    async def test_parse(self):
        with patch.dict(superdesk.resources, resources):
            items = await parser.parse(
                get_fixture_path("cp_transcripts.json", "cp_transcripts"), provider
            )

        item = items[0]
        self.assertEqual("text", item["type"])
        self.assertEqual("transcript", item["extra"]["type"])
        self.assertEqual(True, item["extra"]["publish_ingest_id_as_guid"])
        self.assertEqual(1, item["extra"]["cp_version"])
        self.assertEqual("d3c8487a-1757-4dde-8bb5-22ca166c1e67.1", item["guid"])
        self.assertEqual(1, item["version"])
        self.assertEqual("d3c8487a-1757-4dde-8bb5-22ca166c1e67.0", item["rewrite_of"])
        self.assertTrue(item["body_html"].startswith("<p>laying around"))
