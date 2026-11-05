"""Run the exact example files included in the PDF and check observable results."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
EXPECTED = {
    "ch01_links.py": "https://example.org/articles/advanced",
    "ch02_local_requests.py": "'items': ['one', 'two']",
    "ch03_cards.py": "Second article",
    "ch04_xpath.py": "('Two', '/item/2')",
    "ch05_cursor.py": "[1, 2, 3, 4]",
    "ch06_xml.py": "'title': 'Second'",
    "ch07_sqlite.py": "1\n",
    "ch08_async.py": "item-4",
    "ch09_async_http.py": "{'id': 3}",
    "ch10_browser.py": "Ready",
    "ch12_pipeline.py": "'title': 'A title'",
    "ch13_robots.py": "/private/report False",
    "ch14_diagnostics.py": "pagination: repeated cursor",
    "ch15_session.py": "401 200",
    "ch16_retry.py": "GET stopped after: 3",
    "ch17_binary.py": "verified bytes: 22528",
    "ch18_har.py": "GET example.org 200",
    "ch20_pipeline.py": "pages=2, unique_items=3",
    "ch21_queue.py": "unique items: [1, 2, 3]",
    "ch22_config.py": "has_token=False",
}


@pytest.mark.parametrize("name,expected", sorted(EXPECTED.items()))
def test_python_example(name, expected):
    env = os.environ.copy()
    env.pop("CRAWL_TOKEN", None)
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / name)], cwd=ROOT, env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert expected in result.stdout


def test_scrapy_spider(tmp_path):
    output = tmp_path / "items.jsonl"
    result = subprocess.run(
        [sys.executable, "-m", "scrapy", "runspider",
         str(EXAMPLES / "ch11_spider.py"), "-O", str(output), "--loglevel", "ERROR"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40,
    )
    assert result.returncode == 0, result.stderr
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["title"] == "Local example"


def test_ast_example():
    if shutil.which("node") is None:
        pytest.skip("Node.js is required for the optional AST chapter")
    result = subprocess.run(
        ["node", str(EXAMPLES / "ch19_ast.js")], cwd=EXAMPLES,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "const total = 14;" in result.stdout


def test_every_printed_code_reference_exists():
    import re

    for chapter in (ROOT / "chapters").glob("*.tex"):
        content = chapter.read_text(encoding="utf-8")
        for match in re.finditer(r"\\VerbatimInput\{([^}]+)\}", content):
            assert (ROOT / match.group(1)).is_file(), (chapter, match.group(1))
