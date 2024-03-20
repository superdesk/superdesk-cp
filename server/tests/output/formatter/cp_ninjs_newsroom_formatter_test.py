import cp
import flask
import unittest

from unittest.mock import patch

from cp.output.formatter.cp_ninjs_newsroom_formatter import CPNewsroomNinjsFormatter


class TestCPNewsroomNinjsFormatter(unittest.TestCase):
    def setUp(self) -> None:
        self.formatter = CPNewsroomNinjsFormatter()
        self.app = flask.Flask(__name__)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self) -> None:
        self.ctx.pop()

    @patch("superdesk.get_resource_service")
    def test_transform_to_ninjs(self, mock_get_resource_service):
        # Create a sample article and subscriber
        article = {"ingest_id": "123", "type": "text", "auto_publish": True}
        subscriber = {
            # Add necessary fields for the test
        }

        # Call the _transform_to_ninjs method
        result = self.formatter._transform_to_ninjs(article, subscriber)

        # Assert that the result is as expected
        self.assertEqual(result["guid"], "123")

        # Add more assertions for other fields if needed

    @patch("superdesk.get_resource_service")
    def test_transform_to_ninjs_with_broadcast(self, mock_get_resource_service):
        # Create a sample article and subscriber
        article = {
            "ingest_id": "123",
            "type": "text",
            "auto_publish": True,
            "subject": [
                {"name": "Broadcast", "qcode": cp.BROADCAST, "scheme": cp.DISTRIBUTION},
            ],
        }
        subscriber = {
            # Add necessary fields for the test
        }

        # Call the _transform_to_ninjs method with is_broadcast=True
        result = self.formatter._transform_to_ninjs(article, subscriber, recursive=True)

        # Assert that the result is as expected
        self.assertEqual(result["guid"], "123-br")

    @patch("superdesk.get_resource_service")
    def test_update_ninjs_subjects_exception(self, mock_get_resource_service):
        mock_get_resource_service.side_effect = Exception("Test exception")

        ninjs = {"subject": [{"name": "test", "scheme": "subject"}]}
        with self.assertLogs(
            "cp.output.formatter.cp_ninjs_newsroom_formatter", level="ERROR"
        ) as cm:
            self.formatter.update_ninjs_subjects(ninjs, "en-CA")

        self.assertIn(
            "An error occurred. We are in CP NewsRoom Ninjs Formatter Ninjs Subjects exception:  Test exception",
            cm.output[0],
        )
