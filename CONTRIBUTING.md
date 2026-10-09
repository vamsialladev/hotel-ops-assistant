# Contributing

## Workflow
1. Create a branch from `main`: `feature/<short-name>`, `fix/<short-name>` or `docs/<short-name>`.
2. Make the change, with tests or eval questions where relevant.
3. Run the checks below locally.
4. Open a pull request. CI must pass before merging.

## Checks before every pull request
```bash
ruff check . && ruff format --check .
python -m pytest -q
python -m eval.run_eval
```
If retrieval accuracy drops, explain why in the pull request.

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
2. Rebuild the index; the property appears in the app automatically.
3. Add eval questions for it, and extend the isolation test in `tests/test_retrieve.py`.

**Add an eval question**
Add one line to `eval/questions.jsonl` with `property`, `question`, `category`, `expected_source` and `must_contain`. For a question the system must refuse, set `expected_source` to `null` and `unanswerable` to `true`.
