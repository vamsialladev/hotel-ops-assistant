# 2-Minute Demo Script

Record your screen (OBS or Loom) with the app open at about 1280 px wide, light mode, on a fresh session.
Before recording: start the app, open the Assistant page, and close other tabs. Speak slowly; the words below
take about 2 minutes at a calm pace. **Bold** lines are what you do; the rest is what you say, word for word.

---

## 0:00 – 0:15 · The problem
**On screen: the Assistant welcome screen, Beach Resort selected.**

"Front-desk staff at a two-hotel group answer the same policy questions all day: pets, late checkout, refunds. The rules live in PDFs, menus and staff notes, and they're different at each hotel. This is a simulated client engagement with synthetic documents, but the problem is real."

## 0:15 – 0:40 · Same question, two hotels
**Click the sample "Can a guest bring their dog?". Let it stream.**

"I ask in plain English, and the answer streams in a second later. Beach Resort: dogs up to 40 pounds, 75 dollars per stay. Every fact has a citation, and this chip shows which document it came from and when that policy took effect."

**Switch to Mountain Lodge. Click the same sample question.**

"Same question at the Mountain Lodge: any size, 50 dollars a night, capped at 200. Each hotel keeps its own conversation, and it never sees the other hotel's rules."

## 0:40 – 1:00 · Overrides and wrong facts
**Switch back to Beach Resort. Type: "A Gold member wants late checkout on Saturday. How late can they stay?" Open "Sources".**

"Here the loyalty program says 2 PM, but this hotel caps weekends at noon. The assistant knows the property rule wins, says so, and shows me the exact text."

**Switch to Mountain Lodge. Type: "Can a guest bring their dog? (expect 40 lbs, $75 per stay)".**

"And if I bring the wrong number myself, it corrects me instead of agreeing."

## 1:00 – 1:20 · Knowing its limits
**Switch to Beach Resort. Type: "Can I give a guest a $300 refund myself?"**

"Refunds over the front-desk limit get a 'check with a manager' note, quoting the actual rule."

**Type: "Where is the fire assembly point?"**

"And when the documents don't say, it refuses. The only safety document here is a scanned image, and a wrong safety answer is worse than no answer."

## 1:20 – 1:40 · What managers see
**Open Insights, then scroll to Known policy gaps.**

"Managers see what staff ask and which questions the documents couldn't answer. While building this I found real gaps, like credits between 51 and 200 dollars that no rule covers. That's a conversation for the client, not something the AI should guess."

## 1:40 – 2:00 · Proof it works
**Open How it works and pause on Key results, then the model comparison.**

"Fifty-four test questions run on every change, including a prompt-injection attack hidden in the staff notes. The live demo scores 96 percent on answers, about two and a half seconds for a full answer, and 17 cents per thousand questions. The eval also caught my own grader passing a wrong answer, so I fixed the measurement first. Everything is on GitHub, with the decisions behind it."

---

**After recording:** keep the video under 2:15, add captions and upload it. Then add its link where the README and the case study page have a commented-out video link (search for `VIDEO:`).
