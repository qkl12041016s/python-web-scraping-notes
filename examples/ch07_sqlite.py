"""Write to a persistent SQLite file; repeated runs update one stable row."""

from contextlib import closing
import os
from pathlib import Path
import sqlite3


DB_PATH = Path(os.getenv("CH07_DB", "build/ch07_articles.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
rows = [
    ("example.org", "42", "A careful title"),
    ("example.org", "42", "A careful title"),
]

with closing(sqlite3.connect(DB_PATH)) as db:
    db.execute("""CREATE TABLE IF NOT EXISTS articles (
        source TEXT NOT NULL,
        article_id TEXT NOT NULL,
        title TEXT NOT NULL CHECK (length(trim(title)) > 0),
        UNIQUE(source, article_id)
    )""")
    with db:  # Commit or roll back this batch; closing() closes the connection.
        db.executemany("""INSERT INTO articles VALUES (?, ?, ?)
            ON CONFLICT(source, article_id) DO UPDATE SET title=excluded.title""", rows)
    result = db.execute(
        "SELECT article_id, title FROM articles ORDER BY article_id"
    ).fetchall()
    assert result == [("42", "A careful title")]
    print(len(result))
