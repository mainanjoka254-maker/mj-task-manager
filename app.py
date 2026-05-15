from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, redirect, render_template, request

app = Flask(__name__)

DB_PATH = Path(__file__).resolve().parent / "university_projects.db"
TABLE_NAME = "tasks"  # tasks(id INTEGER PRIMARY KEY, name TEXT)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY, "
            "name TEXT"
            ")"
        )
        conn.commit()


def fetch_projects():
    with get_db_connection() as conn:
        return conn.execute(
            f"SELECT id, name FROM {TABLE_NAME} ORDER BY id DESC"
        ).fetchall()


# 1) Root route returns your home page
@app.route('/')
def index():
    init_db()
    projects = fetch_projects()
    return render_template('index.html', projects=projects, message=None)


# 2) /tasks allows both GET and POST
@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    init_db()

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if name:
            name = name[:200]
            with get_db_connection() as conn:
                conn.execute(
                    f"INSERT INTO {TABLE_NAME} (name) VALUES (?)",
                    (name,),
                )
                conn.commit()
        return redirect('/')

    # GET just shows the same home page
    projects = fetch_projects()
    return render_template('index.html', projects=projects, message=None)


if __name__ == '__main__':
    app.run(debug=True)




