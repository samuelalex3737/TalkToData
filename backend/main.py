from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import fetch_history, initialize_database
from .schema import RELATIONSHIP_NOTES, SCHEMA_MAP, SCHEMA_TEXT
from .service import ask_question, get_health

app = FastAPI(
    title="TalkToData API",
    version="1.0.0",
    description="Schema-aware NL-to-SQL backend with assignment-ready guardrails.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    mode: Literal["trusted-llm", "llm", "rule-based"] = "trusted-llm"


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
def health() -> dict:
    return get_health()


@app.get("/schema")
def schema() -> dict:
    return {
        "schema_text": SCHEMA_TEXT,
        "tables": SCHEMA_MAP,
        "relationships": RELATIONSHIP_NOTES,
    }


@app.get("/history")
def history(limit: int = 25) -> dict:
    return {"items": fetch_history(limit=limit)}


@app.post("/ask")
def ask(payload: AskRequest) -> dict:
    return ask_question(payload.question, payload.mode)


@app.get("/about")
def about() -> dict:
    return {
        "product": "TalkToData",
        "summary": "A guarded NL-to-SQL assistant that translates business questions into SQLite queries.",
        "machine_translation_mapping": {
            "rule_based_translation": "Phase A uses hand-written keyword rules.",
            "neural_translation": "Phase B uses an LLM to infer SQL from schema-aware prompts.",
            "guardrails": "Phase C blocks unsafe SQL and exposes the generated SQL for human verification.",
        },
    }
