"""Small, testable response and pagination contracts used by the exercises."""

from collections.abc import Callable


class DataContractError(ValueError):
    pass


def parse_items(status: int, content_type: str, payload: object) -> list[dict]:
    if status == 404:
        raise DataContractError("resource not found (404)")
    if status in (429, 503):
        raise DataContractError(f"temporary HTTP status {status}")
    if status != 200:
        raise DataContractError(f"unexpected HTTP status {status}")
    if "application/json" not in content_type.lower():
        raise DataContractError("expected JSON; received another content type")
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise DataContractError("items must be a list")
    items = payload["items"]
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            raise DataContractError("each item needs an integer id")
    return items


def collect_pages(fetch: Callable[[str | None], dict]) -> list[dict]:
    """Read pages until next is null; reject a repeated cursor and deduplicate ids."""
    cursor = None
    seen_cursors = set()
    records = {}
    while True:
        if cursor in seen_cursors:
            raise DataContractError("repeated cursor")
        seen_cursors.add(cursor)
        page = fetch(cursor)
        for item in parse_items(page["status"], page["content_type"], page["body"]):
            records[item["id"]] = item
        cursor = page["body"].get("next")
        if cursor is None:
            return list(records.values())
