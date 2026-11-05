"""Download bytes into a temporary file, verify them, then publish atomically."""

import hashlib
from http.server import BaseHTTPRequestHandler
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import requests
from common import local_server


PAYLOAD = b"study-data-" * 2048


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        bad = self.path == "/not-binary"
        body = b"<h1>Login required</h1>" if bad else PAYLOAD
        self.send_response(200)
        self.send_header("Content-Type", "text/html" if bad else "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def download(url: str, target: Path, expected_sha256: str, max_bytes=30_000) -> int:
    part = target.with_name(target.name + ".part")
    digest, size = hashlib.sha256(), 0
    try:
        with requests.get(url, stream=True, timeout=(2, 5)) as response:
            response.raise_for_status()
            if response.headers.get("Content-Type", "").split(";")[0] != "application/octet-stream":
                raise ValueError("Unexpected content type; HTML is not a binary file")
            declared = int(response.headers.get("Content-Length", "0"))
            if declared > max_bytes:
                raise ValueError("Declared file size exceeds the limit")
            with part.open("wb") as output:
                for chunk in response.iter_content(chunk_size=4096):
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("Received file size exceeds the limit")
                    output.write(chunk)
                    digest.update(chunk)
        if declared and size != declared:
            raise ValueError("Incomplete download")
        if digest.hexdigest() != expected_sha256:
            raise ValueError("SHA-256 mismatch")
        os.replace(part, target)
        return size
    except Exception:
        part.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    expected = hashlib.sha256(PAYLOAD).hexdigest()
    with TemporaryDirectory() as directory, local_server(Handler) as base:
        destination = Path(directory) / "sample.bin"
        size = download(base + "/sample.bin", destination, expected)
        assert destination.read_bytes() == PAYLOAD
        try:
            download(base + "/not-binary", Path(directory) / "bad.bin", expected)
        except ValueError as error:
            assert "content type" in str(error)
        else:
            raise AssertionError("HTML response must be rejected")
        assert not (Path(directory) / "bad.bin").exists()
    print(f"verified bytes: {size}; rejected HTML")
