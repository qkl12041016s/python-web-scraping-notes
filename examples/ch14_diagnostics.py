"""Diagnose three bad responses without contacting a remote service."""

from validation import DataContractError, collect_pages, parse_items


CASES = [
    ("login page", 200, "text/html", "<h1>Sign in</h1>"),
    ("missing id", 200, "application/json", {"items": [{"title": "Only title"}]}),
]
for name, status, content_type, payload in CASES:
    try:
        parse_items(status, content_type, payload)
    except DataContractError as error:
        print(f"{name}: {error}")


def repeated_page(_cursor):
    return {"status": 200, "content_type": "application/json",
            "body": {"items": [{"id": 1}], "next": "same"}}


try:
    collect_pages(repeated_page)
except DataContractError as error:
    print(f"pagination: {error}")
