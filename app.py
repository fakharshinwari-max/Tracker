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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenditures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                expense_date TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (budget_id) REFERENCES budgets(id)
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
    rows = query_db("SELECT id, title, category, duration_minutes, activity_date, notes FROM activities ORDER BY activity_date DESC, id DESC")
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
        "INSERT INTO activities (title, category, duration_minutes, activity_date, notes) VALUES (?, ?, ?, ?, ?)",
        (title, category, duration, activity_date, notes),
        commit=True,
    )
    return jsonify({"message": "Activity added."}), 201


@app.get("/api/budgets")
def get_budgets():
    rows = query_db(
        """
        SELECT b.id, b.name, b.monthly_limit, b.month,
               COALESCE(SUM(e.amount), b.spent, 0) AS spent,
               ROUND(b.monthly_limit - COALESCE(SUM(e.amount), b.spent, 0), 2) AS remaining
        FROM budgets b
        LEFT JOIN expenditures e ON e.budget_id = b.id
        GROUP BY b.id
        ORDER BY b.month DESC, b.id DESC
        """
    )
    return jsonify([dict(r) for r in rows])


@app.post("/api/budgets")
def add_budget():
    payload = request.get_json(force=True)
    name = payload.get("name", "").strip()
    monthly_limit = float(payload.get("monthly_limit", 0))
    month = payload.get("month", "").strip()

    if not name:
        return jsonify({"error": "Budget name is required."}), 400
    if monthly_limit <= 0:
        return jsonify({"error": "Monthly limit must be greater than zero."}), 400
    if not month:
        return jsonify({"error": "Month is required."}), 400

    query_db(
        "INSERT INTO budgets (name, monthly_limit, month) VALUES (?, ?, ?)",
        (name, monthly_limit, month),
        commit=True,
    )
    return jsonify({"message": "Budget added."}), 201


@app.get("/api/expenditures")
def get_expenditures():
    rows = query_db(
        """
        SELECT e.id, e.title, e.amount, e.expense_date, e.notes, e.budget_id, b.name AS budget_name
        FROM expenditures e
        LEFT JOIN budgets b ON b.id = e.budget_id
        ORDER BY e.expense_date DESC, e.id DESC
        """
    )
    return jsonify([dict(r) for r in rows])


@app.post("/api/expenditures")
def add_expenditures():
    payload = request.get_json(force=True)
    title = payload.get("title", "").strip()
    amount = float(payload.get("amount", 0))
    budget_id = payload.get("budget_id")
    expense_date = payload.get("expense_date", str(date.today()))
    notes = payload.get("notes", "").strip()

    if not title:
        return jsonify({"error": "Expenditure title is required."}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero."}), 400

    query_db(
        "INSERT INTO expenditures (budget_id, title, amount, expense_date, notes) VALUES (?, ?, ?, ?, ?)",
        (budget_id if budget_id else None, title, amount, expense_date, notes),
        commit=True,
    )
    return jsonify({"message": "Expenditure added."}), 201


@app.get("/api/summary")
def summary():
    activity_total = query_db("SELECT COALESCE(SUM(duration_minutes), 0) AS total FROM activities")[0]["total"]
    budget_total = query_db("SELECT COALESCE(SUM(monthly_limit), 0) AS total FROM budgets")[0]["total"]
    spent_total = query_db("SELECT COALESCE(SUM(amount), 0) AS total FROM expenditures")[0]["total"]
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
    webview.create_window("Activity + Budget Tracker", app, width=1280, height=820)
    webview.start(gui="qt", debug=False)


if __name__ == "__main__":
    run_desktop()
