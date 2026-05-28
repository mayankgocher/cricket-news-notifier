"""
Conversation History — Persistent per-session chat history using SQLite.

Stores last N turns (user + assistant) per session.
Session IDs are prefixed to avoid collisions:
  - Telegram users:  "telegram_{chat_id}"
  - Web UI users:    "ui_{session_id}"

Last 5 turns = 5 user messages + 5 assistant replies = 10 rows per session.
"""

import os
import sys
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import SQLITE_DB_PATH

_DB_PATH = SQLITE_DB_PATH

MAX_TURNS = 5  # Keep last 5 user + 5 assistant messages per session


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_table() -> None:
    """Create conversation_history table if it doesn't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                role       TEXT    NOT NULL,
                message    TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_session
            ON conversation_history (session_id, created_at)
        """)
        conn.commit()


def get_history(session_id: str) -> list[dict]:
    """
    Fetch last MAX_TURNS turns for a session.

    Returns list of dicts with 'role' and 'message', oldest first.
    Each turn = 1 user + 1 assistant row, so we fetch last MAX_TURNS*2 rows.
    """
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT role, message FROM conversation_history
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, MAX_TURNS * 2)).fetchall()

    # Reverse to get chronological order (oldest first)
    return [{"role": r["role"], "message": r["message"]} for r in reversed(rows)]


def save_turn(session_id: str, user_message: str, assistant_message: str) -> None:
    """
    Save one full turn (user + assistant) to history.
    Then prune so only last MAX_TURNS turns remain.
    """
    with _get_conn() as conn:
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO conversation_history (session_id, role, message, created_at) VALUES (?, ?, ?, ?)",
            (session_id, "user", user_message, now),
        )
        conn.execute(
            "INSERT INTO conversation_history (session_id, role, message, created_at) VALUES (?, ?, ?, ?)",
            (session_id, "assistant", assistant_message, now),
        )

        # Prune: keep only last MAX_TURNS * 2 rows for this session
        conn.execute("""
            DELETE FROM conversation_history
            WHERE session_id = ? AND id NOT IN (
                SELECT id FROM conversation_history
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            )
        """, (session_id, session_id, MAX_TURNS * 2))

        conn.commit()


def clear_history(session_id: str) -> None:
    """Clear all history for a session."""
    with _get_conn() as conn:
        conn.execute(
            "DELETE FROM conversation_history WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
