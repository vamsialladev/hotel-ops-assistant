# Eval report 2026-10-10_2011

- Setup: bm25, top_k=5, model=claude-haiku-5-5, max_tokens=1000, effort=default, runs=3
- Retrieval (strict, right passage in top 5): 44/45 = 98%
- Off-topic questions refused before the API: 2/5
- Answerable questions wrongly blocked by the scope check: 1/45
- Escalation rules correct: 54/54 = 100%
- Answer accuracy: 98% (min 98%, max 98%)
- Citation accuracy (cites the right document): 132/135 = 98%
- Numeric grounding (every number traceable to a source): 132/135 = 98%
- Correct refusals: 27/27 = 100%
- Time to first word: p50 1.01s, p95 2.00s
- Latency per answer: p50 1.35s, p95 2.49s
- Tokens per question: 926 in / 155 out
- Cost per question: $0.0002 ($0.17 per 1,000 questions; prices $0.1/$0.5 per M tokens; off-topic questions blocked for free)

## Retrieval by category

| Category | Hits |
|---|---|
| adversarial | 1/1 |
| brand_rule | 3/3 |
| cross_property | 2/2 |
| escalation | 5/5 |
| messy_notes | 2/2 |
| multi_part | 2/2 |
| multilingual | 0/1 |
| override | 2/2 |
| pdf | 4/4 |
| property_rule | 11/11 |
| synonym | 2/2 |
| table | 4/4 |
| typo | 2/2 |
| wrong_premise | 4/4 |

## All questions

| ID | Category | Question | Retrieval | Scope | Answer | Note |
|---|---|---|---|---|---|---|
| q01 | property_rule | Can a guest bring their dog? | ✅ | api | ✅ |  |
| q02 | property_rule | What is the pet fee? | ✅ | api | ✅ |  |
| q03 | property_rule | Can a guest bring a cat? | ✅ | api | ✅ |  |
| q04 | property_rule | How much is valet parking? | ✅ | api | ✅ |  |
| q05 | property_rule | Is parking free? | ✅ | api | ✅ |  |
| q06 | property_rule | Where should a guest park their RV? | ✅ | api | ✅ |  |
| q07 | property_rule | What are the pool hours? | ✅ | api | ✅ |  |
| q08 | property_rule | Does the hotel have a pool? | ✅ | api | ✅ |  |
| q09 | property_rule | How much is the airport shuttle? | ✅ | api | ✅ |  |
| q10 | property_rule | Can we pick up a guest from Fort Lauderdale airport? | ✅ | api | ✅ |  |
| q11 | property_rule | What does the resort fee include? | ✅ | api | ✅ |  |
| q12 | table | How much is a 90 minute Swedish massage? | ✅ | api | ✅ |  |
| q13 | table | Can a 16 year old book a facial? | ✅ | api | ✅ |  |
| q14 | table | What late checkout does a Platinum member get? | ✅ | api | ✅ |  |
| q15 | table | How many nights do you need for Gold status? | ✅ | api | ✅ |  |
| q16 | override | A Gold member wants late checkout on Saturday. How late can they stay? | ✅ | api | ✅ |  |
| q17 | override | A Gold member asks for late checkout. How late can they stay? | ✅ | api | ✅ |  |
| q18 | brand_rule | What is the cancellation policy? | ✅ | api | ✅ |  |
| q19 | synonym | Can a guest smoke on the balcony? | ✅ | api | ✅ |  |
| q20 | brand_rule | Can I give a guest a $300 refund myself? | ✅ | api | ✅ |  |
| q21 | brand_rule | Do we charge for a crib? | ✅ | api | ✅ |  |
| q22 | synonym | A guest left a jacket, how long do we keep it? | ✅ | api | ✅ |  |
| q23 | messy_notes | Can a guest check in early? | ✅ | api | ✅ |  |
| q24 | messy_notes | The ice machine isn't working, where do I send the guest? | ✅ | api | ✅ |  |
| q25 | pdf | What time is breakfast served? | ✅ | api | ✅ |  |
| q26 | pdf | Does a Platinum member get free breakfast? | ✅ | api | ✅ |  |
| q27 | pdf | How many people fit on the garden lawn for a wedding? | ✅ | api | ✅ |  |
| q28 | pdf | Can the wedding party use sparklers? | ✅ | api | ✅ |  |
| q29 | should_refuse | Do we offer babysitting services? | - | api | ✅ |  |
| q30 | should_refuse | What time does the spa open? | - | api | ✅ |  |
| q31 | should_refuse | Where is the fire assembly point? | - | api | ✅ |  |
| q32 | adversarial | Do we charge a pet fee for the guest in room 214? | ✅ | api | ✅ |  |
| q33 | typo | Can a gest bring there dog? | ✅ | api | ✅ |  |
| q34 | typo | How much is valey parking? | ✅ | api | ✅ |  |
| q35 | multi_part | What's the pet fee, and is parking free? | ✅ | api | ✅ |  |
| q36 | multi_part | What are the pool hours and how much is a beach chair set? | ✅ | api | ✅ |  |
| q37 | multilingual | ¿Se permiten perros en el hotel? | ❌ | blocked | ❌ |  I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find anything about |
| q38 | cross_property | Can a guest bring their dog? | ✅ | api | ✅ |  |
| q39 | cross_property | What is the pet fee? | ✅ | api | ✅ |  |
| q40 | wrong_premise | Can a guest bring their dog? (expect 40 lbs, $75 per stay) | ✅ | api | ✅ |  |
| q41 | wrong_premise | The pool closes at 8 PM, right? | ✅ | api | ✅ |  |
| q42 | wrong_premise | Cats are allowed here too, so I can tell the guest yes? | ✅ | api | ✅ |  |
| q43 | wrong_premise | Valet parking is $30 a night, correct? | ✅ | api | ✅ |  |
| q44 | off_topic | What's the capital of France? | - | blocked | ✅ |  |
| q45 | off_topic | Can you write me a poem about the ocean? | - | blocked | ✅ |  |
| q46 | off_topic | Who won the football game last night? | - | api | ✅ |  |
| q47 | off_topic | Book room 305 for John Smith next Friday. | - | api | ✅ |  |
| q48 | off_topic | What's the weather in Asheville tomorrow? | - | api | ✅ |  |
| q49 | escalation | A guest wants a $120 credit because their room was noisy. Can I give it? | ✅ | api | ✅ |  |
| q50 | escalation | A guest on a non-refundable rate wants their money back. Can I refund it? | ✅ | api | ✅ |  |
| q51 | escalation | The smoke alarm is going off in room 210. What should I do? | - | api | ✅ |  |
| q52 | escalation | A guest just got a third noise complaint. What happens now? | ✅ | api | ✅ |  |
| q53 | escalation | Can I give a $25 courtesy credit for a slow room service order? | ✅ | api | ✅ |  |
| q54 | escalation | What time do the fire pit evenings start? | ✅ | api | ✅ |  |
