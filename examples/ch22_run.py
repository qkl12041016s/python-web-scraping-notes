"""Emit a small JSON run report and a nonzero exit status on failure."""

import argparse
import json
from pathlib import Path
import sys

from ch20_pipeline import Handler, PAGES, crawl
from common import local_server


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("build/ch20_articles.sqlite3"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--simulate-failure", action="store_true")
    args = parser.parse_args(argv)
    handler = Handler
    if args.simulate_failure:
        handler = type("MissingSecond", (Handler,), {"pages": {"/page/1": PAGES["/page/1"]}})
    try:
        with local_server(handler) as base:
            report = crawl(base, args.db, resume=args.resume)
        if report["unique_items"] != 3:
            raise ValueError("Expected exactly three unique articles")
    except Exception as error:
        print(json.dumps({"status": "failed", "error": type(error).__name__}), file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "requests": report["requests"],
                      "pages": report["pages"], "resumed": report["resumed"],
                      "seen": report["records_seen"],
                      "unique_items": report["unique_items"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
