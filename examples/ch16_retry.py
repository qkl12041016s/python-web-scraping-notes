"""Observe bounded status retries against a local failing server."""

from http.server import BaseHTTPRequestHandler

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RetryError
from urllib3.util import Retry

from common import local_server


class Handler(BaseHTTPRequestHandler):
    attempts = {"flaky": 0, "always": 0, "post": 0}

    def do_GET(self):
        key = "flaky" if self.path == "/flaky" else "always"
        self.attempts[key] += 1
        status = 200 if key == "flaky" and self.attempts[key] >= 3 else 503
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        self.attempts["post"] += 1
        self.send_response(503)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *_args):
        pass


retry = Retry(
    total=2, connect=1, read=0, status=2,
    backoff_factor=0,
    status_forcelist=[429, 503],
    allowed_methods={"GET"},
    respect_retry_after_header=True,
)

if __name__ == "__main__":
    with local_server(Handler) as base, requests.Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=retry))
        session.get(base + "/flaky", timeout=(2, 5)).raise_for_status()
        try:
            session.get(base + "/always", timeout=(2, 5))
        except RetryError:
            pass
        else:
            raise AssertionError("An endless 503 sequence must stop")
        post = session.post(base + "/always", timeout=(2, 5))
        assert post.status_code == 503
    assert Handler.attempts == {"flaky": 3, "always": 3, "post": 1}
    print("GET success after:", Handler.attempts["flaky"])
    print("GET stopped after:", Handler.attempts["always"])
    print("POST status attempts:", Handler.attempts["post"])
