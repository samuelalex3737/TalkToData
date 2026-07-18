from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from .database import (
    fetch_cached_response,
    fetch_history,
    get_latest_order_date,
    initialize_database,
    run_query,
    save_history,
)
from .guardrails import validate_sql
from .providers import detect_provider, repair_translation, translate_question


KNOWN_CITIES = ["mumbai", "delhi", "bengaluru", "chennai", "kolkata", "pune", "hyderabad"]


def rule_based_nl2sql(question: str) -> str | None:
    q = question.lower()

    if "how many orders" in q:
        for city in KNOWN_CITIES:
            if city in q:
                return f"SELECT COUNT(*) AS order_count FROM orders WHERE LOWER(city) = '{city}'"
        return "SELECT COUNT(*) AS order_count FROM orders"

    if "total revenue" in q or ("how much" in q and "sold" in q):
        return "SELECT SUM(total_amount) AS total_revenue FROM orders"

    if "how many customers" in q:
        return "SELECT COUNT(*) AS customer_count FROM customers"

    return None


def build_explanation(question: str, sql: str, llm_explanation: str | None = None) -> str:
    if llm_explanation:
        return llm_explanation

    if "count" in sql.lower():
        return f"This query counts the records needed to answer: {question}"
    if "avg" in sql.lower():
        return f"This query calculates an average to answer: {question}"
    if "sum" in sql.lower():
        return f"This query sums revenue-related values to answer: {question}"
    return "This query retrieves the database records needed to answer the question."


def _extract_city(question: str) -> str | None:
    q = question.lower()
    return next((city for city in KNOWN_CITIES if city in q), None)


def _last_week_range() -> tuple[str, str]:
    latest_order_date = datetime.strptime(get_latest_order_date(), "%Y-%m-%d").date()
    start_date = latest_order_date - timedelta(days=6)
    return start_date.isoformat(), latest_order_date.isoformat()


def fast_path_nl2sql(question: str) -> tuple[str, str] | None:
    q = re.sub(r"\s+", " ", question.strip().lower())
    city = _extract_city(q)

    if ("how many orders" in q or "order count" in q) and city:
        if "last week" in q:
            start_date, end_date = _last_week_range()
            return (
                (
                    "SELECT COUNT(*) AS order_count "
                    "FROM orders "
                    f"WHERE city = '{city.title()}' "
                    f"AND order_date BETWEEN '{start_date}' AND '{end_date}'"
                ),
                f"This query counts orders from {city.title()} over the last seven days in the dataset.",
            )
        return (
            f"SELECT COUNT(*) AS order_count FROM orders WHERE city = '{city.title()}'",
            f"This query counts all orders whose city is {city.title()}.",
        )

    if (
        ("product category" in q or "category" in q)
        and ("most revenue" in q or "earns us the most" in q or "highest revenue" in q)
    ):
        return (
            "SELECT p.category, SUM(oi.quantity * p.price) AS total_revenue "
            "FROM order_items oi "
            "JOIN products p ON oi.product_id = p.id "
            "GROUP BY p.category "
            "ORDER BY total_revenue DESC "
            "LIMIT 1",
            "This query sums quantity times price by product category and returns the highest-revenue category.",
        )

    if "average order value" in q and "repeat customer" in q:
        return (
            "SELECT AVG(o.total_amount) AS average_order_value "
            "FROM orders o "
            "JOIN customers c ON o.customer_id = c.id "
            "WHERE c.is_repeat = 1",
            "This query joins orders to customers and averages order value only for repeat customers.",
        )

    if ("returned most often" in q or "most returned" in q) and "product" in q:
        return (
            "SELECT p.name, COUNT(r.id) AS return_count "
            "FROM returns r "
            "JOIN orders o ON r.order_id = o.id "
            "JOIN order_items oi ON o.id = oi.order_id "
            "JOIN products p ON oi.product_id = p.id "
            "GROUP BY p.name "
            "ORDER BY return_count DESC "
            "LIMIT 1",
            "This query links returns to the products in those orders and finds the product with the highest return count.",
        )

    if ("top 5 cities" in q or "top five cities" in q) and "customer" in q:
        return (
            "SELECT city, COUNT(*) AS customer_count "
            "FROM customers "
            "GROUP BY city "
            "ORDER BY customer_count DESC "
            "LIMIT 5",
            "This query counts customers by city, sorts descending, and returns the top five cities.",
        )

    return None


