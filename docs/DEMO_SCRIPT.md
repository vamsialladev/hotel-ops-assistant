# 2-Minute Demo Script

The published demo video follows this script exactly: `python scripts/record_demo.py` drives the **live app** with
real questions and adds burned-in captions and a WebVTT captions track. It has no voice (decision 58). The video
I record in my own voice follows `docs/VIDEO_SCRIPT.md`; the lines below match this screen recording.
**Bold** lines are what happens on screen.

Published video: https://vamsialla.com/videos/hotel-ops-demo.mp4 (embedded on the
[case study](https://vamsialla.com/projects/hotel-ops-assistant.html#demo)).

---

## 0:00 · Title card (3 s)
**On screen: "Hotel Operations Knowledge Assistant · Vamsi Alla · Simulated client engagement · synthetic hotel documents".**

"Hotel Operations Knowledge Assistant: a simulated client project."

## 0:03 · A cited answer within 10 seconds
**Beach Resort welcome screen. Click the good-question example "Can a guest bring their dog?". The answer streams in with its source chip and related questions.**

"A front-desk agent at Beach Resort asks if a guest can bring their dog. In seconds, a short answer appears, with the source for every fact."

## 0:13 · Same question, other hotel
**Switch to Mountain Lodge and click the same example.**

"At Mountain Lodge, the same question gets that hotel's own rules. It never mixes up properties, and related questions are one tap away."

## 0:22 · A property rule beats a brand perk
**Back to Beach Resort. Type "A Gold member wants late checkout on Saturday. How late can they stay?" Open "Sources".**

"Here, the loyalty program promises a two p.m. checkout, but this hotel caps weekends at noon. The assistant applies the hotel's rule and shows the exact text."

## 0:36 · Check with a manager
**Type "Can I give a guest a $300 refund myself?"**

"A refund over the front-desk limit gets a check-with-a-manager note, quoting the policy."

## 0:46 · Refuses instead of guessing
**Type "Where is the fire assembly point?"**

"When the documents don't say, it refuses instead of guessing. A wrong safety answer is worse than none."

## 0:54 · Never a dead end
**Type "Can you book me a room for Friday?" The reply says it can't answer from the hotel's documents and shows "Did you mean" questions and topic chips.**

"And instead of a dead end, it suggests close questions it can answer."

## 1:02 · Guidance on what to ask
**Click "New conversation" in the sidebar. The welcome screen returns: How to use, What this demo knows, good questions.**

"Every new conversation starts with guidance: how to use it, what this demo knows, and good questions to ask."

## 1:09 · Topic chips
**Click the "Spa" topic chip: example questions appear.**

"Topic chips show example questions for each area, like the spa."

## 1:13 · What managers see
**Open Insights and scroll: how people ask, most-used topics, possible policy gaps.**

"Managers see what staff ask, how they ask, and which questions point to gaps in the policies."

## 1:20 · The documents
**Open the Document library.**

"Every answer comes only from these documents, all synthetic, for a simulated client."

## 1:26 · Proof it works
**Open How it works: key results read from the latest eval report.**

"It's measured on fifty-four test questions: ninety-eight percent answer accuracy on this live demo, at about seventeen cents per thousand questions."

## 1:35 · End card (6 s)
**On screen: portfolio, live app and GitHub links.**

"Try the live app, or read the code and the decisions. The links are on screen."

---

**Re-record after a UI change:** `python scripts/record_demo.py --web-out ../vamsi-portfolio/videos/hotel-ops-demo.mp4`
(6 real questions on the live app), then commit the new video, poster and `.vtt` in the portfolio repo.
