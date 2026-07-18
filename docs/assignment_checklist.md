# TalkToData Running Checklist

## Assignment Requirements Extracted from the Case Study

- Answer all five comprehension checkpoints in my own words.
- Produce a one-page solution plan with the five-question mapping table, phase predictions, and a production recommendation.
- Build a working notebook that follows the `Predict -> Run -> Record` protocol for every code cell in the build phases.
- Include Step 0 database creation, data seeding, and verification queries in the notebook.
- Implement Phase A rule-based NL-to-SQL.
- Implement Phase B LLM-based NL-to-SQL with schema-aware prompting.
- Demonstrate hallucinations, including wrong-but-valid SQL behavior and observations across multiple runs.
- Implement Phase C guardrails:
  - Block destructive SQL.
  - Validate references against the schema.
  - Always show generated SQL for human review.
- Ship a working UI where a non-technical user can ask a question and see the answer plus generated SQL.
- Produce a trust memo addressed to the CEO.
- Map the final system back to machine translation concepts.

## Expanded Build Scope Requested by the User

- Use a professional FastAPI backend.
- Build a modern React + TypeScript + Tailwind interface with a SaaS-quality design.
- Prefer Ollama first, then a local OpenAI-compatible endpoint, then an API key.
- Detect available local models automatically.
- Add stronger SQL safety validation for destructive keywords.
- Add schema validation for both tables and columns.
- Add a plain-English SQL explanation.
- Add a human review layer with SQL, explanation, result, and trust warning.
- Include query history, guardrail status, and an about page in the UI.
- Generate `README.md`, `plan.md`, `plan.pdf`, `Trust_Memo.md`, `Trust_Memo.pdf`, and `TalkToData_Assignment.ipynb`.
- Create a final submission checklist that maps every assignment requirement to its implementation.

## Progress Tracker

- [x] Read the assignment document fully.
- [x] Extract the professor's requirements and deliverables.
- [x] Draft the written assignment plan (`plan.md`).
- [x] Generate `plan.pdf`.
- [x] Build the backend and database layer.
- [x] Implement provider detection and NL-to-SQL translation flow.
- [x] Implement guardrails and SQL explanation.
- [x] Build the professional frontend.
- [x] Generate the notebook deliverable.
- [x] Write the trust memo and generate its PDF.
- [x] Write the README with requirement mapping.
- [x] Run build and verification checks.
- [x] Produce the final submission checklist.
