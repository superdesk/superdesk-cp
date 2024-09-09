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
