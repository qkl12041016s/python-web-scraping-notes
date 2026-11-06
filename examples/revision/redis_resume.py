"""Optional local Redis 6.2+ skeleton; run in a disposable demo directory.

Install redis-py separately. Bloom commands require server-side support.
Result storage here is shared by workers only on the same machine.
"""
import argparse
import json
import sqlite3
from pathlib import Path

import redis


STREAM, GROUP = "notes:demo:jobs", "notes-demo"


def initialize(client):
    try:
        client.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except redis.ResponseError as error:
        if "BUSYGROUP" not in str(error):
            raise


def save_and_ack(client, connection, messages):
    for message_id, fields in messages:
        # Substitute the chapter's authorized fetch-and-parse function here.
        record = {"url": fields["url"], "title": "local fixture"}
        with connection:
            connection.execute(
                "INSERT OR IGNORE INTO results(url,payload) VALUES (?,?)",
                (record["url"], json.dumps(record)),
            )
        # Commit first. Crash before ACK => replay, handled by unique key.
        client.xack(STREAM, GROUP, message_id)


def worker(client, database, consumer):
    initialize(client)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS results "
            "(url TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        cursor = "0-0"
        while True:
            reply = client.xautoclaim(
                STREAM, GROUP, consumer, 60_000,
                start_id=cursor, count=10,
            )
            cursor, recovered = reply[0], reply[1]
            save_and_ack(client, connection, recovered)
            if cursor == "0-0":
                break
        batches = client.xreadgroup(
            GROUP, consumer, {STREAM: ">"}, count=10, block=1000
        )
        for _, messages in batches:
            save_and_ack(client, connection, messages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["seed", "work"])
    parser.add_argument("--consumer", default="worker-1")
    parser.add_argument("--db", type=Path, default=Path("results.db"))
    args = parser.parse_args()
    client = redis.Redis(
        host="127.0.0.1", port=6379, decode_responses=True,
        socket_timeout=5,
    )
    initialize(client)
    if args.action == "seed":
        for url in ["fixture:1", "fixture:2", "fixture:1"]:
            client.xadd(STREAM, {"url": url})
    else:
        worker(client, args.db, args.consumer)


if __name__ == "__main__":
    main()
