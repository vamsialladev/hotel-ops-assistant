"""Scope check: refuse clearly off-topic questions before calling the API.

Works in both retrieval modes:
- keyword-only: no passage shares a single keyword with the question -> out of scope
- hybrid:       no keyword match AND no passage is at least `min_similarity` similar in meaning

The hybrid threshold was tuned on the eval so that no answerable question is blocked (the
"jacket" question has no keyword match but a similarity of 0.47). Anything that passes this
check still goes to Claude, whose prompt refuses questions outside the hotel's documents.
"""

SCOPE_MESSAGE = (
    "I can only help with this hotel's policies, fees, amenities and procedures, and I couldn't find "
    "anything about this in the hotel's documents. If it's a hotel question, please check with a manager."
)

# Shown instead of SCOPE_MESSAGE when the question is in Spanish (Project 4).
SCOPE_MESSAGE_ES = (
    "Solo puedo ayudar con las políticas, tarifas, servicios y procedimientos de este hotel, y no encontré nada "
    "sobre esto en sus documentos. Si es una pregunta sobre el hotel, consulte con un gerente."
)

# Emergencies never wait for the model (Project 4, decision 53): the documents have no readable emergency
# procedure, so the answer is always this message plus the safety manager note, with no API call.
SAFETY_MESSAGE = (
    "This sounds like an emergency. If anyone may be in danger, call emergency services (911) now, follow the "
    "hotel's posted emergency procedures and contact the Manager on Duty. The assistant has no emergency "
    "procedure it can read, so it won't guess."
)
SAFETY_MESSAGE_ES = (
    "Esto parece una emergencia. Si alguien puede estar en peligro, llame ahora a los servicios de emergencia "
    "(911), siga los procedimientos de emergencia publicados del hotel y avise al gerente de turno. El asistente "
    "no tiene ningún procedimiento de emergencia que pueda leer, así que no adivinará."
)


def safety_message(language: str) -> str:
    return SAFETY_MESSAGE_ES if language == "es" else SAFETY_MESSAGE


def scope_message(language: str) -> str:
    return SCOPE_MESSAGE_ES if language == "es" else SCOPE_MESSAGE


def in_scope(signals: dict, min_similarity: float) -> bool:
    if signals["keyword_matches"] > 0:
        return True
    best = signals.get("best_similarity")
    return best is not None and best >= min_similarity
