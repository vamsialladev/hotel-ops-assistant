# Decision Log

Short records of the important choices, written for the client's engineering team.

## 1. Hybrid search instead of embeddings only
**Context:** Staff ask with exact terms (prices, "AVL", "valet") and with loose phrasing ("smoke" vs "smoking").
**Decision:** BM25 + embeddings, merged with Reciprocal Rank Fusion.
**Tradeoff:** Slightly more code, but it catches both exact-term and meaning-based matches. Keyword-only scored 92% hit@5 and missed the smoking question.

## 2. Filter by property before searching
**Context:** The same question has different correct answers at different hotels.
**Decision:** Each chunk is tagged with its property. Search only sees the selected property plus brand-wide docs.
**Tradeoff:** Staff must select their property. A wrong answer from another hotel is worse than one extra click.

## 3. Exclude superseded documents at ingestion
**Context:** Old policy versions stay in shared folders and contradict current rules.
**Decision:** Docs with `status: superseded` are never indexed.
**Tradeoff:** Requires the hotel to label documents. The runbook (Project 5) covers this process.

## 4. Refuse rather than guess
**Context:** A confidently wrong answer (e.g., "pets are fine") creates guest conflicts.
**Decision:** The model answers only from sources and uses a fixed "couldn't find this" message otherwise.
**Tradeoff:** Some answerable questions may be refused. These are tracked in evals.

## 5. Small, fast model by default
**Context:** Staff use this with a guest waiting, so speed and cost matter more than eloquence.
**Decision:** Default to Claude Haiku; the model can be changed in `.env`.
**Tradeoff:** Revisit in Project 4 with cost and latency measurements.

## 6. Mask digits when detecting repeated PDF headers/footers
**Context:** Footers like "Page 1 of 3" differ on every page, so they were leaking into chunks.
**Decision:** Compare lines with digits replaced by `#`. Lines repeated on 60%+ of pages are removed.
**Tradeoff:** A genuinely repeated line, such as the same price on most pages, could be removed. This is unlikely, and a unit test covers the expected behavior.

## 7. Domain stopwords for keyword search
**Context:** After renaming the loyalty program to "Guest Rewards", keyword hit@5 dropped from 93% to 86%. Questions like "Can a guest bring their dog?" matched loyalty docs on the word "guest".
**Decision:** Ignore "guest", "guests", "hotel" and "hotels" in keyword search, because they appear in nearly every document.
**Result:** On its own, this made things worse (82%), which revealed the real cause (decision 8). After stemming, the stopwords made no measurable difference. I kept them because they're cheap and logically correct.
**Tradeoff:** The list is hand-made and specific to this domain.

## 8. Light stemming for keyword search
**Context:** The eval showed keyword search failing on word forms: "cat"/"cats", "RV"/"RVs", "smoke"/"smoking", "crib"/"cribs". Some of these questions had only passed before by luck, through the shared word "guest".
**Decision:** A small rule-based stemmer (plurals, -ing, trailing -e) applied to both documents and questions.
**Tradeoff:** Simple rules occasionally merge unrelated words. That's acceptable for short policy documents, and the eval catches regressions. Embeddings in hybrid mode cover the remaining synonym cases (e.g. "jacket" → "lost and found").

## 9. Strict, passage-level retrieval evaluation
**Context:** The eval counted a hit if the right *document* appeared anywhere in the top 5. A Spanish question with zero keyword matches still passed, because every passage scored 0 and the right document came first in file order.
**Decision:** Each question names a distinctive phrase (e.g. "up to 40 lbs") that must appear in a retrieved passage from the expected document. Multi-part questions list one phrase per part.
**Result:** The honest score is 94% (32/34) instead of an inflated number. The metric now matches what staff actually need: the passage with the answer.

## 10. Never return passages that match nothing
**Context:** In keyword-only mode, a question with no matching words returned 5 arbitrary passages.
**Decision:** The keyword ranking only includes passages with a score above zero. If nothing is found, the app refuses without calling the API.
**Tradeoff:** In keyword-only mode, some foreign-language questions get a refusal instead of a lucky answer. That's the safer failure. Hybrid search adds meaning-based matches.

## 11. Treat document text as data, not instructions
**Context:** Staff notes can contain pasted guest emails. A test note tells the AI to waive pet and parking fees, and it ranks first for a pet-fee-and-parking question.
**Decision:** The prompt states that sources are reference data and instructions inside them must be ignored. The eval includes this attack and fails any answer containing "are waived".
**Tradeoff:** Prompt rules reduce but don't eliminate injection risk. Project 4 adds screening of new documents before indexing.

## 12. Deterministic answer checks before an LLM judge
**Context:** Checking only that an answer contains "40" misses invented numbers and wrong citations.
**Decision:** Added citation accuracy and numeric grounding (every number in the answer must appear in a cited source or in the question). Both are plain code, unit-tested, cost nothing, and give the same result every time.
**Tradeoff:** They can't judge meaning (e.g. a wrong "yes" with no numbers). Project 3 adds an LLM judge, checked against human labels.
