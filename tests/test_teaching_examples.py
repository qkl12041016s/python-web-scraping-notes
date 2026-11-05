"""Checks for the added hands-on teaching steps and their failure cases."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(EXAMPLES))
from ch05_cursor import Handler as CursorHandler, PAGES as CURSOR_PAGES, collect  # noqa: E402
from ch06_xml import SOURCE, parse_xml  # noqa: E402
from ch17_binary import Handler as BinaryHandler, PAYLOAD, download  # noqa: E402
from common import local_server  # noqa: E402


def run_python(name, *args):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(EXAMPLES / name), *map(str, args)],
                          cwd=ROOT, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=30)


@pytest.mark.parametrize("name,expected", [
    ("ch02_payloads.py", "utf8: <p>你好，爬虫</p>"),
    ("ch06_tabular.py", "csv=2, jsonl=2, title=你好"),
    ("ch08_failure.py", "ok=3, failed=1, failed_id=2"),
    ("ch09_failures.py", "ok=1, failed=3: 429, 503, timeout"),
    ("ch17_binary.py", "verified bytes: 22528; rejected HTML"),
    ("ch18_har.py", "12:00:01Z tap list GET example.org 200 120ms"),
])
def test_supplementary_example(name, expected):
    result = run_python(name)
    assert result.returncode == 0, result.stderr
    assert expected in result.stdout


def test_http_cursor_rejects_loop():
    pages = dict(CURSOR_PAGES)
    pages["p3"] = {"items": [{"id": 4}], "next": "p2"}
    handler = type("LoopCursor", (CursorHandler,), {"pages": pages})
    with local_server(handler) as base:
        with pytest.raises(RuntimeError, match="Repeated cursor"):
            collect(base)


def test_xml_contract_rejects_wrong_type_and_missing_title():
    with pytest.raises(ValueError, match="XML response"):
        parse_xml(200, "text/html", SOURCE)
    with pytest.raises(ValueError, match="missing required"):
        parse_xml(200, "application/xml", SOURCE.replace("<title>First</title>", ""))


def test_binary_rejects_html_and_oversize_without_final_file(tmp_path):
    digest = hashlib.sha256(PAYLOAD).hexdigest()
    with local_server(BinaryHandler) as base:
        for suffix, limit in (("/not-binary", 30_000), ("/sample.bin", 100)):
            target = tmp_path / "out.bin"
            with pytest.raises(ValueError):
                download(base + suffix, target, digest, max_bytes=limit)
            assert not target.exists()
            assert not (tmp_path / "out.bin.part").exists()


def test_scrapy_follow_and_enabled_pipeline(tmp_path):
    output = tmp_path / "follow.jsonl"
    result = subprocess.run(
        [sys.executable, "-m", "scrapy", "runspider",
         str(EXAMPLES / "ch11_follow_spider.py"), "-O", str(output),
         "--loglevel", "ERROR"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=45,
    )
    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [row["title"] for row in rows] == ["First local article", "Second local article"]


def test_run_report_failure_exit_then_resume(tmp_path):
    db = tmp_path / "job.sqlite3"
    failed = run_python("ch22_run.py", "--db", db, "--simulate-failure")
    assert failed.returncode == 1
    assert json.loads(failed.stderr)["status"] == "failed"
    resumed = run_python("ch22_run.py", "--db", db, "--resume")
    assert resumed.returncode == 0, resumed.stderr
    report = json.loads(resumed.stdout)
    assert report["status"] == "ok"
    assert report["resumed"] == 1
    assert report["pages"] == 1
    assert report["unique_items"] == 3
