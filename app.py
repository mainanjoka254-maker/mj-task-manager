from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request



DB_PATH = Path(__file__).resolve().parent / "university_projects.db"
TABLE_NAME = "tasks"


PRIORITIES = [
    "Low",
    "Medium",
    "High",
]


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create table (and add priority column if older DB exists)."""
    with get_db_connection() as conn:
        # Create base table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY, "
            "name TEXT, "
            "priority TEXT NOT NULL DEFAULT 'Low'"
            ")"
        )

        # If DB was created by the older script (no priority column), add it.
        # This is safe if the column already exists.
        cols = {
            row[1] for row in conn.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()
        }
        if "priority" not in cols:
            conn.execute(
                f"ALTER TABLE {TABLE_NAME} ADD COLUMN priority TEXT NOT NULL DEFAULT 'Low'"
            )

        conn.commit()


app = Flask(__name__)


@app.get("/api/tasks")
def list_tasks():
    init_db()

    # Search + filter via query params
    query = (request.args.get("query") or "").strip()
    priority_filter = (request.args.get("priority_filter") or "").strip()

    # Normalize filter value
    if priority_filter not in PRIORITIES:
        priority_filter = ""

    where_clauses: list[str] = []
    params: list[object] = []

    if query:
        where_clauses.append("name LIKE ?")
        params.append(f"%{query}%")

    if priority_filter:
        where_clauses.append("priority = ?")
        params.append(priority_filter)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    with get_db_connection() as conn:
        rows = conn.execute(
            f"SELECT id, name, priority FROM {TABLE_NAME} {where_sql} ORDER BY id DESC",
            params,
        ).fetchall()

    return jsonify(
        {
            "items": [dict(r) for r in rows],
        }
    )


@app.post("/api/tasks")
def create_task():
    init_db()


    name = (request.form.get("name") or "").strip()
    priority = (request.form.get("priority") or "Low").strip()

    if not name:
        return jsonify({"error": "Project name cannot be empty."}), 400


    if priority not in PRIORITIES:
        priority = "Low"

    name = name[:200]

    with get_db_connection() as conn:
        cur = conn.execute(
            f"INSERT INTO {TABLE_NAME} (name, priority) VALUES (?, ?)",
            (name, priority),
        )
        conn.commit()
        new_id = cur.lastrowid

    return jsonify({"id": new_id, "name": name, "priority": priority}), 201



@app.delete("/api/tasks/<int:project_id>")
def delete_task(project_id: int):

    init_db()

    with get_db_connection() as conn:
        conn.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (project_id,))
        conn.commit()

    return jsonify({"ok": True, "deleted": project_id}), 200



if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


