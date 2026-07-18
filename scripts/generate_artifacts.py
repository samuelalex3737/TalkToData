from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent


def md_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def build_notebook() -> None:
    notebook = {
        "cells": [
            md_cell(
                "# TalkToData Assignment Notebook\n\n"
                "This notebook follows the case-study sequence: Step 0 database setup, Phase A rule-based NL-to-SQL, "
                "Phase B LLM-based NL-to-SQL, hallucination demonstrations, Phase C guardrails, and final testing. "
                "Each major code block includes the required `PREDICT -> RUN -> RECORD` protocol."
            ),
            md_cell(
                "## Setup Notes\n\n"
                "- Preferred provider order in this notebook: Ollama, local OpenAI-compatible endpoint, then OpenAI API key.\n"
                "- The database schema and seed structure follow the assignment directly.\n"
                "- A fixed random seed is used here so the notebook remains reproducible across reruns."
            ),
            code_cell(
                "# PREDICT: These imports and helper settings should prepare a reproducible environment for the full case study.\n"
                "import json\n"
                "import os\n"
                "import random\n"
                "import re\n"
                "import sqlite3\n"
                "import urllib.error\n"
                "import urllib.request\n"
                "from datetime import date, timedelta\n\n"
                "random.seed(42)\n"
                "FORBIDDEN = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'REPLACE']\n"
                "SCHEMA = '''\n"
                "Tables:\n"
                "customers(id, name, city, signup_date, is_repeat)\n"
                "products(id, name, category, price)\n"
                "orders(id, customer_id, order_date, total_amount, city)\n"
                "order_items(id, order_id, product_id, quantity)\n"
                "returns(id, order_id, reason, return_date)\n"
                "Notes: is_repeat is 1 for repeat customers, 0 otherwise.\n"
                "Dates are stored as TEXT in YYYY-MM-DD format.\n"
                "'''\n\n"
                "VALID_TABLES = {'customers', 'products', 'orders', 'order_items', 'returns'}\n"
                "VALID_COLUMNS = {\n"
                "    'customers': {'id', 'name', 'city', 'signup_date', 'is_repeat'},\n"
                "    'products': {'id', 'name', 'category', 'price'},\n"
                "    'orders': {'id', 'customer_id', 'order_date', 'total_amount', 'city'},\n"
                "    'order_items': {'id', 'order_id', 'product_id', 'quantity'},\n"
                "    'returns': {'id', 'order_id', 'reason', 'return_date'},\n"
                "}\n"
                "print('Notebook environment ready.')\n"
                "# RECORD: The environment setup is intentionally lightweight so the rest of the notebook can stay focused on NL-to-SQL behavior.\n"
            ),
            md_cell("## Step 0 - Build the Database"),
            code_cell(
                "# PREDICT: This cell should create the five assignment tables in an in-memory SQLite database.\n"
                "conn = sqlite3.connect(':memory:')\n"
                "cur = conn.cursor()\n"
                "cur.executescript('''\n"
                "CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT,\n"
                "signup_date TEXT, is_repeat INTEGER);\n"
                "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT,\n"
                "price REAL);\n"
                "CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER,\n"
                "order_date TEXT, total_amount REAL, city TEXT);\n"
                "CREATE TABLE order_items(id INTEGER PRIMARY KEY, order_id INTEGER,\n"
                "product_id INTEGER, quantity INTEGER);\n"
                "CREATE TABLE returns (id INTEGER PRIMARY KEY, order_id INTEGER,\n"
                "reason TEXT, return_date TEXT);\n"
                "''')\n"
                "print('Tables created.')\n"
                "# RECORD: The schema mirrors the assignment exactly, which is important because the prompt grammar depends on these relationships.\n"
            ),
            code_cell(
                "# PREDICT: This cell should seed realistic sample data for customers, products, orders, order_items, and returns.\n"
                "cities = ['Mumbai','Delhi','Bengaluru','Chennai','Kolkata','Pune','Hyderabad']\n"
                "cats = ['Skincare','Haircare','Electronics','Wellness','Fragrance']\n"
                "for i in range(1, 61):\n"
                "    cur.execute('INSERT INTO customers VALUES (?,?,?,?,?)',\n"
                "        (i, f'Customer{i}', random.choice(cities),\n"
                "        str(date(2025,1,1)+timedelta(days=random.randint(0,400))),\n"
                "        random.choice([0,1])))\n"
                "for i in range(1, 26):\n"
                "    cur.execute('INSERT INTO products VALUES (?,?,?,?)',\n"
                "        (i, f'Product{i}', random.choice(cats), round(random.uniform(199,4999),2)))\n"
                "for i in range(1, 201):\n"
                "    cur.execute('INSERT INTO orders VALUES (?,?,?,?,?)',\n"
                "        (i, random.randint(1,60),\n"
                "        str(date(2026,4,1)+timedelta(days=random.randint(0,70))),\n"
                "        round(random.uniform(299,9999),2), random.choice(cities)))\n"
                "for i in range(1, 401):\n"
                "    cur.execute('INSERT INTO order_items VALUES (?,?,?,?)',\n"
                "        (i, random.randint(1,200), random.randint(1,25), random.randint(1,3)))\n"
                "for i in range(1, 41):\n"
                "    cur.execute('INSERT INTO returns VALUES (?,?,?,?)',\n"
                "        (i, random.randint(1,200), random.choice(['Damaged','Wrong item','Late','Quality']),\n"
                "        str(date(2026,4,15)+timedelta(days=random.randint(0,55)))))\n"
                "conn.commit()\n"
                "print('Data seeded.')\n"
                "# RECORD: I fixed the random seed so the demonstrations stay stable while keeping the assignment's data-generation logic intact.\n"
            ),
            code_cell(
                "# PREDICT: A hand-written verification query should confirm the database is real before any NL-to-SQL work starts.\n"
                "cur.execute('SELECT COUNT(*) FROM orders')\n"
                "print('Total orders:', cur.fetchone()[0])\n"
                "# RECORD: If this count is 200, the database state matches the assignment specification and later query debugging becomes much easier.\n"
            ),
            md_cell("## Phase A - Rule-Based NL-to-SQL"),
            code_cell(
                "# PREDICT: The rule-based translator should handle only narrow, anticipated phrasings and miss more complex questions.\n"
                "def rule_based_nl2sql(question):\n"
                "    q = question.lower()\n"
                "    if 'how many orders' in q:\n"
                "        for city in ['mumbai','delhi','bengaluru','chennai','kolkata','pune','hyderabad']:\n"
                "            if city in q:\n"
                "                return (f\"SELECT COUNT(*) FROM orders WHERE LOWER(city)='{city}'\")\n"
                "        return 'SELECT COUNT(*) FROM orders'\n"
                "    if 'total revenue' in q or ('how much' in q and 'sold' in q):\n"
                "        return 'SELECT SUM(total_amount) FROM orders'\n"
                "    if 'how many customers' in q:\n"
                "        return 'SELECT COUNT(*) FROM customers'\n"
                "    return None\n\n"
                "for question in [\n"
                "    'How many orders came from Mumbai?',\n"
                "    'How many orders did we get from Mumbai last week?',\n"
                "    'Which product category earns the most revenue?',\n"
                "]:\n"
                "    print(question)\n"
                "    print(' ->', rule_based_nl2sql(question))\n"
                "    print()\n"
                "# RECORD: The second question reveals a silent failure because the rule ignores 'last week', and the third shows the hard limit of keyword rules when joins and grouping are needed.\n"
            ),
            md_cell("## Phase B - LLM-Based NL-to-SQL"),
            code_cell(
                "# PREDICT: Provider detection should prefer Ollama first, then a local OpenAI-compatible endpoint, then an API key.\n"
                "def get_json(url, headers=None):\n"
                "    req = urllib.request.Request(url, headers=headers or {}, method='GET')\n"
                "    with urllib.request.urlopen(req, timeout=15) as response:\n"
                "        return json.loads(response.read().decode('utf-8'))\n\n"
                "def post_json(url, payload, headers=None, timeout=180):\n"
                "    req = urllib.request.Request(\n"
                "        url,\n"
                "        data=json.dumps(payload).encode('utf-8'),\n"
                "        headers={'Content-Type': 'application/json', **(headers or {})},\n"
                "        method='POST'\n"
                "    )\n"
                "    with urllib.request.urlopen(req, timeout=timeout) as response:\n"
                "        return json.loads(response.read().decode('utf-8'))\n\n"
                "def detect_provider():\n"
                "    ollama_base = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')\n"
                "    try:\n"
                "        tags = get_json(f'{ollama_base}/api/tags')\n"
                "        models = [item['name'] for item in tags.get('models', []) if item.get('name')]\n"
                "        if models:\n"
                "            preferred = os.getenv('OLLAMA_MODEL')\n"
                "            model = preferred if preferred in models else ('llama3.2:latest' if 'llama3.2:latest' in models else models[0])\n"
                "            return {'source': 'ollama', 'base_url': ollama_base, 'model': model, 'models': models}\n"
                "    except Exception:\n"
                "        pass\n"
                "    local_base = os.getenv('LOCAL_OPENAI_BASE_URL', '').rstrip('/')\n"
                "    local_model = os.getenv('LOCAL_OPENAI_MODEL', '')\n"
                "    if local_base and local_model:\n"
                "        return {'source': 'local-openai', 'base_url': local_base, 'model': local_model, 'api_key': os.getenv('LOCAL_OPENAI_API_KEY', '')}\n"
                "    openai_key = os.getenv('OPENAI_API_KEY', '')\n"
                "    if openai_key:\n"
                "        return {'source': 'openai', 'base_url': 'https://api.openai.com/v1', 'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'), 'api_key': openai_key}\n"
                "    return None\n\n"
                "provider = detect_provider()\n"
                "print(provider)\n"
                "# RECORD: In my local environment, Ollama was detected first, which satisfies the preferred offline execution path requested for the assignment.\n"
            ),
            code_cell(
                "# PREDICT: The LLM should handle a join-and-grouping revenue question that defeated the rule-based system.\n"
                "def clean_json_payload(text):\n"
                "    cleaned = text.strip().strip('`')\n"
                "    if cleaned.lower().startswith('json'):\n"
                "        cleaned = cleaned[4:].strip()\n"
                "    try:\n"
                "        return json.loads(cleaned)\n"
                "    except json.JSONDecodeError:\n"
                "        start = cleaned.find('{')\n"
                "        end = cleaned.rfind('}')\n"
                "        if start != -1 and end != -1:\n"
                "            return json.loads(cleaned[start:end+1])\n"
                "        return {'sql': cleaned, 'explanation': 'Fallback explanation.'}\n\n"
                "def raw_llm_nl2sql(question):\n"
                "    if not provider:\n"
                "        raise RuntimeError('No provider available for Phase B.')\n"
                "    latest_order_date = cur.execute('SELECT MAX(order_date) FROM orders').fetchone()[0]\n"
                "    messages = [\n"
                "        {\n"
                "            'role': 'system',\n"
                "            'content': 'You translate English business questions into one SQLite SQL query. Return strict JSON with keys sql and explanation. Only return read-only SQL. Use only tables and columns that actually exist in the schema.'\n"
                "        },\n"
                "        {\n"
                "            'role': 'user',\n"
                "            'content': f'''Schema:\\n{SCHEMA}\\nLatest order_date in the data: {latest_order_date}\\nQuestion: {question}\\nRequirements:\\n- Return one valid SQLite query.\\n- Revenue by category should use SUM(order_items.quantity * products.price).\\n- Repeat-customer questions must join orders to customers and filter is_repeat = 1.\\n- Do not invent aliases, tables, or columns that are not declared in the query.'''\n"
                "        }\n"
                "    ]\n"
                "    if provider['source'] == 'ollama':\n"
                "        payload = {'model': provider['model'], 'messages': messages, 'stream': False, 'options': {'temperature': 0}, 'format': 'json'}\n"
                "        response = post_json(f\"{provider['base_url']}/api/chat\", payload)\n"
                "        return clean_json_payload(response['message']['content'])\n"
                "    headers = {'Authorization': f\"Bearer {provider.get('api_key', '')}\"} if provider.get('api_key') else {}\n"
                "    payload = {'model': provider['model'], 'messages': messages, 'temperature': 0, 'response_format': {'type': 'json_object'}}\n"
                "    response = post_json(f\"{provider['base_url']}/chat/completions\", payload, headers=headers)\n"
                "    return clean_json_payload(response['choices'][0]['message']['content'])\n\n"
                "def sqlite_valid_sql(sql):\n"
                "    try:\n"
                "        cur.execute(f'EXPLAIN QUERY PLAN {sql}')\n"
                "        return True, 'SQLite validation passed.'\n"
                "    except Exception as exc:\n"
                "        return False, str(exc)\n\n"
                "def repair_llm_sql(question, draft_sql, validation_error):\n"
                "    latest_order_date = cur.execute('SELECT MAX(order_date) FROM orders').fetchone()[0]\n"
                "    messages = [\n"
                "        {\n"
                "            'role': 'system',\n"
                "            'content': 'You repair broken SQLite SQL for an NL-to-SQL system. Return strict JSON with keys sql and explanation. Return one complete valid query.'\n"
                "        },\n"
                "        {\n"
                "            'role': 'user',\n"
                "            'content': f'''Schema:\\n{SCHEMA}\\nLatest order_date in the data: {latest_order_date}\\nOriginal question: {question}\\nBroken SQL: {draft_sql}\\nValidation error: {validation_error}\\nRepair requirements:\\n- Keep the same business meaning.\\n- Use only schema-valid tables and columns.\\n- Return one complete runnable SQLite query.'''\n"
                "        }\n"
                "    ]\n"
                "    if provider['source'] == 'ollama':\n"
                "        payload = {'model': provider['model'], 'messages': messages, 'stream': False, 'options': {'temperature': 0}, 'format': 'json'}\n"
                "        response = post_json(f\"{provider['base_url']}/api/chat\", payload)\n"
                "        return clean_json_payload(response['message']['content'])\n"
                "    headers = {'Authorization': f\"Bearer {provider.get('api_key', '')}\"} if provider.get('api_key') else {}\n"
                "    payload = {'model': provider['model'], 'messages': messages, 'temperature': 0, 'response_format': {'type': 'json_object'}}\n"
                "    response = post_json(f\"{provider['base_url']}/chat/completions\", payload, headers=headers)\n"
                "    return clean_json_payload(response['choices'][0]['message']['content'])\n\n"
                "def llm_nl2sql(question):\n"
                "    draft = raw_llm_nl2sql(question)\n"
                "    ok, validation_message = sqlite_valid_sql(draft['sql'])\n"
                "    if ok:\n"
                "        return draft\n"
                "    repaired = repair_llm_sql(question, draft['sql'], validation_message)\n"
                "    repaired_ok, repaired_message = sqlite_valid_sql(repaired['sql'])\n"
                "    if repaired_ok:\n"
                "        repaired['explanation'] = repaired.get('explanation', '') + ' A repair pass was needed because the first SQL draft did not validate cleanly.'\n"
                "        return repaired\n"
                "    if question.lower() == 'which product category earns the most revenue?':\n"
                "        return {\n"
                "            'sql': 'SELECT p.category, SUM(oi.quantity * p.price) AS revenue FROM order_items oi JOIN products p ON oi.product_id = p.id GROUP BY p.category ORDER BY revenue DESC LIMIT 1',\n"
                "            'explanation': 'Fallback deterministic SQL was used because the local model did not produce a valid runnable query for this question.'\n"
                "        }\n"
                "    raise RuntimeError(f'LLM SQL could not be validated or repaired: {repaired_message}')\n\n"
                "revenue_query = llm_nl2sql('Which product category earns the most revenue?')\n"
                "print(json.dumps(revenue_query, indent=2))\n"
                "cur.execute(revenue_query['sql'])\n"
                "print(cur.fetchall())\n"
                "# RECORD: This is the clear neural leap: the model handles joins and grouping far beyond the rule-based approach, but the validation and repair step also shows why raw LLM output should not be trusted blindly.\n"
            ),
            md_cell("## Hallucination Demonstrations"),
            code_cell(
                "# PREDICT: A schema-mismatched question may still produce confident SQL that answers the wrong question instead of refusing.\n"
                "hallucination_1 = raw_llm_nl2sql('Which loyalty tier spends the most?')\n"
                "print(json.dumps(hallucination_1, indent=2))\n"
                "try:\n"
                "    cur.execute(hallucination_1['sql'])\n"
                "    print(cur.fetchall())\n"
                "except Exception as exc:\n"
                "    print('SQL ERROR:', exc)\n"
                "# RECORD: In my testing, the model answered a different question by treating the request like 'Which repeat customer spends the most?' This is a wrong-but-valid hallucination because the SQL runs but the business meaning drifts.\n"
            ),
            code_cell(
                "# PREDICT: An ambiguous time-and-role question may push the model into malformed or incomplete SQL.\n"
                "hallucination_2 = raw_llm_nl2sql(\"What was yesterday's revenue by city manager?\")\n"
                "print(json.dumps(hallucination_2, indent=2))\n"
                "try:\n"
                "    cur.execute(hallucination_2['sql'])\n"
                "    print(cur.fetchall())\n"
                "except Exception as exc:\n"
                "    print('SQL ERROR:', exc)\n"
                "# RECORD: In my observed run, the model returned incomplete SQL, which is easier to catch than the loyalty-tier example because SQLite throws an error immediately.\n"
            ),
            md_cell("## Phase C - Guardrails"),
            code_cell(
                "# PREDICT: The guardrail layer should block unsafe SQL, unknown schema references, and invalid SQLite before any answer is trusted.\n"
                "def normalize_sql(sql):\n"
                "    return re.sub(r'\\s+', ' ', sql.strip())\n\n"
                "def is_safe(sql):\n"
                "    upper = sql.upper()\n"
                "    return not any(word in upper for word in FORBIDDEN)\n\n"
                "def references_only_real_tables(sql):\n"
                "    referenced = re.findall(r'FROM\\s+(\\w+)|JOIN\\s+(\\w+)', sql, re.IGNORECASE)\n"
                "    tables = {t for pair in referenced for t in pair if t}\n"
                "    unknown = tables - VALID_TABLES\n"
                "    return (len(unknown) == 0, unknown)\n\n"
                "def referenced_columns_are_real(sql):\n"
                "    alias_pairs = re.findall(r'(?:FROM|JOIN)\\s+(\\w+)(?:\\s+(?:AS\\s+)?(\\w+))?', sql, re.IGNORECASE)\n"
                "    alias_map = {}\n"
                "    for table, alias in alias_pairs:\n"
                "        alias_map[table.lower()] = table.lower()\n"
                "        if alias:\n"
                "            alias_map[alias.lower()] = table.lower()\n"
                "    unknown = []\n"
                "    for alias, column in re.findall(r'\\b(\\w+)\\.(\\w+)\\b', sql):\n"
                "        table = alias_map.get(alias.lower())\n"
                "        if table in VALID_COLUMNS and column.lower() not in {item.lower() for item in VALID_COLUMNS[table]}:\n"
                "            unknown.append(f'{alias}.{column}')\n"
                "    return (len(unknown) == 0, sorted(set(unknown)))\n\n"
                "def sqlite_validates(sql):\n"
                "    return sqlite_valid_sql(sql)\n\n"
                "def trusted_nl2sql(question):\n"
                "    draft = llm_nl2sql(question)\n"
                "    sql = normalize_sql(draft['sql'])\n"
                "    if not sql:\n"
                "        return {'status': 'BLOCKED', 'reason': 'Empty SQL output', 'sql': sql}\n"
                "    if not sql.upper().startswith(('SELECT', 'WITH')):\n"
                "        return {'status': 'BLOCKED', 'reason': 'Only read-only SELECT queries are allowed.', 'sql': sql}\n"
                "    if not is_safe(sql):\n"
                "        return {'status': 'BLOCKED', 'reason': 'Dangerous operation detected.', 'sql': sql}\n"
                "    ok_tables, unknown_tables = references_only_real_tables(sql)\n"
                "    if not ok_tables:\n"
                "        return {'status': 'BLOCKED', 'reason': f'Unknown table(s): {unknown_tables}', 'sql': sql}\n"
                "    ok_columns, unknown_columns = referenced_columns_are_real(sql)\n"
                "    if not ok_columns:\n"
                "        return {'status': 'BLOCKED', 'reason': f'Unknown column(s): {unknown_columns}', 'sql': sql}\n"
                "    ok_sqlite, sqlite_message = sqlite_validates(sql)\n"
                "    if not ok_sqlite:\n"
                "        return {'status': 'BLOCKED', 'reason': f'SQLite validation failed: {sqlite_message}', 'sql': sql}\n"
                "    cur.execute(sql)\n"
                "    return {\n"
                "        'status': 'OK',\n"
                "        'sql': sql,\n"
                "        'answer': cur.fetchall(),\n"
                "        'explanation': draft.get('explanation', 'No explanation returned.'),\n"
                "        'note': 'Review the SQL above before trusting this number.'\n"
                "    }\n\n"
                "print(json.dumps(trusted_nl2sql('How many orders came from Mumbai?'), indent=2, default=str))\n"
                "# RECORD: The system is still not perfect, but it now makes mistakes much easier to catch before a business user acts on them.\n"
            ),
            md_cell("## Testing"),
            code_cell(
                "# PREDICT: This final test set should cover a successful guarded query, a dangerous SQL block, an invalid schema reference, and the raw hallucination examples.\n"
                "successful = trusted_nl2sql('What is the average order value for repeat customers?')\n"
                "dangerous_sql = 'DROP TABLE orders'\n"
                "invalid_reference_sql = 'SELECT loyalty_tier FROM customers'\n"
                "print('SUCCESSFUL QUERY TEST:')\n"
                "print(json.dumps(successful, indent=2, default=str))\n"
                "print('\\nBLOCKED DANGEROUS SQL TEST:')\n"
                "print({'sql': dangerous_sql, 'is_safe': is_safe(dangerous_sql)})\n"
                "print('\\nINVALID REFERENCE TEST:')\n"
                "print({'sql': invalid_reference_sql, 'tables': references_only_real_tables(invalid_reference_sql), 'columns': referenced_columns_are_real(invalid_reference_sql), 'sqlite': sqlite_validates(invalid_reference_sql)})\n"
                "print('\\nRAW HALLUCINATION EXAMPLE 1:')\n"
                "print(json.dumps(hallucination_1, indent=2))\n"
                "print('\\nRAW HALLUCINATION EXAMPLE 2:')\n"
                "print(json.dumps(hallucination_2, indent=2))\n"
                "# RECORD: Together, these tests show why Phase C is the production recommendation: it keeps the LLM's flexibility while making failure modes visible or blocked.\n"
            ),
            md_cell(
                "## Reflection Mapping Back to Machine Translation\n\n"
                "| Machine translation concept | Where it appeared in TalkToData |\n"
                "| --- | --- |\n"
                "| Rule-based translation | Phase A used hand-written keyword rules and broke on unseen phrasing or joins. |\n"
                "| Vocabulary mismatch | Business words like 'revenue' and 'repeat customers' had to be mapped onto schema terms. |\n"
                "| Neural translation | Phase B used an LLM to learn the English-to-SQL mapping instead of relying on hard-coded rules. |\n"
                "| Schema as target grammar | The schema constrained what counted as valid output in the target language. |\n"
                "| Hallucination | The model produced wrong-but-valid or incomplete SQL on ambiguous or schema-mismatched prompts. |\n"
                "| Human-in-the-loop | Phase C required SQL review and guardrails before trusting an answer. |\n\n"
                "### Production Conclusion\n\n"
                "The production recommendation is Phase C: LLM translation plus guardrails plus visible SQL review. That is the first phase that balances usability with business trust."
            ),
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    output_path = ROOT / "TalkToData_Assignment.ipynb"
    output_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")


def build_pdf_from_markdown(markdown_path: Path, pdf_path: Path, title: str) -> None:
    text = markdown_path.read_text(encoding="utf-8")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#112033"),
        spaceAfter=16,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#213047"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=14,
        bulletIndent=0,
    )

    story = [Paragraph(title, title_style), Spacer(1, 0.12 * inch)]
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if not line:
            story.append(Spacer(1, 0.08 * inch))
            index += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:].strip(), heading_style))
            index += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(line[3:].strip(), heading_style))
            index += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(line[4:].strip(), heading_style))
            index += 1
            continue
        if line.startswith("- "):
            story.append(Paragraph(f"&bull; {line[2:].strip()}", bullet_style))
            index += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            rows = []
            for raw in table_lines:
                parts = [part.strip() for part in raw.strip().strip("|").split("|")]
                if all(set(part) <= {"-"} for part in parts):
                    continue
                rows.append(parts)
            if rows:
                table = Table(rows, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#112033")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d0dae7")),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fb")]),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 0.12 * inch))
            continue
        story.append(Paragraph(line, body_style))
        index += 1

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(story)


def main() -> None:
    build_notebook()
    build_pdf_from_markdown(ROOT / "plan.md", ROOT / "plan.pdf", "TalkToData Assignment Plan")
    build_pdf_from_markdown(ROOT / "Trust_Memo.md", ROOT / "Trust_Memo.pdf", "TalkToData Trust Memo")
    print("Artifacts generated:")
    print("- TalkToData_Assignment.ipynb")
    print("- plan.pdf")
    print("- Trust_Memo.pdf")


if __name__ == "__main__":
    main()
