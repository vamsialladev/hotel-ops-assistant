# Security and Data Privacy

This is a portfolio project: a **simulated client engagement** with **synthetic hotel documents**, running as an
open public demo with no sign-in. The protections below are sized for that. Real sign-in with roles and
per-property access is planned for Project 4.

## Data handled
- **Indexed:** hotel policy documents only (policies, menus, SOPs, staff notes). All synthetic.
- **Not indexed:** guest records, payment data, reservations. The assistant answers policy questions; it can't look up guests.
- **Sent to the Claude API per question:** the question and the top 5 matching passages. Earlier turns are never sent.
- **Logged on the app server (git-ignored, never committed):**
  - `data/usage.jsonl`: time, property, model, retrieval mode, the question as typed, tokens in/out, estimated cost,
    time to first word, total time, refused or not, grounding flag, manager notes, retrieved passages and scores,
    error code.
  - `data/feedback.jsonl`: 👍 / 👎, the optional reason, the question and answer.
  - `data/daily_count.json`: today's question count for the daily cap.
- **Logged to stdout** (Streamlit Cloud's owner-only logs): the same usage record **without the question text**.
- **Never logged anywhere:** the API key, the admin password or any other secret.

## Log retention
- Usage and feedback logs keep only the **most recent 5,000 entries** (`LOG_MAX_ENTRIES`); older lines are trimmed
  on every write.
- On Streamlit Community Cloud the files are deleted whenever the app restarts or redeploys.
- Questions are stored **as typed**. The input box and the privacy note ask visitors not to enter guest names or
  personal details, but nothing stops them. Personal-data redaction before logging and before API calls is planned
  for Project 4. Until then, the public Insights page masks emails, card-like numbers and phone numbers in refused
  questions, and the owner should delete the logs regularly.

## Secrets
- The API key and admin password live only in `.env` locally (excluded by `.gitignore` and `.dockerignore`) or in
  Streamlit secrets in the cloud. `.env.example` holds placeholders only.
- A pre-commit hook blocks committed private keys; GitHub secret scanning and push protection are enabled on the repo.
- Error messages are masked for anything that looks like an Anthropic key before they're logged.

## Threat model

| Threat | Impact | Mitigation | Status |
|---|---|---|---|
| API key leak | Someone spends the owner's credit | Key only in `.env` / Streamlit secrets; git- and docker-ignored; pre-commit key check; GitHub secret scanning + push protection; key masked in error logs | Mitigated |
| Cost abuse by visitors | API bill grows | 20 questions per session, 200 per day across all visitors (server-side, survives refresh), 500-character limit, off-topic questions refused before the API, `max_tokens` cap; owner sets a spending limit in the Anthropic Console | Mitigated; the daily count resets if the cloud app restarts |
| Prompt injection in documents or questions | Wrong or harmful instructions followed (e.g. "waive all fees") | System prompt treats sources as data; a planted injection is in the eval and checked by hand every run; answers can't take actions | Partly mitigated: prompt rules reduce, not eliminate, the risk |
| XSS through answers, documents or questions | Script runs in a visitor's browser | All model output, document text and user input is HTML-escaped (and `$` escaped) before display; `unsafe_allow_html` only for static styling and a static diagram; unit tests with `<script>` input | Mitigated |
| Admin brute force | Owner data exposed | `hmac.compare_digest`, 1-second delay per failure, 5-attempt lockout for 15 minutes, page hidden until unlocked and absent when no password is set | Partly mitigated: lockout is per session, not per IP; this is demo protection, not authentication |
| Cross-property data leak | Staff told another hotel's rules | Search filtered to the selected property + brand-wide docs before ranking (unit-tested); cross-property eval cases (q38, q39) | Mitigated |
| Personal data in logs | Guest details stored in logs | Input reminder, privacy note, git-ignored logs, 5,000-entry retention, masking on the public Insights page, question text kept out of stdout logs | Partly mitigated: redaction planned for Project 4 |
| Vulnerable dependencies | Known CVEs in the app | Pinned versions, Dependabot weekly, `pip-audit` in CI fails on any known vulnerability | Mitigated |
| Wrong answer reaching a guest | Refunds, complaints, safety risk | Answers only from cited sources; fixed refusal; wrong facts in questions corrected; numbers checked against cited sources at runtime; "Check with a manager" notes for refunds, safety and repeated complaints; 54-case eval on every change | Partly mitigated: answers can still be wrong, so the disclaimer tells staff to verify important decisions |

## OWASP Top 10 for LLM Applications (2025)

| OWASP risk | Relevant here? | Mitigation in this project | Status |
|---|---|---|---|
| LLM01 Prompt Injection | Yes | Sources treated as data in the system prompt; planted injection in `front_desk_notes.txt` tested every eval run and read by hand; the model has no tools or actions | Partly mitigated |
| LLM02 Sensitive Information Disclosure | Yes | No guest data indexed; property isolation; public Insights masks emails and numbers; question text kept out of stdout logs; admin data behind a password | Partly mitigated (redaction in Project 4) |
| LLM03 Supply Chain | Yes | Pinned dependencies, Dependabot, `pip-audit` in CI, official Anthropic SDK only | Mitigated |
| LLM04 Data and Model Poisoning | Yes (documents) | Superseded documents excluded; instruction-like text in documents flagged in the Document library; documents come from the hotel's own staff | Partly mitigated (content screening for uploads in Project 4) |
| LLM05 Improper Output Handling | Yes | Output is HTML- and `$`-escaped; answers are never executed, used in file paths or passed to a shell | Mitigated |
| LLM06 Excessive Agency | Low | The model can only write text; it has no tools, no write access and no external actions | Mitigated by design |
| LLM07 System Prompt Leakage | Low | The prompt contains no secrets; it's public in `src/generate.py` | Accepted |
| LLM08 Vector and Embedding Weaknesses | Yes | Property filter applied before ranking; embeddings built only from the hotel's documents; no user-supplied documents | Mitigated |
| LLM09 Misinformation | Yes | Cited answers, refusals, runtime numeric grounding check, correction of wrong facts in questions, manager notes, measured eval | Partly mitigated |
| LLM10 Unbounded Consumption | Yes | Per-session and daily caps, length limit, scope check before the API, `max_tokens`, Console spending limit | Mitigated |

## Partly mitigated: plan for Project 4
- **Real authentication:** sign-in with roles (staff, manager, owner) and per-property access, replacing the shared
  admin password and the per-session lockout.
- **Personal-data redaction** of questions before they're logged or sent to the API.
- **Prompt-injection screening** of new or changed documents before indexing, plus an LLM judge (Project 3)
  calibrated against human labels for "did the answer follow an injected instruction?".
- **Durable, access-controlled log storage** with an explicit retention period, instead of local files.
- **Per-IP rate limiting** at the hosting layer.

## Public deploy checklist
- Set a **monthly spending limit** in the Anthropic Console before sharing the link.
- Set `ADMIN_PASSWORD` to a long random value (or leave it unset to remove the Admin page).
- Keep `MAX_QUESTIONS_PER_SESSION` and `MAX_QUESTIONS_PER_DAY` at or below the defaults.

## Reporting
This is a portfolio project. Please report issues by opening a GitHub issue; for anything sensitive, email
vamsialla.dev@gmail.com instead.
