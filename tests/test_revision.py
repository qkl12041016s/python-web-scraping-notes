"""Regression checks for the specific defects found in the second review."""

from http.server import BaseHTTPRequestHandler
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from urllib.parse import urlsplit

import pytest
from lxml import html


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from ch01_links import LinkParser  # noqa: E402
from ch04_xpath import SOURCE, extract_cards  # noqa: E402
from ch20_pipeline import Handler, PAGES, crawl  # noqa: E402
from ch22_config import load_settings  # noqa: E402
from common import local_server  # noqa: E402


def test_links_deduplicate_in_first_seen_order():
    parser = LinkParser("https://example.org/list")
    parser.feed('<a href="/a#one">A</a><a href="/a#two">A again</a>'
                '<a href="/b">B</a>')
    assert parser.links == ["https://example.org/a", "https://example.org/b"]


def test_xpath_context_and_empty_cases():
    tree = html.fromstring(SOURCE)
    first = tree.xpath("//article")[0]
    assert first.xpath("//a/@href") == ["/item/1", "/item/2"]
    assert first.xpath(".//a/@href") == ["/item/1"]
    assert extract_cards("<main></main>") == []
    with pytest.raises(ValueError, match="Empty response"):
        extract_cards("")


def test_xpath_nested_text_and_multiple_classes():
    sample = '<main><article class="featured card"><h2>Hi <em>there</em></h2>' \
             '<a href="/one">Open</a></article></main>'
    assert extract_cards(sample) == [("Hi there", "/one")]


def test_sqlite_file_can_be_run_twice(tmp_path):
    db = tmp_path / "articles.sqlite3"
    env = os.environ.copy()
    env["CH07_DB"] = str(db)
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(ROOT / "examples" / "ch07_sqlite.py")],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "1"
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT article_id, title FROM articles").fetchall() == [
            ("42", "A careful title")]


def test_project_exact_rows_duplicate_and_second_run(tmp_path):
    db = tmp_path / "crawl.sqlite3"
    with local_server(Handler) as base:
        first = crawl(base, db)
        second = crawl(base, db)
    for report in (first, second):
        assert report["pages"] == 2
        assert report["records_seen"] == 4
        assert report["unique_items"] == 3
        assert [(item_id, title, urlsplit(url).path) for item_id, title, url in report["rows"]] == [
            ("1", "First", "/item/1"),
            ("2", "Second", "/item/2"),
            ("3", "Third", "/item/3"),
        ]


@pytest.mark.parametrize("before,after", [
    ("<h2>First</h2>", "<h2>   </h2>"),
    ('data-id="1"', 'data-id=""'),
    ('data-id="1"', ''),
    ('href="/item/1"', 'href=""'),
])
def test_project_rejects_blank_required_fields(tmp_path, before, after):
    pages = dict(PAGES)
    pages["/page/1"] = pages["/page/1"].replace(before, after, 1)
    case_handler = type("CaseHandler", (Handler,), {"pages": pages})
    db = tmp_path / "bad.sqlite3"
    with local_server(case_handler) as base:
        with pytest.raises(ValueError, match="nonblank"):
            crawl(base, db)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0


def test_project_rejects_failed_response_then_resumes(tmp_path):
    db = tmp_path / "resume.sqlite3"
    pages = {"/page/1": PAGES["/page/1"]}
    missing_second = type("MissingSecond", (Handler,), {"pages": pages})
    with local_server(missing_second) as base:
        with pytest.raises(Exception, match="404"):
            crawl(base, db)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 2
    with local_server(Handler) as base:
        report = crawl(base, db, resume=True)
    assert report["resumed"] == 1
    assert report["pages"] == 1
    assert report["unique_items"] == 3


def test_project_interruption_commits_page_then_resumes(tmp_path):
    db = tmp_path / "interrupt.sqlite3"
    with local_server(Handler) as base:
        with pytest.raises(InterruptedError, match="committed page"):
            crawl(base, db, stop_after=1)
        result = crawl(base, db, resume=True)
    assert result["resumed"] == 1
    assert result["pages"] == 1
    assert result["requests"] == 1
    assert result["unique_items"] == 3


def test_project_repeated_page_stops_before_second_write(tmp_path):
    pages = dict(PAGES)
    pages["/page/2"] += '<a rel="next" href="/page/1">Loop</a>'
    case_handler = type("LoopHandler", (Handler,), {"pages": pages})
    db = tmp_path / "loop.sqlite3"
    with local_server(case_handler) as base:
        with pytest.raises(ValueError, match="Repeated page"):
            crawl(base, db)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 2


def test_project_rejects_foreign_redirect_before_request(tmp_path):
    class Outside(BaseHTTPRequestHandler):
        hits = 0

        def do_GET(self):
            type(self).hits += 1
            self.send_response(200)
            self.end_headers()

        def log_message(self, *_args):
            pass

    with local_server(Outside) as foreign:
        class Redirect(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", foreign + "/page/1")
                self.end_headers()

            def log_message(self, *_args):
                pass

        with local_server(Redirect) as base:
            with pytest.raises(ValueError, match="allowed origin"):
                crawl(base, tmp_path / "redirect.sqlite3")
    assert Outside.hits == 0


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "0"])
def test_configuration_rejects_nonfinite_or_nonpositive(monkeypatch, value):
    monkeypatch.setenv("CRAWL_TIMEOUT", value)
    with pytest.raises(ValueError, match="finite and positive"):
        load_settings()


def test_ast_does_not_fold_overflow_into_shadowed_infinity():
    script = 'function compute(Infinity) { return 1e308 * 1e308; } const total = compute(1);'
    env = os.environ.copy()
    env["AST_SOURCE"] = script
    result = subprocess.run(
        ["node", str(ROOT / "examples" / "ch19_ast.js")],
        cwd=ROOT / "examples", env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "return Infinity;" not in result.stdout
    assert "1e+308 * 1e+308" in result.stdout or "1e308 * 1e308" in result.stdout
