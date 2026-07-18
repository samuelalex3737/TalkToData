from __future__ import annotations

import json
import os
import random
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "talktodata.db"
SERVERLESS_DB_PATH = Path(tempfile.gettempdir()) / "talktodata.db"
DB_PATH = Path(
    os.getenv(
        "TALKTODATA_DB_PATH",
        str(SERVERLESS_DB_PATH if os.getenv("VERCEL") else DEFAULT_DB_PATH),
    )
)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def initialize_database(force_reset: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        cur = conn.cursor()
        if force_reset:
            cur.executescript(
                """
                DROP TABLE IF EXISTS query_history;
                DROP TABLE IF EXISTS returns;
                DROP TABLE IF EXISTS order_items;
                DROP TABLE IF EXISTS orders;
                DROP TABLE IF EXISTS products;
                DROP TABLE IF EXISTS customers;
                """
            )

        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT,
                city TEXT,
                signup_date TEXT,
                is_repeat INTEGER
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date TEXT,
                total_amount REAL,
                city TEXT
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER
            );

            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                reason TEXT,
                return_date TEXT
            );

            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                mode TEXT NOT NULL,
                provider_name TEXT,
                provider_model TEXT,
                status TEXT NOT NULL,
                sql_text TEXT,
                explanation TEXT,
                answer_json TEXT,
                guardrails_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        cur.execute("SELECT COUNT(*) AS count FROM customers")
        existing_rows = cur.fetchone()["count"]
        if existing_rows:
            conn.commit()
            return

        rng = random.Random(42)
        cities = [
            "Mumbai",
            "Delhi",
            "Bengaluru",
            "Chennai",
            "Kolkata",
            "Pune",
            "Hyderabad",
        ]
        categories = [
            "Skincare",
            "Haircare",
            "Electronics",
            "Wellness",
            "Fragrance",
        ]

        for index in range(1, 61):
            cur.execute(
                "INSERT INTO customers VALUES (?,?,?,?,?)",
                (
                    index,
                    f"Customer{index}",
                    rng.choice(cities),
                    str(date(2025, 1, 1) + timedelta(days=rng.randint(0, 400))),
                    rng.choice([0, 1]),
                ),
            )

        for index in range(1, 26):
            cur.execute(
                "INSERT INTO products VALUES (?,?,?,?)",
                (
                    index,
                    f"Product{index}",
                    rng.choice(categories),
                    round(rng.uniform(199, 4999), 2),
                ),
            )

        for index in range(1, 201):
            cur.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?)",
                (
                    index,
                    rng.randint(1, 60),
                    str(date(2026, 4, 1) + timedelta(days=rng.randint(0, 70))),
                    round(rng.uniform(299, 9999), 2),
                    rng.choice(cities),
                ),
            )

        for index in range(1, 401):
            cur.execute(
                "INSERT INTO order_items VALUES (?,?,?,?)",
                (
                    index,
                    rng.randint(1, 200),
                    rng.randint(1, 25),
                    rng.randint(1, 3),
                ),
            )

        for index in range(1, 41):
            cur.execute(
                "INSERT INTO returns VALUES (?,?,?,?)",
                (
                    index,
                    rng.randint(1, 200),
                    rng.choice(["Damaged", "Wrong item", "Late", "Quality"]),
                    str(date(2026, 4, 15) + timedelta(days=rng.randint(0, 55))),
                ),
            )

        conn.commit()


def run_query(sql: str) -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [description[0] for description in (cur.description or [])]

    return {
        "columns": columns,
        "rows": [list(row) for row in rows],
        "row_count": len(rows),
    }


def explain_query(sql: str) -> tuple[bool, str]:
    try:
        with get_connection() as conn:
            conn.execute(f"EXPLAIN QUERY PLAN {sql}")
        return True, "SQL passed SQLite query-plan validation."
    except sqlite3.Error as exc:
        return False, str(exc)


def get_latest_order_date() -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT MAX(order_date) AS latest_order_date FROM orders").fetchone()
    return row["latest_order_date"]


def save_history(
    *,
    question: str,
    mode: str,
    provider_name: str | None,
    provider_model: str | None,
    status: str,
    sql_text: str | None,
    explanation: str | None,
    answer: dict[str, Any] | None,
    guardrails: dict[str, Any] | None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO query_history (
                question,
                mode,
                provider_name,
                provider_model,
                status,
                sql_text,
                explanation,
                answer_json,
                guardrails_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question,
                mode,
                provider_name,
                provider_model,
                status,
                sql_text,
                explanation,
                json.dumps(answer) if answer is not None else None,
                json.dumps(guardrails) if guardrails is not None else None,
            ),
        )
        conn.commit()


def fetch_history(limit: int = 25) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                question,
                mode,
                provider_name,
                provider_model,
                status,
                sql_text,
                explanation,
                answer_json,
                guardrails_json,
                created_at
            FROM query_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    history: list[dict[str, Any]] = []
    for row in rows:
        history.append(
            {
                "id": row["id"],
                "question": row["question"],
                "mode": row["mode"],
                "provider_name": row["provider_name"],
                "provider_model": row["provider_model"],
                "status": row["status"],
                "sql": row["sql_text"],
                "explanation": row["explanation"],
                "answer": json.loads(row["answer_json"]) if row["answer_json"] else None,
                "guardrails": json.loads(row["guardrails_json"]) if row["guardrails_json"] else None,
                "created_at": row["created_at"],
            }
        )
    return history


def fetch_cached_response(question: str, mode: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                question,
                mode,
                provider_name,
                provider_model,
                status,
                sql_text,
                explanation,
                answer_json,
                guardrails_json,
                created_at
            FROM query_history
            WHERE question = ? AND mode = ? AND status IN ('OK', 'BLOCKED')
            ORDER BY id DESC
            LIMIT 1
            """,
            (question, mode),
        ).fetchone()

    if not row:
        return None

    return {
        "id": row["id"],
        "question": row["question"],
        "mode": row["mode"],
        "provider_name": row["provider_name"],
        "provider_model": row["provider_model"],
        "status": row["status"],
        "sql": row["sql_text"],
        "explanation": row["explanation"],
        "answer": json.loads(row["answer_json"]) if row["answer_json"] else None,
        "guardrails": json.loads(row["guardrails_json"]) if row["guardrails_json"] else None,
        "created_at": row["created_at"],
    }
