from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from typing import Any

from .database import get_latest_order_date
from .schema import RELATIONSHIP_NOTES, SCHEMA_TEXT


DEFAULT_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "180"))


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def detect_ollama() -> dict[str, Any] | None:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        data = _get_json(f"{base_url}/api/tags")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None

    models = [model.get("name") for model in data.get("models", []) if model.get("name")]
    if not models:
        return None

    preferred_names = [
        os.getenv("OLLAMA_MODEL", "").strip(),
        "qwen2.5-coder:7b",
        "qwen2.5:7b",
        "llama3.1:8b",
        "llama3.2:latest",
        "mistral:latest",
        "deepseek-coder:6.7b",
    ]
    model = next((name for name in preferred_names if name and name in models), models[0])

    return {
        "source": "ollama",
        "name": "Ollama",
        "model": model,
        "base_url": base_url,
        "available_models": models,
    }


def detect_local_openai_compatible() -> dict[str, Any] | None:
    base_url = os.getenv("LOCAL_OPENAI_BASE_URL", "").strip().rstrip("/")
    model = os.getenv("LOCAL_OPENAI_MODEL", "").strip()
    if not base_url or not model:
        return None

    return {
        "source": "local-openai-compatible",
        "name": "Local OpenAI-Compatible Endpoint",
        "model": model,
        "base_url": base_url,
        "api_key": os.getenv("LOCAL_OPENAI_API_KEY", "").strip(),
    }


def detect_openai_cloud() -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    return {
        "source": "openai",
        "name": "OpenAI",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        "base_url": "https://api.openai.com/v1",
        "api_key": api_key,
    }


def detect_provider() -> dict[str, Any] | None:
    return detect_ollama() or detect_local_openai_compatible() or detect_openai_cloud()


def build_messages(question: str) -> list[dict[str, str]]:
    latest_order_date = get_latest_order_date()
    relationship_text = "\n".join(f"- {line}" for line in RELATIONSHIP_NOTES)

    system = (
        "You translate English business questions into ONE SQLite SQL query and one short plain-English explanation. "
        "Return strict JSON with keys sql and explanation. "
        "Only generate read-only SQL using SELECT or WITH. "
        "Never use markdown fences, comments, or multiple statements."
    )
    user = f"""
Database schema:
{SCHEMA_TEXT}

Relationship notes:
{relationship_text}

Reference date for relative time phrases:
- latest order_date in the database is {latest_order_date}

Requirements:
- Produce exactly one valid SQLite query.
- Use only tables and columns from the schema.
- If the question asks for "top" or "most", sort descending and use LIMIT 1 unless another limit is requested.
- Revenue by product or category should use SUM(order_items.quantity * products.price), not orders.total_amount.
- For repeat-customer questions, join orders to customers and filter customers.is_repeat = 1.
- When you refer to text values like city or category, preserve the capitalization shown in the data where possible.

Question:
{question}
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_repair_messages(question: str, bad_sql: str, validation_error: str) -> list[dict[str, str]]:
    latest_order_date = get_latest_order_date()
    relationship_text = "\n".join(f"- {line}" for line in RELATIONSHIP_NOTES)

    system = (
        "You repair SQLite SQL for an NL-to-SQL system. "
        "Return strict JSON with keys sql and explanation. "
        "Return exactly one complete read-only query that can run by itself. "
        "Do not return a partial CTE, multiple statements, markdown, or commentary."
    )
    user = f"""
Database schema:
{SCHEMA_TEXT}

Relationship notes:
{relationship_text}

Reference date for relative time phrases:
- latest order_date in the database is {latest_order_date}

Original question:
{question}

Previous SQL:
{bad_sql}

Validation error:
{validation_error}

Repair requirements:
- Return one complete SQLite query.
- Use only schema-valid tables and columns.
- If you use a CTE, finish with a final SELECT statement.
- Preserve the intent of the original business question.
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _parse_json_content(raw_content: str) -> dict[str, str]:
    cleaned = raw_content.strip().strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {
                "sql": cleaned.strip(),
                "explanation": "The model did not return structured JSON, so this explanation was generated as a fallback.",
            }
        data = json.loads(cleaned[start : end + 1])

    return {
        "sql": str(data.get("sql", "")).strip(),
        "explanation": str(data.get("explanation", "")).strip(),
    }


def _call_ollama(provider: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, str]:
    payload = {
        "model": provider["model"],
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0},
        "format": "json",
    }
    response = _post_json(f"{provider['base_url']}/api/chat", payload)
    content = response.get("message", {}).get("content", "")
    return _parse_json_content(content)


def _call_openai_style(provider: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, str]:
    headers = {}
    api_key = provider.get("api_key")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": provider["model"],
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    response = _post_json(f"{provider['base_url']}/chat/completions", payload, headers=headers)
    content = response["choices"][0]["message"]["content"]
    return _parse_json_content(content)


def _call_provider(provider: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, str]:
    if provider["source"] == "ollama":
        return _call_ollama(provider, messages)
    return _call_openai_style(provider, messages)


def translate_question(question: str) -> tuple[dict[str, str], dict[str, Any] | None, str | None]:
    provider = detect_provider()
    if not provider:
        return (
            {
                "sql": "",
                "explanation": (
                    "No LLM provider is currently available. Start Ollama, configure a local OpenAI-compatible "
                    "endpoint, or provide an OpenAI API key to enable Phase B and Phase C."
                ),
            },
            None,
            "No provider detected.",
        )

    messages = build_messages(question)
    try:
        result = _call_provider(provider, messages)
    except (TimeoutError, socket.timeout):
        return (
            {
                "sql": "",
                "explanation": (
                    "The detected model did not answer before the timeout window expired. "
                    "Try a simpler question, wait for the model to finish loading, or choose another provider."
                ),
            },
            provider,
            "The model timed out before returning SQL.",
        )
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as exc:
        return (
            {
                "sql": "",
                "explanation": (
                    "The provider was detected, but the request failed before a SQL response was returned."
                ),
            },
            provider,
            str(exc),
        )

    return result, provider, None


def repair_translation(
    *,
    question: str,
    bad_sql: str,
    validation_error: str,
    provider: dict[str, Any],
) -> tuple[dict[str, str], str | None]:
    messages = build_repair_messages(question, bad_sql, validation_error)
    try:
        return _call_provider(provider, messages), None
    except (TimeoutError, socket.timeout):
        return (
            {
                "sql": bad_sql,
                "explanation": "The repair attempt timed out, so the original SQL was kept for review.",
            },
            "The repair attempt timed out.",
        )
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as exc:
        return (
            {
                "sql": bad_sql,
                "explanation": "The repair attempt failed, so the original SQL was kept for review.",
            },
            str(exc),
        )
