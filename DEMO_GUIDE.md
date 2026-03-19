# Demo Guide — Onboarding / Offboarding Agent POC

## Overview

This POC automates employee GitHub access using an AI agent pipeline:

```
HTTP Request → FastAPI → CrewAI Agents → Ollama (RAG) + GitHub Enterprise
```

**Onboarding flow:**
1. **Role Classifier** searches the ChromaDB knowledge base (via Ollama embeddings) to determine the correct GitHub team for the employee's role
2. **GitHub Manager** resolves the corporate email → GitHub username, then adds the user to the team
3. **Onboarding Reporter** generates a markdown summary report

**Offboarding flow:**
1. **GitHub Manager** resolves the email → GitHub username, removes from both teams
2. **Offboarding Reporter** generates a compliance report

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 – 3.13 | |
| [Ollama](https://ollama.com) | latest | Must be running locally |
| GitHub Enterprise token | — | `admin:org` + `read:user` scopes |
| uv | latest | `pip install uv` |

---

## Step 1 — Install Dependencies

```bash
cd onboarding_agent

# Option A: using uv (recommended)
crewai install

# Option B: using pip
pip install -r requirements.txt
```

---

## Step 2 — Pull Ollama Models

Two models are required — the LLM for reasoning and an embedding model for RAG:

```bash
ollama pull llama3.2          # LLM used by all agents
ollama pull nomic-embed-text  # Embeddings used by ChromaDB RAG
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

---

## Step 3 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# LLM
MODEL=ollama/llama3.2:latest
API_BASE=http://localhost:11434

# GitHub Enterprise
GITHUB_TOKEN=ghp_your_token_here
GITHUB_ORG=your-org-name
GITHUB_BASE_URL=https://github.yourcompany.com/api/v3
```

> **GitHub token scopes needed:** `admin:org` (to manage team membership) and `read:user` (to resolve email → username via search).

---

## Step 4 — Set Up GitHub Teams

In your GitHub Enterprise organisation, create two teams if they don't exist:

| Team name | Slug | Access level |
|---|---|---|
| Developer | `developer` | Read + Write on repos |
| ReadOnly | `readonly` | Read-only on repos |

The team **slug** (lowercase, hyphenated) is what the agent uses — not the display name.

To find or verify slugs:
```
https://github.yourcompany.com/orgs/YOUR_ORG/teams
```

---

## Step 5 — Load the Knowledge Base into ChromaDB

Before starting the server, index the role policy documents into ChromaDB:

```bash
python init_db.py
```

Expected output:
```
Knowledge dir : /path/to/onboarding_agent/knowledge
ChromaDB path : /path/to/onboarding_agent/.chromadb

Files to index:
  - role_policies.md

Indexing knowledge base — calling Ollama for embeddings...
(This may take a minute on first run)

Done. 24 chunks indexed into 'onboarding_policies'.
You can now start the server: onboarding_agent
```

**This only needs to be done once.** The `.chromadb/` directory persists across server restarts.

To force a full re-index after editing `knowledge/role_policies.md`:
```bash
python init_db.py --force
# or via the API once the server is running:
curl -X POST http://localhost:8000/rag/reindex
```

---

## Step 6 — Start the API Server

```bash
onboarding_agent
# or
uvicorn onboarding_agent.api:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Open the interactive API docs: **http://localhost:8000/docs**

---

## Step 7 — Demo Scenarios

### Health Check

```bash
curl http://localhost:8000/health
```
```json
{"status": "ok", "service": "onboarding-agent"}
```

---

### Demo 1 — Onboard a Software Engineer (→ Developer team)

```bash
curl -X POST http://localhost:8000/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "Alice Smith",
    "email": "alice.smith@company.com",
    "employee_role": "Senior Software Engineer",
    "department": "Platform Engineering"
  }'
