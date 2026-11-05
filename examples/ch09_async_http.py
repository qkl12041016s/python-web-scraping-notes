"""Fetch three JSON responses asynchronously from a local server."""

import asyncio
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit

import aiohttp
from common import local_server


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        item_id = int(urlsplit(self.path).path.rsplit("/", 1)[-1])
        body = json.dumps({"id": item_id}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


async def fetch(session, limit, base, item_id):
    async with limit:
        async with session.get(f"{base}/item/{item_id}") as response:
            response.raise_for_status()
            return await response.json()


async def run(base):
    timeout = aiohttp.ClientTimeout(total=5)
    limit = asyncio.Semaphore(2)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [fetch(session, limit, base, i) for i in (1, 2, 3)]
        return await asyncio.gather(*tasks)


with local_server(Handler) as base:
    result = asyncio.run(run(base))
    assert [row["id"] for row in result] == [1, 2, 3]
    print(result)
