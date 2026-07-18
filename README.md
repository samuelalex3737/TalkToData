# TalkToData

**TalkToData** is an intelligent, guarded Natural Language to SQL (NL2SQL) system. It seamlessly translates business questions in plain English into secure SQLite queries, executes them, and displays the answers—all while providing human-readable explanations and enforcing strict safety guardrails to ensure reliability.

**Live Demo:** [https://talktodata-nl2sql.vercel.app/](https://talktodata-nl2sql.vercel.app/)

## ✨ Features

- **Natural Language Queries**: Ask complex business questions in plain English and get immediate data-backed answers.
- **Strict Safety Guardrails**: Built-in protections enforce read-only execution, block destructive keywords (`DROP`, `DELETE`, `UPDATE`, etc.), and validate schema structure before execution.
- **Self-Correction**: Automatically detects incomplete or malformed LLM drafts and repairs them on the fly.
- **Multi-Provider LLM Support**: Seamlessly switch between local models (like `Ollama`), local OpenAI-compatible endpoints, and cloud APIs (OpenAI).
- **Explainable SQL**: Demystifies the generated query with a human-readable `EXPLAIN QUERY PLAN`, alongside trust notes for transparency.
- **Beautiful UI/UX**: Responsive, modern SaaS-style frontend built with React, TypeScript, and TailwindCSS featuring dark mode support.

## 🏗️ Architecture

- **Backend** (`/backend`): A robust FastAPI service handling natural language translation, query validation, and database interactions.
- **Frontend** (`/frontend`): A sleek React application offering an intuitive chat interface, query history, and system guardrail monitoring.
- **Database**: Seeded SQLite database optimized for fast queries.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend Setup

Install the required Python dependencies:
```bash
pip install fastapi "uvicorn[standard]"
```

Start the FastAPI server:
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup

Navigate to the frontend directory and install dependencies:
```bash
cd frontend
npm install
```

Start the development server:
```bash
npm run dev
```

### 3. LLM Configuration
By default, TalkToData looks for a local Ollama instance (`http://127.0.0.1:11434`).
If you prefer to use OpenAI or a local OpenAI-compatible server, create a `.env` file in the root or `backend` directory (see `.env.example`) and configure your API keys.

## 🛡️ Guardrails & Security

This system is built with trust at its core. Every query is intercepted and evaluated before touching the database:
1. Multi-statement queries are immediately blocked.
2. Destructive operations are completely rejected.
3. Referenced tables and columns are strictly validated against the actual database schema.
4. `EXPLAIN QUERY PLAN` runs first to catch deep syntax or schema discrepancies before real execution.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to fork the repository and submit a pull request.
