"""Shared local HTTP fixture for examples that need a server."""

from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from threading import Thread


@contextmanager
def local_server(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