```

**What the agents do:**
- `role_classifier` queries ChromaDB: *"which team for Senior Software Engineer?"* → returns `developer`
- `github_manager` resolves `alice.smith@company.com` → GitHub username → calls `add_membership(developer)`
- `onboarding_reporter` writes a markdown report summarising access granted

**Expected response:**
```json
{
  "status": "success",
  "employee": "Alice Smith",
  "email": "alice.smith@company.com",
  "report": "## Onboarding Summary\n..."
}
```

A full report is also saved to `onboarding_report.md`.

---

### Demo 2 — Onboard a Product Manager (→ ReadOnly team)

```bash
curl -X POST http://localhost:8000/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "Bob Jones",
    "email": "bob.jones@company.com",
    "employee_role": "Product Manager",
    "department": "Product"
  }'
```

**What differs from Demo 1:**
- `role_classifier` queries ChromaDB: *"which team for Product Manager?"* → returns `readonly`
- `github_manager` adds Bob to the `readonly` team instead

---

### Demo 3 — Offboard an Employee

```bash
curl -X POST http://localhost:8000/offboard \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "Alice Smith",
    "email": "alice.smith@company.com",
    "reason": "Resignation"
  }'
```

**What the agents do:**
- `github_manager` resolves the email → GitHub username
- Attempts removal from **both** `developer` and `readonly` teams (one will be a no-op)
- `offboarding_reporter` generates a compliance report

---

### Demo 4 — Refresh the Knowledge Base

If you edit `knowledge/role_policies.md` (e.g., add a new role), re-index without restarting:

```bash
curl -X POST http://localhost:8000/rag/reindex
```
```json
{"status": "ok", "chunks_indexed": 24}
```

---

## Watching Agent Reasoning (Console)

The server runs agents in `verbose=True` mode. In the terminal running the server, you will see each agent's step-by-step reasoning:

```
[role_classifier] > Searching knowledge base for: "team for Senior Software Engineer"
[role_classifier] > Tool result: "Roles in the Developer team: Software Engineer, Senior Software Engineer..."
[role_classifier] > Final answer: developer

[github_manager] > Resolving alice.smith@company.com → alice-smith
[github_manager] > Adding alice-smith to developer team...
[github_manager] > SUCCESS: Added to 'developer' team
```

This is the core of the demo — showing the agents reasoning through the task.

---

## Using Swagger UI (No curl required)

Navigate to **http://localhost:8000/docs** for a click-through interface:

1. Click **POST /onboard** → **Try it out**
2. Edit the example JSON with real values
3. Click **Execute**
4. View the response and the agent's report inline

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI (port 8000)                  │
│   POST /onboard          POST /offboard    POST /rag/reindex│
└───────────────────────────────┬─────────────────────────────┘
                                │
              ┌─────────────────┴──────────────────┐
              │                                    │
     OnboardingCrew                       OffboardingCrew
              │                                    │
    ┌─────────┼──────────┐             ┌───────────┴────────┐
    ▼         ▼          ▼             ▼                    ▼
role_      github_    onboarding_   github_           offboarding_
classifier  manager   reporter      manager           reporter
    │         │                       │
    ▼         ▼                       ▼
 RAG tool  GitHub tool           GitHub tool
    │         │                       │
    ▼         ▼                       ▼
ChromaDB  GitHub Enterprise      GitHub Enterprise
(Ollama   (email → username      (remove from all
embeds)    → add to team)         teams)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `connection refused` on port 11434 | Run `ollama serve` |
| `model not found` | Run `ollama pull llama3.2` |
| `nomic-embed-text not found` | Run `ollama pull nomic-embed-text` |
| `No GitHub account found for email` | User's GitHub email may be set to private; ask them to make it public in GitHub settings |
| `404 Not Found` on team | Verify the team slug is exactly `developer` or `readonly` (lowercase) |
| `403 Forbidden` on GitHub | Token missing `admin:org` or `read:user` scope |
| Agent takes too long | Normal for local LLM — llama3.2 on CPU can take 1–3 min per request |
