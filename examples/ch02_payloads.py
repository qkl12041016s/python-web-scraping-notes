"""Compare URL parameters, form data, JSON body, and UTF-8 bytes locally."""

from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlsplit

import requests
from common import local_server


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path == "/chinese":
            body = "<p>你好，爬虫</p>".encode("utf-8")
            content_type = "text/html"  # Deliberately omits a charset.
        else:
            body = json.dumps({"query": parse_qs(urlsplit(self.path).query)}).encode()
            content_type = "application/json"
        self.reply(body, content_type)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        body = json.dumps({"type": self.headers["Content-Type"],
                           "body": raw.decode("utf-8")}).encode()
        self.reply(body, "application/json")

    def reply(self, body, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


with local_server(Handler) as base, requests.Session() as session:
    query = session.get(base + "/search", params={"q": "中文"}, timeout=5).json()
    form = session.post(base + "/submit", data={"q": "中文"}, timeout=5).json()
    payload = session.post(base + "/submit", json={"q": "中文"}, timeout=5).json()
    chinese = session.get(base + "/chinese", timeout=5)
    text_from_bytes = chinese.content.decode("utf-8")
    chinese.encoding = "utf-8"
    assert query["query"] == {"q": ["中文"]}
    assert form["type"].startswith("application/x-www-form-urlencoded")
    assert payload["type"].startswith("application/json")
    assert text_from_bytes == chinese.text == "<p>你好，爬虫</p>"
    print("query:", query["query"])
    print("form:", form["type"].split(";")[0])
    print("json:", payload["type"])
    print("utf8:", chinese.text)
