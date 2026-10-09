# Architecture

## System overview
```mermaid
flowchart LR
    subgraph Offline["Indexing (when documents change)"]
        A["Hotel documents<br/>MD, TXT, PDF"] --> B["Load and clean<br/>skip superseded docs<br/>strip PDF headers/footers<br/>flag scanned pages"]
        B --> C["Section-aware chunking<br/>tag property + section"]
        C --> D["Keyword index<br/>BM25 + stemming"]
        C --> E["Vector index<br/>sentence embeddings"]
    end
    subgraph Online["Answering (every question)"]
        F["Staff question<br/>+ selected property"] --> G["Filter: this property<br/>+ brand-wide docs"]
        G --> H["Hybrid search<br/>BM25 + vectors<br/>Reciprocal Rank Fusion"]
        D --> H
        E --> H
        H --> I["Top 5 passages"]
        I --> J["Claude<br/>answer only from sources<br/>cite every fact<br/>refuse if not found"]
        J --> K["Answer + sources<br/>in Streamlit app"]
    end
```

## Request flow
```mermaid
sequenceDiagram
    actor Staff as Front-desk agent
    participant App as Streamlit app
    participant Search as Retriever
    participant LLM as Claude API
    Staff->>App: Picks property, asks a question
    App->>Search: search(question, property)
    Search->>Search: Filter to property + brand-wide
    Search->>Search: BM25 and vector ranking, fused
    Search-->>App: Top 5 passages
    App->>LLM: Rules + numbered passages + question
    LLM-->>App: Short answer with [n] citations
    App-->>Staff: Answer, cited sources, latency, tokens
```

## Components
| Component | File | Responsibility |
|---|---|---|
| Config | `src/config.py` | Paths, model names, top-k; all overridable by environment variables |
| Ingestion | `src/ingest.py` | Load documents, clean, chunk, tag, embed, save index |
| Retrieval | `src/retrieve.py` | Property filter, BM25 + vector search, rank fusion |
| Generation | `src/generate.py` | Prompt, Claude call, citation parsing, refusal detection |
| Web app | `app.py` | Staff interface with sources and debug view |
| CLI | `ask.py` | Quick command-line questions |
| Evaluation | `eval/run_eval.py`, `eval/metrics.py` | 37 questions; strict retrieval, citation and grounding checks; reports; CI threshold |
| Feedback | `src/feedback.py` | Logs staff 👍 / 👎 for weekly review |
| Tests | `tests/` | Ingestion, isolation, stemming, citation parsing |

## Key design choices
See [DECISIONS.md](DECISIONS.md) for the full log. In short:
- **Hybrid search**, because staff use exact terms (prices, airport codes) and loose phrasing.
- **Property filter before search**, because a correct answer from the wrong hotel is still wrong.
- **Refuse rather than guess**, because a confident wrong answer causes guest conflicts.
- **Small, fast model**, because a guest is waiting.

## Scaling path
| Today (2 properties) | At 100+ properties |
|---|---|
| Index stored in local files | Managed vector database (e.g. pgvector) |
| Rebuild the whole index | Incremental re-indexing when a document changes |
| Single Streamlit app | API service + staff app, with single sign-on per property |
| No access control | Role-based access per property |
| Basic logging | Metrics dashboard: usage, latency, cost, refusal rate (Project 4) |
