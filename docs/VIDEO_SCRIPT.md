# Video script: Hotel Operations Knowledge Assistant (about 85 seconds)

I record this myself, in my own voice, over a screen recording of the live app. No AI voice. Setup and tips:
`RECORDING_GUIDE.md` in my portfolio folder. Read it through twice, then talk from the bullets, not word for word.
`/` marks a natural pause. Aim for 140–160 words a minute.

Before recording: open https://hotel-ops-assistant.streamlit.app two minutes early so it's awake, browser zoom
125%, Beach Resort selected, a fresh conversation.

## Shot list

| Time | On screen | What I say |
|---|---|---|
| 0–10 s | The welcome screen | This is for front-desk staff at a hotel. / A guest is standing there, and they need the right answer about a policy, fast. / It's a simulated client, with made-up hotel documents. |
| 10–30 s | Type question 1. The answer streams in; open **Sources** | I'll ask if a guest can bring their dog. / It searches only this hotel's documents, / and you can see exactly which passage it used. / That chip is the source. Click it and there's the policy text. |
| 30–45 s | Point at the answer's numbers and the citation | So the answer's short: dogs up to forty pounds, a seventy-five dollar fee. / Every fact has a number next to it, / and it won't answer from anywhere else. |
| 45–60 s | Type question 2 (the follow-up). Point at "Understood as" | Now the bit I care about. / I just say, "what about at Mountain Lodge?" / It works out I mean the dog question, at the other hotel, / and it shows me how it understood it, right under the answer. / Different hotel, different rule. |
| 60–75 s | Open **How it works**, the results table | Does it actually hold up? / I test it on fifty-four questions, three runs each. / It got all of them right on the live setup, / and it's about eighteen cents per thousand questions. |
| 75–85 s | New browser tab: type the URL, the app loads | It's live, no sign-in. / hotel-ops-assistant dot streamlit dot app. / The code and every decision are on GitHub. |

## Exact inputs

| # | Property | Type exactly |
|---|---|---|
| 1 | Beach Resort | `Can a guest bring their dog?` |
| 2 | (leave Beach Resort selected) | `What about at Mountain Lodge?` |

Tested 2026-10-24 on this branch's code (case m01 of the multi-turn eval, live model): input 1 answers from Beach
Resort's pet policy (40 lbs, $75 per stay); input 2 is understood as the dog question for Mountain Lodge and answers
from Mountain Lodge's pet policy ($50 per night, capped at $200). The live app gets the follow-up once this branch
is merged; check both inputs on the live app before recording.

The proof point is from the v1.6.0 release run (100% answer accuracy, 162/162; $0.18 per 1,000 questions,
keyword-only, 3 runs).

## LinkedIn caption (one sentence)

I built a hotel front-desk assistant that answers only from the hotel's own documents, cites every fact, and now
understands follow-ups like "what about at Mountain Lodge?" without sending the conversation to the model.