def build_cached_response(cached: dict[str, Any]) -> dict[str, Any]:
    mode = cached["mode"]
    provider_name = cached.get("provider_name")
    provider_model = cached.get("provider_model")
    return {
        "status": cached["status"],
        "mode": mode,
        "question": cached["question"],
        "sql": cached["sql"],
        "explanation": cached["explanation"],
        "answer": cached["answer"],
        "guardrails": cached["guardrails"],
        "provider": {
            "source": "cache",
            "name": provider_name or "Cached Response",
            "model": provider_model,
        },
        "trust_note": (
            "Served from cache to reduce latency. Review the generated SQL and explanation before trusting this answer."
            if mode == "trusted-llm"
            else "Served from cache to reduce latency."
        ),
    }


def run_fast_path(question: str, mode: str) -> dict[str, Any] | None:
    fast_translation = fast_path_nl2sql(question)
    if not fast_translation:
        return None

    sql, explanation = fast_translation
    guardrails = validate_sql(sql) if mode == "trusted-llm" else None
    if guardrails and guardrails["status"] != "SAFE":
        return None

    answer = run_query(guardrails["normalized_sql"] if guardrails else sql)
    response = {
        "status": "OK",
        "mode": mode,
        "question": question,
        "sql": guardrails["normalized_sql"] if guardrails else sql,
        "explanation": explanation,
        "answer": answer,
        "guardrails": guardrails,
        "provider": {
            "source": "deterministic-fast-path",
            "name": "Deterministic Fast Path",
            "model": None,
        },
        "trust_note": (
            "Answered through a deterministic fast path, then validated before execution."
            if mode == "trusted-llm"
            else "Answered through a deterministic fast path."
        ),
    }
    save_history(
        question=question,
        mode=mode,
        provider_name="Deterministic Fast Path",
        provider_model=None,
        status=response["status"],
        sql_text=response["sql"],
        explanation=explanation,
        answer=answer,
        guardrails=guardrails,
    )
    return response


def run_rule_based(question: str) -> dict[str, Any]:
    sql = rule_based_nl2sql(question)
    if not sql:
        response = {
            "status": "NO_MATCH",
            "mode": "rule-based",
            "question": question,
            "sql": None,
            "explanation": "The rule-based translator could not match this phrasing.",
            "answer": None,
            "guardrails": None,
            "provider": None,
            "trust_note": "Phase A is intentionally brittle and only handles a narrow set of phrases.",
        }
        save_history(
            question=question,
            mode="rule-based",
            provider_name=None,
            provider_model=None,
            status=response["status"],
            sql_text=None,
            explanation=response["explanation"],
            answer=None,
            guardrails=None,
        )
        return response

    answer = run_query(sql)
    response = {
        "status": "OK",
        "mode": "rule-based",
        "question": question,
        "sql": sql,
        "explanation": build_explanation(question, sql),
        "answer": answer,
        "guardrails": None,
        "provider": None,
        "trust_note": "Phase A is explainable, but it may ignore important details like time filters or unseen phrasing.",
    }
    save_history(
        question=question,
        mode="rule-based",
        provider_name=None,
        provider_model=None,
        status=response["status"],
        sql_text=sql,
        explanation=response["explanation"],
        answer=answer,
        guardrails=None,
    )
    return response


