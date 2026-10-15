"""Which language a question is written in: 'es' (Spanish) or 'en'. Deterministic and free (no API call).

Project 2's detector needs at least three Spanish words, which a short front-desk question rarely has
("¿Cuánto cuesta el estacionamiento?" has one). This one also counts Spanish punctuation, accented letters and
common question words, and is scaled for short text. Unit tests cover both directions, including English
questions with Spanish loan words ("Is the plaza open?").
"""

import re
import unicodedata

SPANISH_WORDS = re.compile(
    r"\b(el|la|los|las|del|que|qué|por|para|con|una|un|su|sus|usted|ustedes|hay|es|son|está|están|se|en|"
    r"cuánto|cuanto|cuánta|cuántos|cuántas|cómo|como|dónde|donde|cuándo|cuando|puedo|puede|pueden|podemos|"
    r"tiene|tienen|tenemos|hola|gracias|reserva|habitación|habitacion|huésped|huesped|huéspedes|"
    r"precio|cuesta|tarifa|hora|abre|cierra|incluye|incluido|permiten|permite|mascotas?|perros?|gatos?|"
    r"desayuno|piscina|salida|llegada|noche|noches|también|muy|si|sí|mi|nuestra|nuestro|al|lo|le|les|hacemos)\b",
    re.I,
)
SPANISH_MARKS = re.compile(r"[¿¡ñáéíóú]", re.I)
ENGLISH_WORDS = re.compile(
    r"\b(the|is|are|what|how|much|does|do|can|guest|room|time|where|when|have|has|and|of|to|for|with|"
    r"there|our|we|i|you|my|a|an|in|on|at|it|this|that|be|will|should)\b",
    re.I,
)

LANGUAGE_NAMES = {"en": "English", "es": "Spanish"}


def detect_language(text: str) -> str:
    text = text or ""
    words = re.findall(r"\w+", text)
    if not words:
        return "en"
    spanish = len(SPANISH_WORDS.findall(text)) + (1 if SPANISH_MARKS.search(text) else 0)
    english = len(ENGLISH_WORDS.findall(text))
    return "es" if spanish >= 2 and spanish > english else "en"


def fold(text: str) -> str:
    """Lowercase without accents: 'Habitación' -> 'habitacion'. Used for accent-insensitive matching."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
