"""Round-trip Chinese records through CSV and JSON Lines."""

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory


ROWS = [{"id": "1", "title": "你好"}, {"id": "2", "title": "第二条"}]

with TemporaryDirectory() as directory:
    csv_path = Path(directory) / "articles.csv"
    jsonl_path = Path(directory) / "articles.jsonl"
    with csv_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["id", "title"])
        writer.writeheader()
        writer.writerows(ROWS)
    with jsonl_path.open("w", encoding="utf-8") as output:
        for row in ROWS:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    with csv_path.open("r", encoding="utf-8", newline="") as source:
        csv_rows = list(csv.DictReader(source))
    with jsonl_path.open("r", encoding="utf-8") as source:
        jsonl_rows = [json.loads(line) for line in source]
    assert csv_rows == jsonl_rows == ROWS
    print("csv=2, jsonl=2, title=你好")
