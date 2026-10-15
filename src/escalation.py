"""'Check with a manager' rules, taken from the hotel's own documents.

Each rule quotes the document line that justifies it, word for word (a unit test checks the
quote still appears in the source file). Triggers are deterministic checks on the question,
so the same question always gets the same note, with no extra API call.
"""

import re
from dataclasses import dataclass

from src.retrieve import fold_accents

COURTESY_LIMIT = 50  # brand_standards.md: credits up to $50 without approval
MANAGER_LIMIT = 200  # brand_standards.md: over $200 needs the Manager on Duty


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    message: str
    quote: str | None  # exact sentence from the source document, or None when the rule is about a missing document
    source: str  # document path under data/raw, or a description of what is missing
    properties: tuple[str, ...] = ()  # empty = every property
    source_label: str | None = None  # shown instead of the document name when the rule is about a gap


REFUND_OVER_LIMIT = Rule(
    id="refund_over_limit",
    title="Check with a manager: refund or credit over the front-desk limit",
    message="Front desk can only issue credits up to $50 on its own. Over $200 needs the Manager on Duty, "
    "and the documents don't cover amounts in between, so check with a manager before promising anything.",
    quote="Front desk agents may issue courtesy credits up to $50 without approval. "
    "Any refund or credit over $200 must be approved by the Manager on Duty.",
    source="shared/brand_standards.md",
)
NONREFUNDABLE_EXCEPTION = Rule(
    id="nonrefundable_exception",
    title="Check with a manager: non-refundable rate",
    message="Only the General Manager can approve an exception on a non-refundable rate.",
    quote="Non-refundable rate: no refunds or date changes under any circumstances, "
    "except when approved by the General Manager.",
    source="shared/brand_standards.md",
)
NOISE_REMOVAL = Rule(
    id="noise_removal",
    title="Check with a manager: repeated noise complaints",
    message="Asking a guest to leave is the Manager on Duty's decision.",
    quote="After a third complaint, the guest may be asked to leave without a refund (Manager on Duty decision).",
    source="mountain-lodge/policies.md",
    properties=("mountain-lodge",),
)
SAFETY = Rule(
    id="safety",
    title="Check with a manager: safety or emergency",
    message="No safety or emergency procedure can be read by the assistant: the only safety document is a "
    "scanned image that hasn't been converted to text. Contact the Manager on Duty and follow the hotel's "
    "posted emergency procedures.",
    quote=None,
    source="beach-resort/fire_safety_scan.pdf",
    source_label="Beach Resort fire safety procedure (scanned, not readable yet); Mountain Lodge has none",
)
REFUSED = Rule(
    id="refused",
    title="Check with a manager",
    message="The hotel's documents don't answer this, so the assistant won't guess.",
    quote=None,
    source="",
    source_label="No matching policy in the hotel's documents",
)

RULES = (REFUND_OVER_LIMIT, NONREFUNDABLE_EXCEPTION, NOISE_REMOVAL, SAFETY)

MONEY_BACK = re.compile(r"\b(refund\w*|credit\w*|comp|comps|comped|compensat\w*|money back|reimburs\w*)\b", re.I)
AMOUNT = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)|\b(\d[\d,]*(?:\.\d{1,2})?)\s?(?:dollars|usd)\b", re.I)
NONREFUNDABLE = re.compile(r"\bnon[- ]?refundable\b", re.I)
NOISE = re.compile(r"\b(noise|noisy|loud|quiet hours)\b", re.I)
# "fire pit" is an amenity and "smoke on the balcony" is a smoking-policy question, not emergencies.
SAFETY_TERMS = re.compile(
    r"\b(fire(?!\s*pits?\b)|evacuat\w*|emergenc\w*|assembly point|smoke (?:alarm|detector)s?|fire alarm|"
    r"alarm is going off|injur\w*|ambulance|medical|first aid|gas leak|flood\w*|earthquake|hurricane|"
    r"tornado|bomb|threat\w*|weapon\w*|intruder|active shooter|cardiac|unconscious)\b",
    re.I,
)
# Project 4 (decision 52): paraphrases staff actually type, and Spanish. Matched on accent-free lowercase text, so
# "incendio", "sangrando" and "se desmayó" match with or without accents. Smoking-policy words ("smoke on the
# balcony", "fumar") are deliberately absent; a test runs every non-safety question in the evals through this and
# requires zero false alarms.
SAFETY_PARAPHRASES = re.compile(
    r"\b(smoke (?:is )?(?:coming|pouring|filling|from|under|in the (?:hall\w*|corridor|kitchen|lobby|room|stair\w*))|"
    r"smell(?:s|ing)? (?:of )?(?:smoke|gas|burning)|burning smell|on fire|flames?|carbon monoxide|co alarm|"
    r"not breathing|stopped breathing|(?:isn['’]?t|is not|not) responding|unresponsive|collapsed|passed out|fainted|"
    r"bleeding|seizure|heart attack|chest pains?|choking|overdose|allergic reaction|anaphyla\w*|drowning|"
    r"stuck in (?:the|an) (?:elevator|lift)|trapped|call 911|police|"
    # Spanish
    r"incendio\w*|fuego|humo|en llamas|alarma de incendio|emergencia\w*|evacua\w*|ambulancia|herid[oa]s?|"
    r"lesion\w*|sangr\w*|inconsciente|desmay\w*|no respira|ataque (?:cardiaco|al corazon)|convulsion\w*|"
    r"fuga de gas|(?:olor a|huele a) (?:gas|humo|quemado)|inundacion|terremoto|amenaza\w*|armas?|urgencias|"
    r"primeros auxilios|policia|"
    # French (a few, the most common)
    r"incendie|fumee|urgence|blesse\w*)\b"
)


def is_safety(question: str) -> bool:
    return bool(SAFETY_TERMS.search(question) or SAFETY_PARAPHRASES.search(fold_accents(question)))


def amounts(question: str) -> list[float]:
    out = []
    for a, b in AMOUNT.findall(question):
        out.append(float((a or b).replace(",", "")))
    return out


def escalations(question: str, prop: str, refused: bool = False) -> list[Rule]:
    """Rules that apply to this question at this property, most important first."""
    found = []
    if is_safety(question):
        found.append(SAFETY)
    if MONEY_BACK.search(question) or NONREFUNDABLE.search(question):
        if NONREFUNDABLE.search(question):
            found.append(NONREFUNDABLE_EXCEPTION)
        if any(x > COURTESY_LIMIT for x in amounts(question)):
            found.append(REFUND_OVER_LIMIT)
    if NOISE.search(question) and (not NOISE_REMOVAL.properties or prop in NOISE_REMOVAL.properties):
        found.append(NOISE_REMOVAL)
    if refused and not found:
        found.append(REFUSED)
    return found


def escalation_ids(question: str, prop: str) -> list[str]:
    """Question-only rule ids (no refusal rule): what the eval compares against."""
    return [r.id for r in escalations(question, prop)]


RULES_BY_ID = {r.id: r for r in (*RULES, REFUSED)}
