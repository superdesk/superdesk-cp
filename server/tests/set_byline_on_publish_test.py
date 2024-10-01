from cp.set_byline_on_publish import set_byline_on_publish


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
