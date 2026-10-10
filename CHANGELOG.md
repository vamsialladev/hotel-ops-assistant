# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/). Versions follow [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-10-09
First release run for real: on Windows, with the Streamlit app, hybrid search and real Claude answers (the
earlier versions were built in a sandbox that couldn't run them). Every number below is measured.

### Added
- **Multi-page product:** Assistant (chat per property, streamed answers, source chips with effective dates,
  "Check with a manager" notes, copy, 👍 / 👎 with reasons), Insights for managers, Document library, How it works
  (results read from the newest eval report), Disclaimer and privacy, and an owner-only Admin page.
- **Answer safety:** wrong facts stated in a question are corrected from the sources; off-topic questions are
  refused before the API in both retrieval modes; runtime numeric grounding check; manager rules quoted word for
  word from the documents; partial answers no longer mistaken for refusals.
- **Demo protections:** per-session limit (20), server-side daily cap (200), 500-character limit, friendly errors
  with private logging, demo banner, footer links, privacy note.
- **Private usage log** (tokens, timing, cost estimate, refusals, grounding flags) with 5,000-entry retention.
- **White-label branding** (`branding.toml`), brand theme with light and dark mode, readable document names.
- **Eval:** 54 questions in 16 categories (cross-property, wrong facts, off-topic, escalation added); time to
  first word; scope and escalation metrics; every raw answer saved per run; keyword-only and hybrid runs.
- `pip-audit` in CI; Playwright scripts for README screenshots and design reviews; a terminal image renderer.

### Changed
- **Model: Claude Haiku 5.5** (was Haiku 4.5): 98% vs 96% answer accuracy on the same 54 questions, about a fifth
  of the cost ($0.19 vs $1.01 per 1,000 questions), about 0.9s more at p95.
- **Python 3.12 required:** `numpy~=2.5` doesn't install on 3.11 (found by the Docker build).
- Streamlit's file watcher turned off (it hung startup for 5+ minutes with PyTorch loaded).
- Docker image uses CPU PyTorch, runs as a non-root user and listens on `$PORT`.
- Business case uses the measured AI cost; projected net value for 2 properties is now $8,524 / $31,887 /
  $66,451 (pessimistic / base / optimistic).
- Coverage measures product code only.

### Fixed
- Dollar amounts rendered as LaTeX ("$50 … $200" became math).
- The eval graded a wrong "yes" as correct (q13) and safe injection answers as wrong (q32).
- Single-letter tokens ("s" in "What's") matched almost every passage in keyword search.
- File paths and folder names shown in the public UI.

### Results (Claude Haiku 5.5, 3 runs)
| | Keyword-only (live demo) | Hybrid |
|---|---|---|
| Strict retrieval | 96% (43/45) | 98% (44/45) |
| Answer accuracy | 96% | 98% |
| Correct refusals | 26/27 | 27/27 |
| Escalation rules | 54/54 | 54/54 |
| Full answer p95 | 2.71s | 2.42s |
| Cost per 1,000 questions | $0.17 | $0.19 |

148 unit tests, 96% coverage.

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
