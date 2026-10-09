# Validation Checklist

These steps need a real API key and a person, so they can't run in CI. Each one replaces an assumption or a blank in the README with a real, measured number. Record results in the README and in [ENGINEERING_LOG.md](ENGINEERING_LOG.md).

## 1. Hybrid search and answer quality (about 15 minutes, a few cents)
```bash
python -m src.ingest                      # builds the index with embeddings
python -m eval.run_eval                   # hybrid retrieval score
python -m eval.run_eval --answers --runs 3 --price-in <USD per M input tokens> --price-out <USD per M output tokens>
```
Look up the current model prices on the Anthropic pricing page.
**Fill in:** the Hybrid row of the README Scores table: retrieval, answer accuracy (mean and range), citation accuracy, numeric grounding, p95 latency, cost per 1,000 questions.
**Check in particular:** the Spanish question, the "jacket" question, and that the prompt-injection question never says fees are waived.

## 2. Manual baseline for the business case (about 20 minutes)
1. Pick 10 questions from `eval/questions.jsonl`.
2. **Without the app:** open the documents in `data/raw/` and time how long each answer takes you to find. Use a phone stopwatch.
3. **With the app:** time the same 10 questions.
4. Run the calculator with your measured minutes saved:
   ```bash
   python scripts/business_case.py --minutes-saved <your measured number>
   ```
**Fill in:** a line in BUSINESS_CASE.md under Assumptions: "Measured on 10 questions: manual X s, assistant Y s."

Be honest that it's a small, self-run test. It's still far better than a pure assumption.

## 3. Held-out questions (about 30 minutes)
You wrote the documents and the questions, which biases the eval.
1. Ask someone who has worked in a hotel to read `data/raw/` and write 10 questions a guest or staff member might really ask, without looking at `eval/questions.jsonl`.
2. Add them to `eval/questions.jsonl` with category `held_out`, without changing the code first.
3. Run the eval. Report the held-out score separately in the README.

If nobody is available, write 10 yourself *now*, before changing anything else, and label them that way.

## 4. Real app check (about 10 minutes)
Run `streamlit run app.py` and go through the 9-question checklist from the Windows guide. Use the 👍 / 👎 buttons, then confirm `data/feedback.jsonl` was written. Capture the screenshots listed in [images/README.md](images/README.md).

## Done when
- [ ] No `_fill in_` left in the README
- [ ] Business case cites a measured baseline
- [ ] Held-out score reported
- [ ] App screenshots and demo GIF added
