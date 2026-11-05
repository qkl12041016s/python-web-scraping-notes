"""Summarize a sanitized, in-memory HAR-like record."""

from urllib.parse import urlsplit


HAR = {
    "log": {"entries": [
        {"startedDateTime": "2026-11-05T12:00:01Z", "time": 120,
         "_operation": "tap list",
         "request": {"method": "GET", "url": "https://example.org/api/list"},
         "response": {"status": 200}},
        {"startedDateTime": "2026-11-05T12:00:02Z", "time": 45,
         "_operation": "render image",
         "request": {"method": "GET", "url": "https://example.org/img/a.png"},
         "response": {"status": 200}},
    ]}
}

for entry in sorted(HAR["log"]["entries"], key=lambda row: row["startedDateTime"]):
    request = entry["request"]
    status = entry["response"]["status"]
    host = urlsplit(request["url"]).hostname
    print(entry["startedDateTime"], entry["_operation"],
          request["method"], host, status, f'{entry["time"]}ms')
