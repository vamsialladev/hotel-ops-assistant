# Business Case

> **These are projections from stated assumptions, not measured results.** This is a simulated engagement. A real pilot would replace each assumption with a measurement (see "How to validate").

## The problem in business terms
Front-desk staff answer policy questions all day: pets, late checkout, parking, fees, events. The answers are spread across PDFs, menus, brand standards and staff notes, and they differ by property. This causes three costs:

1. **Staff time:** searching documents or asking a manager while a guest waits.
2. **Wrong answers:** a guest is promised something the policy doesn't allow, and the hotel gives a refund or comp to recover.
3. **Inconsistency:** different answers on different shifts, which hurts guest reviews and slows down new-hire training.

## Assumptions (per property)
| Assumption | Value | Why this number |
|---|---|---|
| Policy lookups per day | 40 | Roughly 2–3 per hour across shifts at a mid-size hotel |
| Minutes saved per lookup | 2.5 | Searching documents or finding a manager vs. a 10-second answer |
| Front-desk cost per hour | $20 | Typical US front-desk wage plus overhead |
| Wrong answers per week that lead to a refund or comp | 1 | Conservative |
| Average refund or comp | $75 | Partial night credit, waived fee, or F&B voucher |
| AI cost per question | $0.0002 | **Measured**, not assumed: $0.16 per 1,000 questions keyword-only and $0.18 hybrid with Claude Haiku 5.5 on the 54-question eval (rounded up) |

## Projected results
| | 2 properties (this engagement) | 100-property group |
|---|---|---|
| Staff hours saved per year | 1,217 | 60,833 |
| Value of staff time | $24,333 | $1,216,667 |
| Fewer refunds from wrong answers | $7,800 | $390,000 |
| **Total projected value per year** | **$32,133** | **$1,606,667** |
| Running cost per year | $246 | $15,292 (includes $15K hosting and support) |
| **Net value per year** | **$31,887** | **$1,591,375** |

## Sensitivity: pessimistic, base and optimistic
A single number hides uncertainty, so here is a range. Only the three most uncertain assumptions change; wage, refund size and AI cost stay the same.

| Scenario | Lookups/day | Minutes saved | Wrong answers/week | Net value, 2 properties | Net value, 100 properties |
|---|---|---|---|---|---|
| Pessimistic | 20 | 1.0 | 0.5 | $8,524 | $423,187 |
| **Base** | **40** | **2.5** | **1.0** | **$31,887** | **$1,591,375** |
| Optimistic | 60 | 3.5 | 2.0 | $66,451 | $3,319,562 |

Even the pessimistic case returns many times its running cost. The AI cost is now measured rather than assumed;
at $0.0002 per question it is a rounding error next to staff time, so the case rests on **minutes saved per lookup**. The result is most sensitive to **minutes saved per lookup**, so that is the first thing a pilot should measure.

Run it yourself and change any assumption:
```bash
python scripts/business_case.py
python scripts/business_case.py --properties 100 --hosting 15000
python scripts/business_case.py --scenarios --properties 100 --hosting 15000
```

## Policy gaps to raise with the client
Found while building and evaluating the assistant (also shown to managers on the app's Insights page). Each one is
a decision for the hotel group, not something the assistant should guess.

| Gap | Evidence | Suggested fix |
|---|---|---|
| **Credits between $51 and $200 have no rule.** Front desk may give up to $50 without approval and the Manager on Duty approves anything over $200; nothing names the approver in between. | Hotel Group Brand Standards › Refunds and Escalation | Add one sentence naming the approver for $51–$200 (for example, the front office supervisor). Until then the assistant shows "Check with a manager" for any credit over $50. |
| **No readable safety or emergency procedure.** Beach Resort's fire safety procedure is a scanned image with no text; Mountain Lodge has none. | Beach Resort fire safety procedure (scan) | Provide a text version for each property, or run OCR on the scan. |
| **Early check-in fee exists only in informal staff notes.** It has no effective date and no owner. | Mountain Lodge front desk notes | Move the rule into the Mountain Lodge property policy. |
| **Guest emails pasted into staff notes.** One contains instructions aimed at an AI ("waive all fees"). | Mountain Lodge front desk notes | Keep guest correspondence out of shared staff notes. |

## Value that isn't in the numbers
- **Faster onboarding:** new hires get correct answers on day one.
- **Consistency:** the same answer on every shift, with the source shown.
- **Fewer manager interruptions** for routine questions.
- **Policy gaps become visible:** questions the system refuses show which policies are missing.

## How to validate in a real pilot (2 weeks, 1 property)
| Measure | How |
|---|---|
| Lookup time | Time 20 lookups before (manual) and after (assistant) |
| Usage | Count questions per day from app logs |
| Accuracy | A manager reviews 50 random answers |
| Refused questions | Review weekly; each one is a missing or unclear policy |
| Staff satisfaction | 3-question survey at the end of the pilot |

## Success metrics and go / no-go criteria
Agreed before the pilot starts, so the decision isn't made after seeing the results.

| KPI | Target to continue | How it's measured |
|---|---|---|
| Answer accuracy (manager review of 50 answers) | 95% or higher | Weekly review sheet |
| Wrong answers that reached a guest | 0 serious, 2 or fewer minor | Front-desk incident log |
| Median time to answer | Under 15 seconds (vs. measured manual baseline) | Timed sample of 20 lookups |
| Daily active staff | 70% or more of front-desk staff by week 2 | App logs |
| Helpful rating | 80% or more thumbs-up | In-app feedback buttons |
| Refusal rate | Under 15%, with each refusal reviewed | App logs |

**Go:** all targets met → expand to all shifts, then to the second property.
**Fix and re-test:** accuracy or adoption below target → review refusals and feedback, update documents or retrieval, run 1 more week.
**Stop:** any serious wrong answer reaches a guest and the cause can't be fixed within the pilot.

## Risks
| Risk | Mitigation |
|---|---|
| Staff don't trust it | Every answer shows its source; start with one shift |
| Policies go out of date | Documents have an effective date and status; outdated versions are excluded |
| A wrong answer reaches a guest | Refuses rather than guesses; evaluated on every change; sensitive topics (refunds, safety) point to a manager |
