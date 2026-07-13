# Bilingual Commerce Agent 🌸

An Arabic/English AI customer service agent for UAE e-commerce, built on a real perfume catalog. It understands mixed Arabic dialects (MSA, Gulf, Egyptian), searches semantically across languages, and executes real purchase/return transactions — deployed live on WhatsApp.

> Ask it "عايز اشتري عطر مرسيدس بنز" and it understands, searches, buys, and replies — in Arabic, on WhatsApp, backed by a real PostgreSQL transaction.

---

## Why this project

Most customer-service bots in the Gulf either don't handle Arabic well, or bolt English NLP onto Arabic as an afterthought. This project treats bilingual understanding as a first-class requirement: intent parsing handles dialect and code-switching, and product search uses semantic embeddings — not keyword matching — so "الايفوريا" finds "Euphoria" and "عطر مرسيدس" finds "Mercedes Benz Club Extreme."

---

## Architecture

```
WhatsApp Customer
       │
       ▼
Meta Cloud API (Webhook)
       │
       ▼
FastAPI  ──────────────────────────────────┐
       │                                    │
       ▼                                    │
┌─────────────────────────────────────┐     │
│           LangGraph Agent            │     │
│                                       │     │
│  parse_intent (LLM)                  │     │
│       │                              │     │
│       ▼                              │     │
│  retrieve_products (SQL + semantic)  │     │
│       │                              │     │
│       ▼                              │     │
│  decide_action ──┬── read ───┐       │     │
│                   │           │       │     │
│                mutate         │       │     │
│                   │           │       │     │
│                   ▼           │       │     │
│           validate_stock      │       │     │
│                   │           │       │     │
│                   ▼           │       │     │
│         execute_transaction   │       │     │
│                   │           │       │     │
│                   └───────────┴──▶ format_response (LLM)
└─────────────────────────────────────┘     │
       │                                    │
       ▼                                    │
PostgreSQL (products, orders, transactions) │
ChromaDB (semantic product search)          │
       │                                    │
       └────────────────────────────────────┘
                     │
                     ▼
              Reply sent back
              via WhatsApp API
```

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM | OpenAI (GPT-4.1-mini) |
| Semantic search | ChromaDB + OpenAI embeddings |
| Database | PostgreSQL (SQLAlchemy + Alembic migrations) |
| API | FastAPI |
| Messaging | WhatsApp Business Cloud API (Meta) |
| Containerization | Docker + Docker Compose |
| Rate limiting | SlowAPI |
| Testing | pytest |

---

## What it actually does

- **Understands mixed-language requests**: MSA, Gulf/Egyptian dialect, English, and code-switching, without hardcoded keyword rules
- **Semantic product search**: matches perfumes across transliteration variants and descriptive queries ("العطر الخشبي بتاع مرسيدس"), not just exact names
- **Executes real transactions**: row-locked, atomic purchase/return operations against PostgreSQL — no partial fulfillment if any item in a multi-item order is out of stock
- **Replies naturally in Arabic**: LLM-generated, context-aware responses suited for WhatsApp, not templated strings
- **Runs on a real WhatsApp number**: tested end-to-end with live Meta Cloud API messages

---

## Data

100 real perfumes sourced from a Fragrantica dataset (Kaggle, CC BY-NC-SA 4.0), enriched with:
- LLM-generated Arabic names and natural product descriptions
- Deterministic AED pricing and stock levels (seeded, reproducible)
- Structured fragrance notes (top/middle/base) and accords

Raw and processed data are excluded from this repo (see `.gitignore`); regenerate locally with the scripts in `scripts/`.

---

## Running locally

### Prerequisites
- Docker Desktop
- Python 3.11+
- An OpenAI API key
- A Meta WhatsApp Business API setup (for the messaging integration)

### Setup

```bash
git clone https://github.com/3mo0o0ry2001/bilingual-commerce-agent.git
cd bilingual-commerce-agent
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Create a `.env` file:
```
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://perfume_admin:dev_password_change_me@localhost:5432/perfume_agent
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_VERIFY_TOKEN=...
```

### Build the data pipeline

```bash
python scripts/build_catalog.py
python scripts/enrich_catalog.py
docker compose up -d
alembic upgrade head
python scripts/seed_database.py
python scripts/build_vector_index.py
```

### Run

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API testing.

### Test

```bash
pytest tests/ -v
```

---

## Project structure

```
app/
├── agents/          # LangGraph nodes and graph definition
├── api/             # FastAPI routes and webhook handler
├── core/            # Shared utilities (rate limiter)
├── db/              # SQLAlchemy models and database config
├── integrations/    # WhatsApp API client
└── search/          # Semantic search (ChromaDB + embeddings)

scripts/             # Data pipeline: build, enrich, seed, index
tests/                # pytest suite
alembic/              # Database migrations
```

---

## Design notes

**Why LangGraph over a single prompt.** Splitting intent parsing, retrieval, validation, and execution into separate nodes makes each step independently testable and debuggable — a failure in `validate_stock` is immediately traceable, versus a monolithic prompt where failures are opaque.

**Why semantic search, not just SQL LIKE.** Exact string matching fails on Arabic transliteration variance ("الايفوريا" vs "يوفوريا" vs "Euphoria"). Embedding both the query and product catalog into the same vector space, and combining Arabic name, English name, brand, and accords into one search document, solves this without hand-written normalization rules.

**Why row-level locking on transactions.** `SELECT ... FOR UPDATE` prevents race conditions where two concurrent purchases of the last unit in stock both succeed, leaving inventory negative — a real risk in any transactional system, not a theoretical one.

---

## License

Code in this repository is provided as-is for portfolio purposes. Perfume data is sourced under CC BY-NC-SA 4.0 and is not redistributed in this repo.
