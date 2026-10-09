# Screenshots

## Already included (real outputs, generated from this repo)
| File | Shows | Used in |
|---|---|---|
| `tests.png` | `pytest -v --cov`: 31 passed, 92% coverage | README → Testing |
| `eval-retrieval.png` | 37-question eval, 32/34 strict retrieval | README → Results |
| `business-case.png` | Calculator scenarios, 100 properties | README → Business value |

Regenerate them after changes so they always match the code.

## Capture these yourself (they need your API key)
Run `streamlit run app.py`, make the browser window about 1200px wide, and capture with **Win + Shift + S**.

| File | Property | Question | Before capturing |
|---|---|---|---|
| `answer.png` | beach-resort | A Gold member wants late checkout on Saturday. How late? | Open "Sources used" |
| `two-properties.png` | both | Can a guest bring their dog? | Capture both answers, place side by side |
| `refusal.png` | beach-resort | Where is the fire assembly point? | Shows the yellow refusal |
| `demo.gif` | beach-resort | Any 2 questions | Record 10–15 seconds with ScreenToGif, under 5 MB |
| `ci.png` | n/a | GitHub → Actions tab | After your first push shows a green check |

Then open the main README and remove the `<!--` and `-->` markers around the hero GIF and the app screenshot table.

## Checklist before committing an image
- No API key, `.env`, or personal browser tabs visible
- Text is readable without zooming
- File under 1 MB for PNG, under 5 MB for GIF
