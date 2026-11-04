"""
SQL database (SQLite) for the chatbot.

Stores the conversations and their messages, so the chat history survives a page reload
or a restart of the container. The database file lives in a docker volume (see docker-compose.yml).

Tables:
    conversations(id, title, created_at)
    messages(id, conversation_id, role, content, sources, created_at)
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, List, Optional

SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "db", "chatbot.db"))

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id  INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
    content          TEXT    NOT NULL,
    sources          TEXT    NOT NULL DEFAULT '[]',  -- JSON list of the retrieved chunks
    created_at       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ChatDatabase:
    """Small data access layer with plain SQL on top of sqlite3."""

    def __init__(self, db_path: str = SQLITE_DB_PATH) -> None:
        self.db_path = db_path
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        # One shared connection, streamlit runs the script in several threads
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        logger.info(f"SQLite database ready at {os.path.abspath(db_path) if db_path != ':memory:' else db_path}")

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # ---------- conversations ----------

    def create_conversation(self, title: str = "New chat") -> int:
        with self._transaction() as conn:
            cur = conn.execute("INSERT INTO conversations (title, created_at) VALUES (?, ?)", (title, _now()))
            return cur.lastrowid

    def list_conversations(self) -> List[sqlite3.Row]:
        """All conversations, newest first."""
        return self._conn.execute("SELECT id, title, created_at FROM conversations ORDER BY id DESC").fetchall()

    def rename_conversation(self, conversation_id: int, title: str) -> None:
        with self._transaction() as conn:
            conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))

    def delete_conversation(self, conversation_id: int) -> None:
        """Deletes the conversation and (ON DELETE CASCADE) all its messages."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

    # ---------- messages ----------

    def add_message(self, conversation_id: int, role: str, content: str, sources: Optional[list] = None) -> int:
        with self._transaction() as conn:
            cur = conn.execute(
                "INSERT INTO messages (conversation_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, role, content, json.dumps(sources or []), _now()),
            )
            return cur.lastrowid

    def get_messages(self, conversation_id: int) -> List[dict]:
        rows = self._conn.execute(
            "SELECT id, role, content, sources, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
        return [{**dict(row), "sources": json.loads(row["sources"])} for row in rows]
