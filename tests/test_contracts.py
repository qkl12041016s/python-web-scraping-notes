"""Exercise failure cases, not just the examples' success paths."""

import pytest

from examples.validation import DataContractError, collect_pages, parse_items


@pytest.mark.parametrize("status,content_type,payload,fragment", [
    (404, "application/json", {}, "404"),
    (429, "application/json", {}, "429"),
    (503, "application/json", {}, "503"),
    (200, "text/html", "<h1>Sign in</h1>", "expected JSON"),
    (200, "application/json", {"items": "wrong"}, "must be a list"),
    (200, "application/json", {"items": [{"title": "missing id"}]}, "integer id"),
])
def test_bad_response_rejected(status, content_type, payload, fragment):
    with pytest.raises(DataContractError, match=fragment):
        parse_items(status, content_type, payload)


def test_repeated_cursor_rejected():
    def fetch(_cursor):
        return {"status": 200, "content_type": "application/json",
                "body": {"items": [{"id": 1}], "next": "again"}}

    with pytest.raises(DataContractError, match="repeated cursor"):
        collect_pages(fetch)


def test_duplicate_item_is_written_once():
    pages = {
        None: {"items": [{"id": 1}], "next": "p2"},
        "p2": {"items": [{"id": 1}, {"id": 2}], "next": None},
    }

    def fetch(cursor):
        return {"status": 200, "content_type": "application/json", "body": pages[cursor]}

    assert [row["id"] for row in collect_pages(fetch)] == [1, 2]
