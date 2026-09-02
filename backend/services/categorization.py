"""
Rule-based categorization and sentiment detection service.
Uses keyword matching to classify feedback — no ML/AI in Milestone 1.
"""

from typing import Tuple, Dict, Any, List
from database import db
from services.preprocessing import normalize


# Keyword-to-category mapping for rule-based classification
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "bug_report": [
        "bug", "crash", "error", "broken", "fails", "fail", "exception",
        "not working", "doesnt work", "doesn't work", "frozen", "freeze",
        "glitch", "defect", "issue", "wrong", "incorrect", "unexpected",
        "unresponsive", "stuck", "hang", "corrupt", "corrupted", "404",
        "500", "timeout", "refused", "segfault", "overflow", "null pointer",
    ],
    "feature_request": [
        "feature", "wish", "add", "would like", "could you", "please add",
        "suggestion", "improve", "enhancement", "request", "want",
        "need", "missing", "it would be great", "it would be nice",
        "would be helpful", "support for", "ability to", "option to",
        "can we", "is there a way", "how about", "would love",
    ],
    "performance_issue": [
        "slow", "lag", "performance", "speed", "delay", "latency",
        "loading", "takes too long", "unresponsive", "memory", "cpu",
        "battery", "heating", "overheating", "choppy", "framerate",
        "fps", "bandwidth", "optimize", "heavy", "resource",
    ],
}

# Keywords for sentiment detection
POSITIVE_KEYWORDS: List[str] = [
    "great", "excellent", "amazing", "love", "awesome", "fantastic",
    "good", "nice", "perfect", "wonderful", "best", "brilliant",
    "helpful", "easy", "smooth", "fast", "reliable", "recommend",
    "thank", "thanks", "pleased", "satisfied", "impressed",
    "enjoy", "enjoying", "happy", "delighted", "superb", "outstanding",
]

NEGATIVE_KEYWORDS: List[str] = [
    "bad", "terrible", "awful", "worst", "hate", "horrible",
    "poor", "disappointing", "disappointed", "frustrating", "frustrated",
    "annoying", "annoyed", "useless", "waste", "broken", "slow",
    "crash", "error", "fail", "bug", "painful", "unacceptable",
    "unusable", "rage", "angry", "upset", "sucks", "garbage",
    "refund", "uninstall", "delete", "never again",
]


def categorize(text: str) -> str:
    """
    Determine the category of feedback based on keyword matching.
    Checks text against predefined keyword lists for each category.
    Returns the first matching category, or 'general_feedback' if no match.
    """
    if not text:
        return "general_feedback"

    # Normalize the text for matching
    tokens = set(normalize(text))
    text_lower = text.lower()

    # Check each category's keywords against the text
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            # For multi-word keywords, check if they appear in the text
            if " " in keyword:
                if keyword in text_lower:
                    return category
            else:
                # For single-word keywords, check both tokens and substring match
                if keyword in tokens or keyword in text_lower:
                    return category

    return "general_feedback"


def detect_sentiment(text: str, rating: int = None) -> str:
    """
    Detect the sentiment of feedback.
    Priority: rating-based > keyword-based > default neutral.

    Rating logic:
      - 4-5 → positive
      - 3   → neutral
      - 1-2 → negative

    Keyword logic (when no rating):
      - Count positive and negative keyword matches
      - If more positive → positive, more negative → negative, else neutral
    """
    # If rating is available, use it as the primary signal
    if rating is not None:
        if rating >= 4:
            return "positive"
        elif rating == 3:
            return "neutral"
        else:
            return "negative"

    # No rating — fall back to keyword analysis
    if not text:
        return "neutral"

    tokens = set(normalize(text))
    text_lower = text.lower()

    # Count positive keyword matches
    positive_count = 0
    for keyword in POSITIVE_KEYWORDS:
        if " " in keyword:
            if keyword in text_lower:
                positive_count += 1
        else:
            if keyword in tokens or keyword in text_lower:
                positive_count += 1

    # Count negative keyword matches
    negative_count = 0
    for keyword in NEGATIVE_KEYWORDS:
        if " " in keyword:
            if keyword in text_lower:
                negative_count += 1
        else:
            if keyword in tokens or keyword in text_lower:
                negative_count += 1

    # Determine sentiment from keyword counts
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


async def batch_categorize(workspace_id: str) -> Dict[str, int]:
    """
    Process all uncategorized feedback in a workspace.
    For each uncategorized record:
    1. Determine category using rule-based keywords
    2. Detect sentiment using rating and/or keywords
    3. Update the record in the database

    Returns counts of processed and updated records.
    """
    # Find all feedback in this workspace that hasn't been categorized yet
    cursor = db.feedback.find(
        {
            "workspace_id": workspace_id,
            "category": None,
        }
    )
    records = await cursor.to_list(length=None)

    processed = 0
    updated = 0

    for record in records:
        processed += 1
        record_id = record["_id"]
        content = record.get("content", "")
        title = record.get("title", "")
        rating = record.get("rating")

        # Combine title and content for better categorization
        combined_text = f"{title} {content}".strip()

        # Determine category
        category = categorize(combined_text)

        # Determine sentiment
        sentiment = detect_sentiment(combined_text, rating)

        # Update the record in the database
        result = await db.feedback.update_one(
            {"_id": record_id},
            {
                "$set": {
                    "category": category,
                    "sentiment": sentiment,
                }
            }
        )

        if result.modified_count > 0:
            updated += 1

    return {
        "processed": processed,
        "updated": updated,
    }
