from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
import webview

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "portable_data"
DB_PATH = DATA_DIR / "tracker.db"


def ensure_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                activity_date TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                spent REAL NOT NULL DEFAULT 0,
                month TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def query_db(sql: str, params: tuple[Any, ...] = (), commit: bool = False) -> list[sqlite3.Row]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql, params)
        if commit:
            conn.commit()
        return cursor.fetchall()


app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/activities")
def get_activities():
    rows = query_db(
        """
        SELECT id, title, category, duration_minutes, activity_date, notes
        FROM activities
        ORDER BY activity_date DESC, id DESC
        """
    )
    return jsonify([dict(r) for r in rows])


@app.post("/api/activities")
def add_activity():
    payload = request.get_json(force=True)
    title = payload.get("title", "").strip()
    category = payload.get("category", "General").strip() or "General"
    duration = int(payload.get("duration_minutes", 0))
    activity_date = payload.get("activity_date", str(date.today()))
    notes = payload.get("notes", "").strip()

    if not title:
        return jsonify({"error": "Title is required."}), 400
    if duration <= 0:
        return jsonify({"error": "Duration must be greater than zero."}), 400

    query_db(
        """
        INSERT INTO activities (title, category, duration_minutes, activity_date, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, category, duration, activity_date, notes),
        commit=True,
    )
    return jsonify({"message": "Activity added."}), 201


@app.get("/api/budgets")
def get_budgets():
    rows = query_db(
        """
        SELECT id, name, monthly_limit, spent, month,
               ROUND(monthly_limit - spent, 2) AS remaining
        FROM budgets
        ORDER BY month DESC, id DESC
        """
    )
    return jsonify([dict(r) for r in rows])


@app.post("/api/budgets")
def add_budget():
    payload = request.get_json(force=True)
    name = payload.get("name", "").strip()
    monthly_limit = float(payload.get("monthly_limit", 0))
    spent = float(payload.get("spent", 0))
    month = payload.get("month", "").strip()

    if not name:
        return jsonify({"error": "Budget name is required."}), 400
    if monthly_limit <= 0:
        return jsonify({"error": "Monthly limit must be greater than zero."}), 400
    if not month:
        return jsonify({"error": "Month is required."}), 400

    query_db(
        """
        INSERT INTO budgets (name, monthly_limit, spent, month)
        VALUES (?, ?, ?, ?)
        """,
        (name, monthly_limit, spent, month),
        commit=True,
    )
    return jsonify({"message": "Budget added."}), 201


@app.get("/api/summary")
def summary():
    activity_total = query_db("SELECT COALESCE(SUM(duration_minutes), 0) AS total FROM activities")[0]["total"]
    budget_total = query_db("SELECT COALESCE(SUM(monthly_limit), 0) AS total FROM budgets")[0]["total"]
    spent_total = query_db("SELECT COALESCE(SUM(spent), 0) AS total FROM budgets")[0]["total"]
    return jsonify(
        {
            "total_activity_minutes": activity_total,
            "total_budget_limit": round(float(budget_total), 2),
            "total_budget_spent": round(float(spent_total), 2),
            "total_budget_remaining": round(float(budget_total - spent_total), 2),
            "database_path": str(DB_PATH),
        }
    )


def run_desktop() -> None:
    ensure_database()
    window = webview.create_window("Activity + Budget Tracker", app, width=1200, height=780)
    webview.start(gui="qt", debug=False)


if __name__ == "__main__":
    run_desktop()
