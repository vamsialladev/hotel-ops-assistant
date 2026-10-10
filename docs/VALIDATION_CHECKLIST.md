# Validation Checklist

What's already measured (by running everything on Windows with a real API key) and what still needs a person.
Record results in the README and in [ENGINEERING_LOG.md](ENGINEERING_LOG.md).

## Done (measured, 2026-10-09)
- [x] Hybrid and keyword-only retrieval: 98% (44/45) and 96% (43/45) strict, on 54 questions.
- [x] Answer eval with Claude Haiku 5.5, 3 runs, both modes: 98% hybrid, 96% keyword-only; correct refusals,
      citation accuracy, numeric grounding, time to first word, p50/p95 latency and cost per 1,000 questions.
- [x] Haiku 4.5 vs 5.5 on the same questions and settings (decision 26).
- [x] The prompt-injection question read by hand in every final run: no answer waives the fee.
- [x] The Streamlit app started headless; every page loaded; scripted QA pass (251 checks) in light and dark mode,
      laptop and phone width, including limits, errors and the Admin lockout.
- [x] README screenshots and the demo GIF captured from the real app (`scripts/capture_screenshots.py`).

## 1. Manual baseline for the business case (about 20 minutes)
The most uncertain assumption is **minutes saved per lookup**.
1. Pick 10 questions from `eval/questions.jsonl`.
2. **Without the app:** open the documents in `data/raw/` and time how long each answer takes you to find.
3. **With the app:** time the same 10 questions.
4. Run the calculator with your measured minutes saved:
   ```bash
   python scripts/business_case.py --minutes-saved <your measured number>
   ```
**Fill in:** a line in BUSINESS_CASE.md under Assumptions: "Measured on 10 questions: manual X s, assistant Y s."
Be honest that it's a small, self-run test. It's still far better than a pure assumption.

## 2. Held-out questions (about 30 minutes)
The same person wrote the documents and the eval questions, which flatters the scores.
1. Ask someone who has worked in a hotel to read `data/raw/` and write 10 questions a guest or staff member might
   really ask, without looking at `eval/questions.jsonl`.
2. Add them to `eval/questions.jsonl` with category `held_out`, without changing the code first.
3. Run the eval in both modes. Report the held-out score separately in the README.

## 3. Click through it yourself (about 15 minutes)
Use the manual test checklist from the release summary on a laptop and a phone, in light and dark mode.

## 4. After deploying
- [x] Live demo at https://hotel-ops-assistant.streamlit.app, linked from the README, case study and profile.
- [ ] Ask 3 questions on the live demo and confirm the How it works page says "keyword-only".
- [ ] Set a monthly spending limit in the Anthropic Console.
- [x] Record the demo video (`python scripts/record_demo.py`, captioned, from the live app) and publish it on the
      portfolio site: https://vamsialladev.github.io/videos/hotel-ops-demo.mp4

## Done when
- [ ] Business case cites a measured baseline
- [ ] Held-out score reported
- [ ] Video link filled in
