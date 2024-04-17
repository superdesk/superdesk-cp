import unittest

from cp.output.formatter.ninjs_formatter_2 import NINJSFormatter_2


class TestNinjsFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = NINJSFormatter_2()

    def test_get_associations_text(self):
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

        result = self.formatter._get_associations(article, {})
        self.assertEqual(result, expected_result)
