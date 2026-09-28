"""
NLP preprocessing service.
Provides tokenization, stopword removal, and a full normalization pipeline.
Uses NLTK for basic text processing (Milestone 1 — no ML/AI).
"""

import re
from typing import List

EXTRA_STOPWORDS = {
    "app", "application", "please", "turn", "bring", "getting", "waste", "also", "even",
    "using", "used", "make", "giving", "give", "much", "many", "good", "bad", "like",
    "need", "want", "would", "could", "should", "thing", "things", "instagram", "facebook",
    "whatsapp", "meta", "really", "always", "every", "cant", "cannot", "dont", "doesnt",
    "wont", "didnt", "got", "get", "still", "back", "time", "one", "two", "see", "seen",
    "features", "feature", "enhancement", "option", "options"
}

# Import NLTK resources — these will be downloaded on first use
try:
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    STOPWORDS_SET = set(stopwords.words('english')).union(EXTRA_STOPWORDS)
    NLTK_AVAILABLE = True
except LookupError:
    # NLTK data not downloaded yet — will download on first call
    STOPWORDS_SET = set(EXTRA_STOPWORDS)
    NLTK_AVAILABLE = False


def _ensure_nltk_downloaded() -> None:
    """
    Ensure required NLTK data packages are downloaded.
    Called lazily on first use.
    """
    global STOPWORDS_SET, NLTK_AVAILABLE
    if not NLTK_AVAILABLE:
        import nltk
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        STOPWORDS_SET = set(stopwords.words('english')).union(EXTRA_STOPWORDS)
        NLTK_AVAILABLE = True



def tokenize(text: str) -> List[str]:
    """
    Split text into individual tokens (words).
    Uses NLTK word_tokenize for proper tokenization.
    Falls back to simple regex splitting if NLTK is unavailable.
    """
    if not text or not isinstance(text, str):
        return []

    _ensure_nltk_downloaded()

    try:
        tokens = word_tokenize(text)
        # Keep only alphanumeric tokens
        tokens = [t for t in tokens if t.isalnum()]
        return tokens
    except Exception:
        # Fallback: simple whitespace + punctuation split
        tokens = re.findall(r'[a-z0-9]+', text.lower())
        return tokens


def remove_stopwords(tokens: List[str]) -> List[str]:
    """
    Remove common English stopwords from a list of tokens.
    Uses NLTK's English stopword list.
    """
    if not tokens:
        return []

    _ensure_nltk_downloaded()

    return [token for token in tokens if token.lower() not in STOPWORDS_SET]


def normalize(text: str) -> List[str]:
    """
    Full normalization pipeline:
    1. Clean text (lowercase, remove special chars, strip whitespace)
    2. Tokenize
    3. Remove stopwords
    Returns a list of clean tokens.
    """
    if not text or not isinstance(text, str):
        return []

    # Step 1: Basic text cleaning
    cleaned = text.lower().strip()
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Step 2: Tokenize
    tokens = tokenize(cleaned)

    # Step 3: Remove stopwords
    filtered = remove_stopwords(tokens)

    return filtered
