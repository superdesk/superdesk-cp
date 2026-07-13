import json
from unittest.mock import patch, AsyncMock

import superdesk
from superdesk.tests import TestCase

from cp.output.formatter.ninjs_formatter_2 import NINJSFormatter_2
from tests.mock import resources, SEQUENCE_NUMBER


class TestNinjsFormatter(TestCase):
    formatter = NINJSFormatter_2()

    async def test_get_associations_text(self):
        # Test case for article type "text"
        article = {
            "type": "text",
            "associations": {
                "key1": {"_id": "value1"},
                "key2": {"_id": "value2"},
                "key3": {"_id": "value3"},
                "key4": None,
            },
        }
        expected_result = {
            "key1": {"guid": "value1"},
            "key2": {"guid": "value2"},
            "key3": {"guid": "value3"},
        }

        result = await self.formatter._get_associations(article, {})
        self.assertEqual(result, expected_result)

    @patch(
        "cp.output.formatter.ninjs_formatter_2.generate_sequence_number",
        new_callable=AsyncMock,
        return_value=SEQUENCE_NUMBER,
    )
    async def test_export_text_article(self, mock_generate_sequence_number):
        article = {
            "_id": "test-id",
            "guid": "test-guid",
            "type": "text",
            "headline": "Test headline",
            "body_html": "<p>Test body</p>",
            "language": "en-CA",
        }

        with patch.dict(superdesk.resources, resources):
            result = await self.formatter.export(article)

        self.assertIsInstance(result, str)
        parsed = json.loads(result)
        self.assertEqual(parsed["guid"], "test-guid")
        self.assertEqual(parsed["type"], "text")
        self.assertEqual(parsed["headline"], "Test headline")
        self.assertEqual(parsed["body_html"], "<p>Test body</p>")
