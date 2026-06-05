from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path("data/study_history.db")


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                model_name TEXT NOT NULL,
                result_markdown TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_history(
    file_name: str,
    model_name: str,
    result_markdown: str,
    db_path: Path = DB_PATH,
) -> int:
    init_db(db_path)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO study_history (file_name, generated_at, model_name, result_markdown)
            VALUES (?, ?, ?, ?)
            """,
            (file_name, generated_at, model_name, result_markdown),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_history(limit: int = 20, db_path: Path = DB_PATH) -> list[dict]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, file_name, generated_at, model_name
            FROM study_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_history(history_id: int, db_path: Path = DB_PATH) -> dict | None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, file_name, generated_at, model_name, result_markdown
            FROM study_history
            WHERE id = ?
            """,
            (history_id,),
        ).fetchone()
    return dict(row) if row else None
