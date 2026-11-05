"""Make one reproducible request to a local JSON server."""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

import requests
from common import local_server


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = parse_qs(urlsplit(self.path).query).get("page", ["1"])[0]
        body = json.dumps({"page": int(page), "items": ["one", "two"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


with local_server(Handler) as base:
    url = base + "/articles"
    with requests.Session() as session:
        response = session.get(url, params={"page": 1}, timeout=(2, 5))
        response.raise_for_status()
        payload = response.json()
        assert isinstance(payload["items"], list)
        print(response.url)
        print(payload)
