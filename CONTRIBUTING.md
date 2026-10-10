# Contributing

## Workflow
1. Create a branch from `main`: `feature/<short-name>`, `fix/<short-name>` or `docs/<short-name>`.
2. Make the change, with tests or eval questions where relevant.
3. Run the checks below locally.
4. Open a pull request. CI must pass before merging.

## Checks before every pull request
```bash
ruff check . && ruff format --check .
python -m pytest -q --cov=src --cov=eval
pip-audit -r requirements.txt
python -m eval.run_eval                 # and --bm25-only, the live demo's mode
```
If retrieval, scope or escalation accuracy drops, explain why in the pull request. For prompt or model changes,
also run `python -m eval.run_eval --answers --runs 3 --price-in 0.10 --price-out 0.50` and read the saved
`.jsonl` answers for the injection, wrong-fact and off-topic questions by hand.

Keep logic in `src/` with unit tests; pages in `views/` only wire it to the UI. Never render dynamic text with
`unsafe_allow_html` unless it went through `src/display.py` escaping first.

## Commit messages
Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for | Example |
|---|---|---|
| `feat:` | New behavior | `feat: add OCR for scanned PDFs` |
| `fix:` | Bug fix | `fix: strip page-number footers from PDFs` |
| `test:` | Tests or eval questions | `test: add eval questions for spa policies` |
| `docs:` | Documentation | `docs: add screenshots to README` |
| `refactor:` | Code change, same behavior | `refactor: split chunking into its own module` |
| `chore:` | Tooling, CI, dependencies | `chore: add ruff to CI` |

## Common tasks

**Add or update a document**
1. Put it in `data/raw/<property>/`, or `data/raw/shared/` if it applies to every property.
2. For Markdown, add front matter: `title`, `effective` date, and `status: current`.
3. If it replaces an older file, set the old file's front matter to `status: superseded`.
4. Rebuild the index and add 1–2 eval questions that the new document should answer.

**Add a new property**
1. Create `data/raw/<new-property>/` with its documents. The folder name becomes the property ID.
2. Add a `[properties.<new-property>]` block to `branding.toml` with its display name, highlights and sample questions.
3. Rebuild the index; the property appears in the app automatically.
4. Add eval questions for it (including a cross-property check), and extend the isolation test in `tests/test_retrieve.py`.

**Rebrand for a client**
Edit `branding.toml`, the theme colors in `.streamlit/config.toml`, and the files in `assets/`. See the README.

**Add an eval question**
Add one line to `eval/questions.jsonl` with `property`, `question`, `category`, `expected_source`, `expected_text`
(a phrase that must be in the retrieved passage) and `must_contain`. Optional fields:

| Field | Meaning |
|---|---|
| `must_not_contain` | Phrases the answer must not assert (a sentence that reports or rejects the claim doesn't count) |
| `must_contain_any` | At least one must appear, e.g. correction words for a wrong fact stated in the question |
| `escalate` | The "Check with a manager" rule ids expected for this question (`[]` = none) |
| `unanswerable` | `true` for questions the system must refuse; set `expected_source` to `null` |
