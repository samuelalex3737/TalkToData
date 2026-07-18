from __future__ import annotations

import re
from typing import Any

from .database import explain_query
from .schema import SCHEMA_MAP, VALID_TABLES

FORBIDDEN = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE"]
ALLOWED_PREFIXES = ("SELECT", "WITH")

SQL_KEYWORDS = {
    "as",
    "asc",
    "avg",
    "between",
    "by",
    "case",
    "count",
    "date",
    "desc",
    "distinct",
    "from",
    "group",
    "having",
    "in",
    "is",
    "join",
    "left",
    "like",
    "limit",
    "max",
    "min",
    "not",
    "null",
    "on",
    "or",
    "order",
    "round",
    "select",
    "sum",
    "then",
    "when",
    "where",
    "with",
}


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip())


def is_read_only(sql: str) -> bool:
    normalized = normalize_sql(sql).upper()
    return normalized.startswith(ALLOWED_PREFIXES)


def has_multiple_statements(sql: str) -> bool:
    trimmed = sql.strip()
    if not trimmed:
        return False
    if ";" not in trimmed:
        return False
    return trimmed.count(";") > 1 or not trimmed.endswith(";")


def dangerous_keywords(sql: str) -> list[str]:
    upper = sql.upper()
    return [keyword for keyword in FORBIDDEN if re.search(rf"\b{keyword}\b", upper)]


def extract_cte_names(sql: str) -> set[str]:
    return {match.group(1).lower() for match in re.finditer(r"\bWITH\s+([A-Za-z_]\w*)\s+AS\b", sql, re.IGNORECASE)}


def extract_table_aliases(sql: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    pattern = re.compile(
        r"\b(?:FROM|JOIN)\s+([A-Za-z_]\w*)(?:\s+(?:AS\s+)?([A-Za-z_]\w*))?",
        re.IGNORECASE,
    )
    for match in pattern.finditer(sql):
        table = match.group(1)
        alias = match.group(2)
        if alias:
            aliases[alias.lower()] = table.lower()
        aliases[table.lower()] = table.lower()
    return aliases


def validate_tables(sql: str) -> dict[str, Any]:
    cte_names = extract_cte_names(sql)
    aliases = extract_table_aliases(sql)
    referenced_tables = {table for table in aliases.values() if table not in cte_names}
    unknown = sorted(table for table in referenced_tables if table not in VALID_TABLES)
    return {
        "ok": not unknown,
        "referenced_tables": sorted(referenced_tables),
        "unknown_tables": unknown,
    }


def validate_columns(sql: str) -> dict[str, Any]:
    aliases = extract_table_aliases(sql)
    unknown_columns: list[str] = []

    for alias, column in re.findall(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b", sql):
        alias_key = alias.lower()
        column_key = column.lower()
        table = aliases.get(alias_key)
        if table in SCHEMA_MAP and column_key not in {value.lower() for value in SCHEMA_MAP[table]}:
            unknown_columns.append(f"{alias}.{column}")

    return {
        "ok": not unknown_columns,
        "unknown_columns": sorted(set(unknown_columns)),
    }


def validate_sql(sql: str) -> dict[str, Any]:
    normalized = normalize_sql(sql)
    keyword_hits = dangerous_keywords(normalized)
    table_validation = validate_tables(normalized)
    column_validation = validate_columns(normalized)
    explain_ok, explain_message = explain_query(normalized)

    if not normalized:
        status = "BLOCKED"
        reason = "The model returned an empty SQL query."
    elif not is_read_only(normalized):
        status = "BLOCKED"
        reason = "Only read-only SELECT queries are allowed."
    elif has_multiple_statements(normalized):
        status = "BLOCKED"
        reason = "Only a single SQL statement is allowed."
    elif keyword_hits:
        status = "BLOCKED"
        reason = f"Dangerous SQL keyword detected: {', '.join(keyword_hits)}"
    elif not table_validation["ok"]:
        status = "BLOCKED"
        reason = f"Unknown table(s): {', '.join(table_validation['unknown_tables'])}"
    elif not column_validation["ok"]:
        status = "BLOCKED"
        reason = f"Unknown column reference(s): {', '.join(column_validation['unknown_columns'])}"
    elif not explain_ok:
        status = "BLOCKED"
        reason = f"SQLite validation failed: {explain_message}"
    else:
        status = "SAFE"
        reason = "SQL passed all guardrail checks."

    return {
        "status": status,
        "reason": reason,
        "read_only": is_read_only(normalized) if normalized else False,
        "dangerous_keywords": keyword_hits,
        "table_validation": table_validation,
        "column_validation": column_validation,
        "sqlite_validation": {
            "ok": explain_ok,
            "message": explain_message,
        },
        "normalized_sql": normalized,
    }
