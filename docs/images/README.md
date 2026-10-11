# Screenshots

Every image here is real output from this repo. Regenerate them after changes so they always match the code.

## Terminal output (rendered from real command output)
| File | Shows | How to regenerate |
|---|---|---|
| `eval-retrieval.png` | 54-question eval, hybrid: retrieval, scope and escalation checks | `python -m eval.run_eval > out.txt`, then `python scripts/render_terminal.py out.txt docs/images/eval-retrieval.png --command "python -m eval.run_eval" --title "hotel-ops-assistant: retrieval, scope and escalation eval (hybrid)"` |
| `tests.png` | `pytest` with coverage: 307 passed, 97% | `python -m pytest -q --cov=src --cov=eval > out.txt`, then render as above |
| `business-case.png` | Calculator scenarios, 100 properties (projection) | `python scripts/business_case.py --scenarios --properties 100 --hosting 15000 > out.txt`, then render |

## App screenshots (captured from the running app with real questions)
Start the app (`streamlit run app.py`), then run `python scripts/capture_screenshots.py`. It asks about 9 real
questions (about $0.002) and never captures the Admin page.

| File | Shows |
|---|---|
| `demo.gif` | The first cited answer on the live app (the dog question at Beach Resort), with its caption (10 s, about 1.4 MB, no sound); made by `python scripts/record_demo.py` |
| `assistant-welcome.png` | Live app welcome screen: How to use, What this demo knows with topic chips, good questions (1280×800) |
| `follow-ups.png` | Live app: a cited answer with related questions |
| `did-you-mean.png` | Live app: a booking request refused, with "Did you mean" questions and topic chips |
| `answer-sources.png` | Gold member late checkout at Beach Resort, with sources expanded |
| `two-properties.png` | The dog question at both properties, side by side |
| `check-with-manager.png` | A $300 refund question with the manager note quoting the rule |
| `refusal.png` | Fire assembly point: refused, with the safety note |
| `insights.png`, `library.png`, `how-it-works.png` | The manager and engineer pages |
| `assistant-light.png`, `assistant-dark.png` | The Assistant in light and dark mode |
| `phone.png` | The Assistant at phone width (390 px) |

Clear `data/usage.jsonl` and `data/feedback.jsonl` before capturing, so Insights shows only the capture session.
For a design review of every page in both modes and both widths: `python scripts/capture_review.py --phone`.

## Checklist before committing an image
- No API key, `.env`, admin page or personal browser tabs visible
- Only real answers and real usage; no made-up data
- Text is readable without zooming
- PNG under 1 MB where possible, GIF under 5 MB

## Admin request log (`request-log/`, captured from a local run with real answers)
| File | Shows |
|---|---|
| `01-request-list.png`, `02-request-list-filtered.png` | Request list, unfiltered and searched for "dog" |
| `03`–`09-details-*.png` | Request details dialog: Summary, Answer, Sources, Performance, Checks, Feedback, Raw |
| `10-details-phone.png` | The dialog at phone width (390 px) |

Run the app locally with a test-only `ADMIN_PASSWORD` set in the environment and a separate `LOG_DIR`, ask a few
questions (an answer, a refusal, a greeting, an off-topic one), rate two, then sign in to Admin and capture. Never use
the real admin password for screenshots, and check that no secret value is visible.

