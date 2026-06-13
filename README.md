# News Hub

Personal RSS news aggregator that organises articles by semantic **topics** rather than chronology — your second brain for news.

**Stack:** React + FastAPI + PostgreSQL/pgvector + OpenAI embeddings + Claude LLM

---

## Quick start

### 1. Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- OpenAI API key (for embeddings)
- Anthropic API key (for topic names & summaries)

### 2. Start the database

```bash
docker compose up -d
```

PostgreSQL with pgvector runs on `localhost:5432`.

### 3. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — fill in OPENAI_API_KEY and ANTHROPIC_API_KEY

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## How it works

```
RSS feeds → poll (APScheduler, hourly) → store articles
        → embed (OpenAI text-embedding-3-small)
        → cluster (HDBSCAN, automatic K)
        → name topics (Claude)
        → track trends (weekly windows)
        → build graph (cosine similarity between topic centroids)
```

### Pages

| Page | Description |
|------|-------------|
| **Digest** | Adaptive summary — top topics by unread count with LLM-generated paragraph summaries. Pick 1 day / week / month window. |
| **Topics** | Full topic list. Click a topic to read its articles in a side panel with a trend sparkline. |
| **Graph** | Force-directed knowledge map. Nodes = topics, edges = semantic similarity. Click a node to open its articles. |
| **Sources** | Manage RSS feeds. Add, pause, delete, or trigger a manual poll. |

### Philosophy (from spec)

- **Pull, not push** — no notifications; the app quietly accumulates content.
- **Topics, not chronology** — navigate by meaning, not by date.
- **Study, not consume** — the goal is understanding, not catching up with everything.
- **Personal** — no social features.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL URL |
| `OPENAI_API_KEY` | — | Required for embeddings |
| `ANTHROPIC_API_KEY` | — | Required for topic names & summaries |
| `RSS_POLL_INTERVAL_SECONDS` | `3600` | How often to poll each source |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Claude model for LLM tasks |
| `HDBSCAN_MIN_CLUSTER_SIZE` | `3` | Minimum articles per topic cluster |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origin(s) |

---

## Data model

```
Source        — RSS feed URL + metadata
Article       — scraped item with embedding vector
Topic         — auto (HDBSCAN cluster) or manual; has centroid embedding
ArticleTopic  — M2M with confidence score
TopicTrend    — weekly article-count snapshots per topic
TopicLink     — cosine-similarity edges for the graph
```

---

## Extending sources

Implement `app/connectors/base.py:BaseConnector` and register your connector in `services/scheduler.py`. The `RSSConnector` is the reference implementation.

---

## API overview

```
GET  /api/sources/                — list sources
POST /api/sources/                — add source (triggers immediate poll)
POST /api/sources/{id}/poll       — manual poll

GET  /api/topics/                 — list topics (with article/unread counts)
GET  /api/topics/{id}             — topic + articles
GET  /api/topics/{id}/trends      — weekly trend data
GET  /api/topics/clusters/pending — clusters awaiting user review
POST /api/topics/clusters/confirm — accept/rename/reject a cluster
POST /api/topics/recluster        — trigger manual re-clustering

GET  /api/digest/?since_days=7    — adaptive digest

GET  /api/graph/                  — graph nodes + edges

PATCH /api/articles/{id}          — mark read / bookmark
POST  /api/articles/mark-all-read — mark topic or all articles as read
```