def run_llm(question: str, *, enforce_guardrails: bool) -> dict[str, Any]:
    mode = "trusted-llm" if enforce_guardrails else "llm"
    cached = fetch_cached_response(question, mode)
    if cached:
        return build_cached_response(cached)

    fast_response = run_fast_path(question, mode)
    if fast_response:
        return fast_response

    translation, provider, provider_error = translate_question(question)
    sql = translation["sql"]
    explanation = build_explanation(question, sql, translation.get("explanation"))
    provider_payload = provider if provider else {"name": None, "model": None, "source": None}

    if not provider or provider_error:
        response = {
            "status": "UNAVAILABLE",
            "mode": mode,
            "question": question,
            "sql": sql or None,
            "explanation": explanation,
            "answer": None,
            "guardrails": None,
            "provider": provider_payload,
            "trust_note": (
                provider_error
                if provider_error
                else "No model is available yet. Start Ollama or configure another provider to enable translation."
            ),
        }
        save_history(
            question=question,
            mode=mode,
            provider_name=provider_payload.get("name"),
            provider_model=provider_payload.get("model"),
            status=response["status"],
            sql_text=sql or None,
            explanation=explanation,
            answer=None,
            guardrails=None,
        )
        return response

    guardrails = validate_sql(sql) if enforce_guardrails else None
    if (
        enforce_guardrails
        and provider
        and sql
        and guardrails
        and guardrails["status"] != "SAFE"
        and not guardrails["dangerous_keywords"]
    ):
        repaired_translation, repair_error = repair_translation(
            question=question,
            bad_sql=sql,
            validation_error=guardrails["reason"],
            provider=provider,
        )
        repaired_sql = repaired_translation.get("sql", "").strip()
        if repaired_sql and repaired_sql != sql:
            sql = repaired_sql
            explanation = build_explanation(question, sql, repaired_translation.get("explanation") or explanation)
            guardrails = validate_sql(sql)
            if repair_error and guardrails["status"] == "SAFE":
                explanation = f"{explanation} A repair pass was needed because the first draft did not validate cleanly."

    if enforce_guardrails and guardrails and guardrails["status"] != "SAFE":
        response = {
            "status": "BLOCKED",
            "mode": mode,
            "question": question,
            "sql": guardrails["normalized_sql"],
            "explanation": explanation,
            "answer": None,
            "guardrails": guardrails,
            "provider": provider_payload,
            "trust_note": "The system blocked this SQL before execution because it did not pass the guardrails.",
        }
        save_history(
            question=question,
            mode=mode,
            provider_name=provider_payload["name"],
            provider_model=provider_payload["model"],
            status=response["status"],
            sql_text=response["sql"],
            explanation=explanation,
            answer=None,
            guardrails=guardrails,
        )
        return response

    try:
        answer = run_query(guardrails["normalized_sql"] if guardrails else sql)
        status = "OK"
        normalized_sql = guardrails["normalized_sql"] if guardrails else sql
    except Exception as exc:  # noqa: BLE001
        answer = None
        status = "ERROR"
        normalized_sql = guardrails["normalized_sql"] if guardrails else sql
        if guardrails is None:
            guardrails = {
                "status": "ERROR",
                "reason": f"SQL execution failed: {exc}",
            }
        else:
            guardrails["status"] = "ERROR"
            guardrails["reason"] = f"SQL execution failed: {exc}"

    response = {
        "status": status,
        "mode": mode,
        "question": question,
        "sql": normalized_sql,
        "explanation": explanation,
        "answer": answer,
        "guardrails": guardrails,
        "provider": provider_payload,
        "trust_note": (
            "Review the generated SQL and explanation before trusting this answer."
            if enforce_guardrails
            else "Phase B can generate strong SQL, but it may still answer the wrong question."
        ),
    }
    save_history(
        question=question,
        mode=mode,
        provider_name=provider_payload["name"],
        provider_model=provider_payload["model"],
        status=response["status"],
        sql_text=response["sql"],
        explanation=explanation,
        answer=answer,
        guardrails=guardrails,
    )
    return response


def ask_question(question: str, mode: str = "trusted-llm") -> dict[str, Any]:
    initialize_database()
    if mode == "rule-based":
        return run_rule_based(question)
    if mode == "llm":
        return run_llm(question, enforce_guardrails=False)
    return run_llm(question, enforce_guardrails=True)


def get_health() -> dict[str, Any]:
    initialize_database()
    provider = detect_provider()
    history = fetch_history(limit=5)
    return {
        "status": "ok",
        "database_ready": True,
        "provider": provider
        or {
            "source": None,
            "name": None,
            "model": None,
            "message": "No LLM provider detected yet.",
        },
        "recent_queries": len(history),
    }
