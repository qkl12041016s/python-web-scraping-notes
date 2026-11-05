"""Local two-page crawl with validation, durable storage and page checkpoints."""

from contextlib import closing
from http.server import BaseHTTPRequestHandler
import os
from pathlib import Path
import sqlite3
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from common import local_server


PAGES = {
    "/page/1": '''<article data-id="1"><h2>First</h2><a href="/item/1">Open</a></article>
    <article data-id="2"><h2>Second</h2><a href="/item/2">Open</a></article>
    <a rel="next" href="/page/2">Next</a>''',
    "/page/2": '''<article data-id="2"><h2>Second</h2><a href="/item/2">Open</a></article>
    <article data-id="3"><h2>Third</h2><a href="/item/3">Open</a></article>''',
}


class Handler(BaseHTTPRequestHandler):
    pages = PAGES

    def do_GET(self):
        body = self.pages.get(urlsplit(self.path).path)
        if body is None:
            self.send_error(404)
            return
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_args):
        pass


def allowed_url(url: str, base: str) -> str:
    candidate, origin = urlsplit(url), urlsplit(base)
    candidate_origin = (candidate.scheme, candidate.hostname, candidate.port)
    expected_origin = (origin.scheme, origin.hostname, origin.port)
    if candidate.scheme not in {"http", "https"} or candidate_origin != expected_origin:
        raise ValueError("URL leaves the allowed origin")
    if candidate.username or candidate.password:
        raise ValueError("Credentials must not appear in a URL")
    return url


def get_page(session, url: str, base: str, report: dict):
    """Check each redirect before following it; never request a foreign origin."""
    for hop in range(4):
        allowed_url(url, base)
        response = session.get(url, allow_redirects=False, timeout=(2, 5))
        report["requests"] += 1
        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location", "").strip()
            response.close()
            if not location or hop == 3:
                raise ValueError("Redirect is missing or exceeds three hops")
            url = allowed_url(urljoin(url, location), base)
            continue
        try:
            response.raise_for_status()
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                raise ValueError("Expected an HTML page")
            return response
        except Exception:
            response.close()
            raise
    raise AssertionError("unreachable")


def parse_page(source: str, page_url: str, base: str):
    soup = BeautifulSoup(source, "html.parser")
    cards = soup.select("article")
    if not cards:
        raise ValueError("No article cards: check for a login or error page")
    records = []
    for card in cards:
        item_id = card.get("data-id", "").strip()
        title_node = card.select_one("h2")
        link_node = card.select_one("a[href]")
        title = title_node.get_text(" ", strip=True) if title_node else ""
        raw_href = link_node.get("href", "").strip() if link_node else ""
        if not item_id or not title or not raw_href:
            raise ValueError("Article id, title and raw href must be nonblank")
        target = allowed_url(urljoin(page_url, raw_href), base)
        if not urlsplit(target).path.startswith("/item/"):
            raise ValueError("Detail URL must start with /item/")
        records.append((item_id, title, target))
    next_node = soup.select_one("a[rel=next]")
    next_path = None
    if next_node is not None:
        raw_next = next_node.get("href", "").strip()
        if not raw_next:
            raise ValueError("Next-page href must be nonblank")
        target = allowed_url(urljoin(page_url, raw_next), base)
        split = urlsplit(target)
        if not split.path.startswith("/page/"):
            raise ValueError("Next page must stay under /page/")
        next_path = split.path + ("?" + split.query if split.query else "")
    return records, next_path


def crawl(base: str, db_path: Path, *, resume=False, stop_after=None) -> dict:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"requests": 0, "pages": 0, "resumed": 0, "records_seen": 0}
    with closing(sqlite3.connect(db_path)) as db, requests.Session() as session:
        db.execute("""CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY CHECK (length(trim(item_id)) > 0),
            title TEXT NOT NULL CHECK (length(trim(title)) > 0),
            url TEXT NOT NULL CHECK (length(trim(url)) > 0)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS checkpoints (
            page_path TEXT PRIMARY KEY, next_path TEXT
        )""")
        page_path, visited = "/page/1", set()
        while page_path is not None:
            if len(visited) >= 100:
                raise ValueError("Page limit reached before a stop signal")
            if page_path in visited:
                raise ValueError("Repeated page: pagination did not advance")
            visited.add(page_path)
            if resume:
                row = db.execute(
                    "SELECT next_path FROM checkpoints WHERE page_path=?", (page_path,)
                ).fetchone()
                if row is not None:
                    report["resumed"] += 1
                    page_path = row[0]
                    continue
            page_url = allowed_url(urljoin(base, page_path), base)
            with get_page(session, page_url, base, report) as response:
                records, next_path = parse_page(response.text, response.url, base)
            if next_path in visited:
                raise ValueError("Repeated page: pagination did not advance")
            with db:  # Data and checkpoint commit together; exceptions roll both back.
                db.executemany("""INSERT INTO items VALUES (?, ?, ?)
                    ON CONFLICT(item_id) DO UPDATE SET
                    title=excluded.title, url=excluded.url""", records)
                db.execute("""INSERT INTO checkpoints VALUES (?, ?)
                    ON CONFLICT(page_path) DO UPDATE SET next_path=excluded.next_path""",
                    (page_path, next_path))
            report["pages"] += 1
            report["records_seen"] += len(records)
            if stop_after is not None and report["pages"] >= stop_after:
                raise InterruptedError("Stopped after a committed page for resume test")
            page_path = next_path
        report["rows"] = db.execute(
            "SELECT item_id, title, url FROM items ORDER BY item_id"
        ).fetchall()
        report["unique_items"] = len(report["rows"])
        return report


if __name__ == "__main__":
    db_file = Path(os.getenv("CH20_DB", "build/ch20_articles.sqlite3"))
    with local_server(Handler) as base_url:
        result = crawl(base_url, db_file, resume=os.getenv("CH20_RESUME") == "1")
    assert [(row[0], row[1], urlsplit(row[2]).path) for row in result["rows"]] == [
        ("1", "First", "/item/1"),
        ("2", "Second", "/item/2"),
        ("3", "Third", "/item/3"),
    ]
    print(f"pages={result['pages']}, unique_items={result['unique_items']}")
    print(f"requests={result['requests']}, seen={result['records_seen']}, "
          f"resumed={result['resumed']}")
