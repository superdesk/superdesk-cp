from unittest.mock import patch

from superdesk.tests import AsyncQuartTestCase

from cp.output.formatter.cp_ninjs_formatter import CPNINJSFormatter


class CPNINJSFormatterTestCase(AsyncQuartTestCase):
    @patch("superdesk.get_resource_service")
    async def test_subject_relevance(self, mock):
        item = {
            "type": "text",
            "subject": [
                {
                    "name": "Society",
                    "qcode": "eef4a135-e188-4d1f-93f1-cf7af1f594a6",
                    "source": "Semaphore",
                    "altids": {"source_name": "source_id"},
                    "scheme": "subject",
                    "original_source": "original_source_value",
                    "relevance": 54,
                    "creator": "Machine",
                },
            ],
        }
        formatter = CPNINJSFormatter()
        ninjs = await formatter._transform_to_ninjs(item, {})
        assert ninjs["subject"][0]["relevance"] == 54
        assert ninjs["subject"][0]["creator"] == "Machine"

    async def test_author_email(self):
        author_ref = {
            "name": "John Doe",
        }
        user = {"email": "john@doe.com"}
        formatter = CPNINJSFormatter()
        author = formatter._format_author(author_ref, user, job_titles_map={})
        assert author.get("email") == user["email"]
