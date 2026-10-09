# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/). Versions follow [Semantic Versioning](https://semver.org/).

## [1.2.0]
### Added
- One-click deploy on Streamlit Community Cloud: the app builds its search index on first start
- `USE_EMBEDDINGS` setting, and automatic fallback to keyword search when embeddings aren't installed

### Changed
- Requirements split into `requirements.txt` (light core), `requirements-hybrid.txt` (adds embeddings) and `requirements-dev.txt`

## [1.1.0]
### Added
- Strict passage-level retrieval eval; citation accuracy, numeric grounding, refusal, consistency (`--runs`), p50/p95 latency and cost metrics
- Adversarial eval questions: prompt injection, misspellings, multi-part, Spanish (37 questions, 11 categories)
- Prompt hardening: document text is treated as data, not instructions
- Staff feedback buttons with logging and a helpful-rate summary
- Business case scenarios (pessimistic, base, optimistic) and pilot KPIs with go / no-go criteria
- Pinned dependencies, `requirements-dev.txt`, Dependabot, coverage gate (70%) in CI
- Validation checklist for results that need a real API key

### Changed
- Keyword search no longer returns passages that match nothing; no passages means a refusal without an API call

## [1.0.0]
### Added
- Ingestion for Markdown, text and PDF documents with section-aware chunking
- Property filtering, superseded-document exclusion, PDF header/footer stripping, scanned-page detection
- Hybrid search (BM25 + embeddings, Reciprocal Rank Fusion) with light stemming
- Cited answers with Claude, with a fixed refusal message when sources don't cover the question
- Streamlit app and command-line tool
- 31-question evaluation with saved reports; 20 unit tests; CI with lint and regression gate
- Docker image, business case calculator, architecture and security documentation
- Step-by-step flow, commands reference, configuration and troubleshooting in README
- Contributing guide and pull request template
