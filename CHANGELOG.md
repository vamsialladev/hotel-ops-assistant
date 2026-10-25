# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/). Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added (final stage: guardrails, tracing, red team; 1.7.0)
- Shared guardrails from [hotel-ai-platform](https://github.com/vamsialladev/hotel-ai-platform) v0.1.2
  (`src/ops.py`): input checks before the rewrite and the API, output checks after the model. Decision 60.
- Passages pass through the shared quarantine before the model (the planted front desk note). Decision 61.
- New outcome `blocked` with refusal reason `guardrail`. Decision 62.
- One trace per question in the shared `ops_request_log` / `ops_trace_span` tables; "Reference: ..." on errors;
  Admin → Traces (waterfall, error rate, p50/p95, cost vs caps, guardrail blocks, health, CSV); feedback linked to
  the trace; structured JSON startup log lines; keep-awake visits (`?source=keepawake`) ask and log nothing.
- Red-team suite (`scripts/run_redteam.py`, `redteam/cases.jsonl`, docs/RED_TEAM.md) in CI.
- Eval after the change (2026-10-25, live keyword-only, 3 runs, `eval/reports/2026-10-25_1906_bm25_answers_claude-haiku-5-5.md`):
  answer accuracy 100% (162/162), strict retrieval 45/45, refusals 27/27, escalation 54/54, p95 3.22 s, $0.17 per
  1,000: the same as the v1.6.0 release run. An earlier run of the same code (54, 53, 53 of 54) crashed on a Windows
  console encoding error before it saved, so its two misses weren't recorded; it isn't counted.
### Changed
- Admin and staff lockout counted per server process as well as per session.
### Added (P-Fix-B: real chat)
- **Follow-up questions:** the latest message is rewritten into a standalone question from the last 3 turns (one
  short Haiku call; `REWRITE_MODE=llm|rule|off`), shown as "Understood as: ..."; only that question and the passages
  reach the model. Naming the other hotel asks about it and moves the picker. Decision 59.
- **One conversation across both hotels**, "Past conversations" in the sidebar (reopen one), "New conversation"
  keeps the old one for the browser session.
- **Share this conversation:** a read-only link with the conversation compressed inside the URL, personal data
  replaced first (`src/share.py`); opening it never calls the API.
- Multi-turn eval (`eval/run_multiturn_eval.py`, 15 + 4 held-out cases, 3 runs): answer accuracy 67% → 96%, p95
  2.95 s → 3.58 s, $0.18 → $0.22 per 1,000 requests. Free CI gate on follow-up retrieval (rule rewrite, 17/18).
- `scripts/make_captions.py` (captions from my own voice) and `docs/VIDEO_SCRIPT.md` with one follow-up.
### Fixed
- Grader: "I can't tell the guest the fee is waived" no longer counts as asserting the waiver.
### Changed
- README first screen: value line, demo video slot, "Try it live" with the wake note, At a glance with a cost row;
  new "Design at scale" section; Business value names who benefits and how a pilot would measure it.
- `scripts/record_demo.py` records a captioned screen recording with no AI voice (decision 58); `piper-tts` removed.
### Added
- CI: lychee link check on the README and docs; gitleaks secret scan (CI and pre-commit).

## [1.6.0] - 2026-10-15
### Added
- **Spanish questions** reach the model and get Spanish answers from the English documents (Spanish hotel vocabulary
  added to the search query, deterministic language detection, Spanish scope message). Refusals keep the exact English
  sentence.
- **Persistent request log** (Project 4): `DATABASE_URL` set to Postgres (Neon on the live app) or SQLite stores every
  request, feedback, error and staff report in one `app_log` table; unset keeps the files exactly as before. A failed
  write falls back to the file.
- **Personal-data redaction before storage:** emails, phone and card-like numbers and names masked, booking IDs hashed.
- **30-day retention** (`RETENTION_DAYS`), applied daily and by `python scripts/retention.py`.
- **Staff role** next to the open Demo mode (`STAFF_PASSWORD`): report an answer for review, no per-session cap.
- **Operations page** (owner only): requests, errors, p50/p95, cost per day, refusals, escalations, budget status, log
  storage, kill switch, staff reports.
- **Budgets** (`BUDGET_P95_S` 4.0 s, `BUDGET_COST_PER_1000` $0.50), also gated by the eval harness in CI.
- **Kill switch** (`KILL_SWITCH`), 30 s per-call timeout and SDK retries with backoff.
- `docker compose up --build`: the app with its own Postgres. CI runs the store tests against Postgres too.

### Changed
- **Safety rule** catches paraphrased and Spanish emergencies ("smoke coming from under a door", "hay un incendio");
  0 false alarms on every non-safety eval question and suggestion.
- **Emergencies never reach the model:** a fixed safety message (English or Spanish) and the manager note.
- Privacy page and Admin note say where logs are kept (database with redaction and retention, or until restart).

### Measured (eval harness, live, keyword-only, 3 runs, 2026-10-15)
- Dev answer accuracy 98% → 100% (162/162); strict retrieval 44/45 → 45/45 (q37 Spanish); p95 2.93 s; $0.18 / 1,000.
- Held-out (13 cases added in Project 3): answer accuracy 67% → 85%, escalation rules 85% → 100%, answer language
  33% → 100%. Eight new held-out cases written before the fixes: 62% → 100%.

## [1.5.0] - 2026-10-11
### Added
- **Complete request log** (schema version 2): one record per request, whether answered, refused, off-topic,
  greeting, error or cap (the session limit is now logged too). Each record has a request ID, an anonymous session
  ID, the outcome and refusal reason, the full answer, citations, follow-ups shown, every retrieved passage with
  its score and whether it was cited, timing, tokens, cost, grounding flags and a short safe error message.
  👍 / 👎 ratings carry the same request ID.
- **Admin request list:** one table, newest first, with colored result badges, filters (date range, property,
  result, feedback, errors only, question text), "Showing X of Y requests" and "Load more".
- **Request details:** selecting a row opens a dialog with Summary, Answer, Sources, Performance, Checks,
  Feedback and Raw tabs, plus "Download this request (JSON)".
- **Log downloads:** "Download usage log (JSONL)" and "Download feedback log (JSONL)" (Admin only), under a
  "Log since … · Logs reset when the app restarts" note.

### Changed
- Every log record is masked for secret values and Anthropic-key shapes before it's written, including text a
  visitor types.
- Records from older versions get an outcome and a stable ID; anything missing shows "not recorded".
- The activity table and "Recent questions" are replaced by the request list. The privacy page says questions and
  answers are logged for quality and kept only until the app restarts, and that no names or accounts are collected.
- README author line uses the current title.

## [1.4.0] - 2026-10-10
### Added
- **In-app guidance** on the welcome screen (first visit and after every New conversation, both properties): a
  "How to use" strip, a "What this demo knows" panel whose topic chips come from the indexed documents,
  good-question examples with a tip, and a rotating "Try: …" hint in the chat input. Fits one laptop screen.
- **Curated suggestions** (`data/suggestions.toml`): topic examples, 2-3 follow-ups under each answer (chosen by
  the cited section's topic, never repeating a question), "Did you mean" after a refusal (closest curated
  questions by keyword score) and the property's popular questions as a fallback. No extra API call.
- **Greetings and meta questions** ("hi", "thanks", "what can you do?") get an instant reply with examples; no
  API call and not counted toward the limits. Off-topic or gibberish input gets a polite scope message with
  popular questions and topic chips.
- **Content coverage:** three synthetic guest handbooks (brand-wide and one per property, effective 2026-04-01)
  for Wi-Fi, early check-in, the gym, room service, breakfast, laundry, quiet hours, luggage, accessibility
  and hiking. No existing fact changed.
- **Visitor eval** (`eval/visitor_questions.jsonl`, 49 questions a visitor types first) with first-question
  success: 43% → 100% keyword-only, 49% → 100% hybrid (real answers). CI gates its routing and retrieval at
  100% and checks every curated suggestion retrieves its topic.
- Question source logged with every question and rating; Insights shows how people ask, most-used topics,
  typed policy gaps and suggestions that got a 👎; Admin shows the source and first-question success (live and
  from the eval); How it works explains how the app helps users ask.
- **Narrated demo video:** `scripts/record_demo.py` adds an AI voice (Piper, offline, open source) timed to each
  step, mixed to about -16 LUFS, plus a WebVTT track and the narration script (`--no-voice` to skip).
- README "See it in action" at the top; new screenshots from the live app; `make eval-visitors`, `make video`.

### Changed
- Search spells compound words one way in questions and documents (check-out/checkout, Wi-Fi/wifi) and adds a
  short list of visitor synonyms to the query (gym → fitness, left → lost and found).
- The model comparison was re-run on the new documents: Haiku 4.5 98% (96–98%) vs Haiku 5.5 97% (96–98%),
  within run-to-run range; 5.5 stays shipped for about a fifth of the cost. The How it works caption follows the
  data instead of a fixed sentence.
- 54-question eval re-run: keyword-only 98% answer accuracy (was 96%), 44/45 retrieval, 27/27 refusals.

### Fixed
- On phones, the sidebar stayed open over the chat input after "New conversation", so nothing could be typed;
  the input is now freed and focused (regression test).
- After a push, the live app showed an error on every page: Streamlit Cloud's in-place update kept old modules
  in memory. `codeguard.py` re-imports changed code together, and the index rebuilds when documents change.
- Usage and feedback logs resolve their file at call time, so tests no longer write to the local log.

## [1.3.3] - 2026-10-10
### Added
- Captioned 2-minute demo video, recorded from the live app with real answers by `python scripts/record_demo.py`
  (Playwright + ffmpeg): title card, burned-in captions, end card with links. Published on the portfolio site
  (https://vamsialla.com/videos/hotel-ops-demo.mp4), embedded on the case study page and linked from the README.
- README command "Re-record the demo"; unit tests for the recorder's caption timing and cards (208 tests).

### Changed
- `docs/images/demo.gif` re-made from the live app (the dog question at Beach Resort, 10 s).
- `docs/video/` (the video master and raw recording) is git-ignored.

### Verified on the live app
- Answers with sources at both hotels, a "Check with a manager" answer, the fire assembly point refusal, an
  off-topic question refused before the API, and a wrong fee corrected.
- New conversation (disabled → enabled → toast → disabled), 👍 and 👎 with a reason appearing on Insights,
  footer links, the Document library link, and the Admin sign-in form.

## [1.3.2] - 2026-10-10
### Added
- `python scripts/make_secrets.py` (`make secrets`) builds `.streamlit/secrets.toml` from `.env`: every
  setting at the top level and double-quoted, ready to paste into Streamlit Cloud. It prints only "set" or
  "missing". `.streamlit/secrets.toml.example` shows the keys with placeholders.
- Startup check: a missing `ANTHROPIC_API_KEY` or `ADMIN_PASSWORD` is logged by name, never by value.
- Admin page: each secret shown as set or missing; recent errors show a plain "likely cause".
- A line under the chat input: "Answers are written live by AI using only the documents in the Document
  library", linking to that page.
- README: a "Secrets" section (copy, paste, save, reboot) and the order settings are read in.
- Tests for the secrets check, the secrets file, error categories, the new line and the Admin secrets status
  (205 tests, 96% coverage).

### Changed
- API errors are classified with a model-not-found category and logged with their likely cause
  (authentication, credit balance, model not found, rate limit, network).

## [1.3.1] - 2026-10-10
### Added
- **Owner monitoring on the Admin page:** health and recent errors, warnings when the error rate or estimated
  cost crosses a threshold (`ALERT_ERROR_RATE`, `ALERT_MIN_EVENTS`, `ALERT_DAILY_COST_USD`), questions today vs
  the daily cap, a filterable activity table with 👍 / 👎, CSV downloads of the usage, feedback and error logs,
  sign out, and automatic sign-out after 30 minutes idle (`ADMIN_IDLE_MINUTES`).
- **Error list:** every caught error is recorded in `data/errors.jsonl` (git-ignored, bounded) as well as stdout.
- **Error boundary** on every page and button callback: a friendly message instead of Streamlit's crash screen.
- One-click Windows launcher: `run_app.bat` / `run_app.ps1`.
- README: Monitoring section, live demo link, auto-redeploy note, and a note on AI-assisted development.
- Tests: every page rendered with `AppTest`, with and without an injected exception; button state; file
  races; monitoring; sign out and auto-lock (184 tests, 96% coverage).

### Changed
- "New conversation" is disabled with a tooltip when the conversation is empty, and shows a toast when it clears.
- Usage and feedback records carry a `turn_id`, so ratings line up with their answers.
- Codespaces dev container uses Python 3.12.

### Fixed
- Crash on the Assistant page when two app instances share `data/` on Windows (file-sharing `PermissionError`
  on the daily counter and logs), reproduced with a two-process test and fixed with retries and safe fallbacks.
- Streamlit Cloud kept serving old code after a push: the file watcher was off (decision 19). It's back on with
  `.venv` excluded, which also fixes the original startup hang; local runs and Docker turn it off for speed.

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
