from unittest.mock import patch, AsyncMock

from superdesk.tests.async_case import IsolatedAsyncioTestCase
from cp.set_byline_on_publish import set_byline_on_publish


class SetBylineOnPublishTestCase(IsolatedAsyncioTestCase):
    async def test_set_byline_on_publish(self):
        item = {"authors": [{"name": "John Doe"}, {"name": "Foo Bar"}]}
        updates = {}
        await set_byline_on_publish(item, updates)
        assert item["byline"] == "John Doe, Foo Bar"
        assert updates["byline"] == "John Doe, Foo Bar"

        item = {"authors": [{"name": "John Doe"}], "byline": "foo"}
        updates = {}
        await set_byline_on_publish(item, updates)
        assert item["byline"] == "foo"
        assert "byline" not in updates

        item = {
            "authors": [
                {
                    "_id": ["64d13ff3446949ccb5348bdc", "writer"],
                    "role": "writer",
                    "name": "Writer",
                    "parent": "64d13ff3446949ccb5348bdc",
                    "sub_label": "foo bar",
                }
            ]
        }

        updates = {}
        await set_byline_on_publish(item, updates)
        assert item["byline"] == "foo bar"
        assert updates["byline"] == item["byline"]

    async def test_set_byline_on_publish_with_authors(self):
        item = {"authors": [{"name": "John Doe"}, {"name": "Foo Bar"}]}
        updates = {}
        await set_byline_on_publish(item, updates)
        assert item["byline"] == "John Doe, Foo Bar"
        assert updates["byline"] == "John Doe, Foo Bar"

    async def test_set_byline_on_publish_with_existing_byline(self):
        item = {"authors": [{"name": "John Doe"}], "byline": "foo"}
        updates = {}
        await set_byline_on_publish(item, updates)
        assert item["byline"] == "foo"
        assert "byline" not in updates

    @patch("cp.set_byline_on_publish.get_resource_service")
    async def test_set_byline_with_no_authors(self, mock_get_resource_service):
        mock_user_service = AsyncMock()
        mock_default_user = {
            "_id": "64d13ff3446949ccb5348bdc",
            "username": "cpdefaultauthor",
            "first_name": "Default",
            "last_name": "Author",
            "email": "default.author@example.com",
        }
        mock_user_service.find_one_async.return_value = mock_default_user
        mock_get_resource_service.return_value = mock_user_service

        item = {"language": "en-CA"}
        updates = {}

        await set_byline_on_publish(item, updates)

        assert item["byline"] == "Default Author"
        assert updates["byline"] == "Default Author"

    @patch("cp.set_byline_on_publish.get_resource_service")
    async def test_set_byline_with_missing_default_user(
        self, mock_get_resource_service
    ):
        mock_user_service = AsyncMock()
        mock_user_service.find_one_async.return_value = None
        mock_get_resource_service.return_value = mock_user_service

        item = {"language": "en-CA"}
        updates = {}

        try:
            await set_byline_on_publish(item, updates)
        except ValueError as e:
            assert str(e) == "Default user 'cpdefaultauthor' not found in the database."

    @patch("superdesk.get_resource_service")
    async def test_set_byline_skips_default_for_non_cp_sources(
        self, mock_get_resource_service
    ):
        mock_user_service = AsyncMock()
        mock_user_service.find_one_async.return_value = {
            "_id": "64d13ff3446949ccb5348bdc",
            "username": "cpdefaultauthor",
            "first_name": "Default",
            "last_name": "Author",
            "email": "default.author@example.com",
        }
        mock_get_resource_service.return_value = mock_user_service

        item = {"language": "en-CA", "source": "Reuters"}
        updates = {}

        await set_byline_on_publish(None, item, updates)

        assert "authors" not in item
        assert "byline" not in item
        assert "byline" not in updates
