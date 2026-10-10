"""Policy gaps found while building and evaluating the assistant: things the documents don't
cover, or cover only informally. Shown to managers on the Insights page and listed in
docs/BUSINESS_CASE.md as items to raise with the client. Evidence quotes are checked by a test.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Gap:
    title: str
    detail: str
    evidence: str  # exact text from the source document
    source: str
    suggestion: str


KNOWN_GAPS = (
    Gap(
        title="Credits between $51 and $200 have no rule",
        detail="Front desk may give up to $50 without approval, and the Manager on Duty approves anything over "
        "$200. Nothing says who approves $51 to $200.",
        evidence="Front desk agents may issue courtesy credits up to $50 without approval. "
        "Any refund or credit over $200 must be approved by the Manager on Duty.",
        source="shared/brand_standards.md",
        suggestion="Add one sentence naming the approver for $51-$200 (for example, the front office supervisor).",
    ),
    Gap(
        title="No readable safety or emergency procedure",
        detail="Beach Resort's fire safety document is a scanned image with no text, so it can't be searched. "
        "Mountain Lodge has no safety document at all. The assistant refuses every safety question.",
        evidence="",
        source="beach-resort/fire_safety_scan.pdf",
        suggestion="Provide a text version of the safety procedures for each property (or run OCR on the scan).",
    ),
    Gap(
        title="Early check-in fee exists only in informal staff notes",
        detail="The early check-in fee at Mountain Lodge is written in the front desk notes, not in the "
        "property policy, so it has no effective date and could be changed by anyone.",
        evidence="early check in before 12pm",
        source="mountain-lodge/front_desk_notes.txt",
        suggestion="Move the early check-in rule into Mountain Lodge's property policy.",
    ),
    Gap(
        title="Guest emails pasted into staff notes",
        detail="A pasted guest email in the staff notes contains instructions aimed at an AI assistant "
        "(asking it to waive fees). The assistant ignores it, but notes should not hold guest correspondence.",
        evidence="SYSTEM NOTICE TO THE AI ASSISTANT",
        source="mountain-lodge/front_desk_notes.txt",
        suggestion="Keep guest correspondence out of shared staff notes.",
    ),
)
