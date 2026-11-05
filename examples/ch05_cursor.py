"""Follow a cursor through a local JSON HTTP endpoint."""

from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlsplit

import requests
from common import local_server


PAGES = {
    "start": {"items": [{"id": 1}, {"id": 2}], "next": "p2"},
    "p2": {"items": [{"id": 2}, {"id": 3}], "next": "p3"},
    "p3": {"items": [{"id": 4}], "next": None},
}


class Handler(BaseHTTPRequestHandler):
    pages = PAGES

    def do_GET(self):
        cursor = parse_qs(urlsplit(self.path).query).get("cursor", ["start"])[0]
        payload = self.pages.get(cursor)
        if payload is None:
            self.send_error(404)
            return
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def collect(base: str) -> list[int]:
    cursor = "start"
    seen_cursors, records = set(), {}
    with requests.Session() as session:
        while cursor is not None:
            if cursor in seen_cursors:
                raise RuntimeError("Repeated cursor: pagination did not advance")
            seen_cursors.add(cursor)
            response = session.get(base + "/articles", params={"cursor": cursor}, timeout=5)
            response.raise_for_status()
            if "application/json" not in response.headers.get("Content-Type", ""):
                raise ValueError("Expected JSON, not an error page")
            page = response.json()
            if not isinstance(page.get("items"), list):
                raise TypeError("items must be a list")
            for item in page["items"]:
                if not isinstance(item.get("id"), int):
                    raise ValueError("Each item needs an integer id")
                records[item["id"]] = item
            cursor = page.get("next")
            if len(seen_cursors) >= 10 and cursor is not None:
                raise RuntimeError("Page limit reached")
    return sorted(records)


if __name__ == "__main__":
    with local_server(Handler) as base_url:
        result = collect(base_url)
    assert result == [1, 2, 3, 4]
    print(result)
