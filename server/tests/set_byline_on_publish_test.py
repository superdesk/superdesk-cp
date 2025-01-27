from cp.set_byline_on_publish import set_byline_on_publish
from unittest.mock import patch, MagicMock


def test_set_byline_on_publish():
    item = {"authors": [{"name": "John Doe"}, {"name": "Foo Bar"}]}
    updates = {}
    set_byline_on_publish(None, item, updates, foo=1)
    assert item["byline"] == "John Doe, Foo Bar"
    assert updates["byline"] == "John Doe, Foo Bar"

    item = {"authors": [{"name": "John Doe"}], "byline": "foo"}
    updates = {}
    set_byline_on_publish(None, item, updates)
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
    set_byline_on_publish(None, item, updates)
    assert item["byline"] == "foo bar"
    assert updates["byline"] == item["byline"]


def test_set_byline_on_publish_with_authors():
    item = {"authors": [{"name": "John Doe"}, {"name": "Foo Bar"}]}
    updates = {}
    set_byline_on_publish(None, item, updates)
    assert item["byline"] == "John Doe, Foo Bar"
    assert updates["byline"] == "John Doe, Foo Bar"


def test_set_byline_on_publish_with_existing_byline():
    item = {"authors": [{"name": "John Doe"}], "byline": "foo"}
    updates = {}
    set_byline_on_publish(None, item, updates)
    assert item["byline"] == "foo"
    assert "byline" not in updates


@patch("superdesk.get_resource_service")
def test_set_byline_with_no_authors(mock_get_resource_service):
    mock_user_service = MagicMock()
    mock_default_user = {
        "_id": "64d13ff3446949ccb5348bdc",
        "username": "cpdefaultauthor",
        "first_name": "Default",
        "last_name": "Author",
        "email": "default.author@example.com",
    }
    mock_user_service.find_one.return_value = mock_default_user
    mock_get_resource_service.return_value = mock_user_service

    item = {"language": "en-CA"}
    updates = {}

    set_byline_on_publish(None, item, updates)

    assert item["byline"] == "Default Author"
    assert updates["byline"] == "Default Author"


@patch("superdesk.get_resource_service")
def test_set_byline_with_missing_default_user(mock_get_resource_service):
    mock_user_service = MagicMock()
    mock_user_service.find_one.return_value = None
    mock_get_resource_service.return_value = mock_user_service

    item = {"language": "en-CA"}
    updates = {}

    try:
        set_byline_on_publish(None, item, updates)
    except ValueError as e:
        assert str(e) == "Default user 'cpdefaultauthor' not found in the database."
