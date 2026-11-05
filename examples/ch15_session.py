"""Demonstrate a cookie round trip on a local server."""

from http.server import BaseHTTPRequestHandler

import requests
from common import local_server


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/start":
            self.send_response(200)
            self.send_header("Set-Cookie", "session=local-demo; HttpOnly; SameSite=Lax")
        elif self.path == "/private":
            cookie = self.headers.get("Cookie", "")
            self.send_response(200 if "session=local-demo" in cookie else 401)
        else:
            self.send_response(404)
        self.end_headers()

    def log_message(self, *_args):
        pass


with local_server(Handler) as base:
    without_session = requests.get(base + "/private", timeout=5)
    with requests.Session() as session:
        session.get(base + "/start", timeout=5).raise_for_status()
        with_session = session.get(base + "/private", timeout=5)
    print(without_session.status_code, with_session.status_code)
