# 2-Minute Demo Script

Record your screen (Loom or OBS) with the Streamlit app open. Speak to a hotel manager first, then an engineer.

## 0:00 - The problem (15s)
"Front-desk staff at a 2-property hotel group answer the same policy questions all day. The rules live in PDFs, menus, and staff notes, and they're different at each hotel. Wrong answers mean upset guests."

## 0:15 - Property-specific answer (25s)
Select **beach-resort**, ask: *Can a guest bring their dog?* → 40 lbs, $75 per stay.
Switch to **mountain-lodge**, ask the same → any size, $50/night.
"Same question, different hotel, different correct answer, each with its source."

## 0:40 - The override (20s)
**beach-resort**: *A Gold member wants late checkout on Saturday. How late can they stay?*
"The loyalty program says 2 PM, but Miami caps weekends at noon. The assistant knows property rules win, and says so."

## 1:00 - Messy data (20s)
**mountain-lodge**: *Can a guest check in early?* → found in an informal staff notes file.
**beach-resort**: *What time is breakfast served?* → found in a multi-page PDF.
Mention: the old 2024 policy that says "no pets" is never used.

## 1:20 - It refuses instead of guessing (15s)
**beach-resort**: *Where is the fire assembly point?*
"That document is a scanned image. The system flags it for OCR instead of guessing. A wrong safety answer is worse than no answer."

## 1:35 - Proof it works (25s)
Show `eval/reports/` and the CI badge.
"37 test questions run on every commit, including a prompt-injection attack hidden in the staff notes. The eval also caught my own metric being too lenient, so I made it strict: the exact passage has to be found. Here are the numbers."
