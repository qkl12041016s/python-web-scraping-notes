"""Collect partial success, 429, 503 and timeout from a local HTTP server."""

import asyncio
from http.server import BaseHTTPRequestHandler
from time import sleep

import aiohttp
from common import local_server


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            sleep(0.4)
        status = {"/ok": 200, "/limited": 429, "/unavailable": 503,
                  "/slow": 200}.get(self.path, 404)
        body = b'{"id": 1}' if status == 200 else b"{}"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if status == 429:
            self.send_header("Retry-After", "1")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, *_args):
        pass


async def fetch(session, base, name):
    try:
        async with session.get(base + "/" + name) as response:
            response.raise_for_status()
            return name, await response.json(), None
    except (aiohttp.ClientResponseError, asyncio.TimeoutError) as error:
        return name, None, type(error).__name__


async def run(base):
    timeout = aiohttp.ClientTimeout(total=0.2)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        names = ["ok", "limited", "unavailable", "slow"]
        return await asyncio.gather(*(fetch(session, base, name) for name in names))


if __name__ == "__main__":
    with local_server(Handler) as base_url:
        results = asyncio.run(run(base_url))
    assert results[0][1] == {"id": 1}
    assert [row[0] for row in results if row[2]] == ["limited", "unavailable", "slow"]
    print("ok=1, failed=3: 429, 503, timeout")
