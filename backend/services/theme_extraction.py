"""
Theme extraction and Customer Pain-Point identification engine.
Provides NLP theme mining, keyword clustering, and impact-weighted pain point detection with explainable formulas.
"""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
from services.preprocessing import normalize, STOPWORDS_SET
from services.categorization import detect_sentiment, categorize


def _resolve_sentiment(item: Dict[str, Any]) -> str:
    s = item.get("sentiment")
    if s:
        return s
    text = f"{item.get('title') or ''} {item.get('content') or ''}".strip()
    return detect_sentiment(text, item.get("rating"))


def _resolve_category(item: Dict[str, Any]) -> str:
    c = item.get("category")
    if c:
        return c
    text = f"{item.get('title') or ''} {item.get('content') or ''}".strip()
    return categorize(text)



# Domain topics definition with comprehensive semantic keywords
DOMAIN_TOPICS = {
    "Authentication & Access": [
        "login", "signin", "sign in", "signup", "sign up", "password", "password reset",
        "auth", "token", "session", "2fa", "mfa", "logout", "unexpected logout",
        "account", "register", "credential", "reset", "biometric", "face id", "fingerprint",
        "multiple account", "switch account"
    ],
    "Performance & Stability": [
        "slow", "lag", "latency", "load", "loading", "freeze", "freezes", "crash", "crashes",
        "performance", "delay", "responsive", "unresponsive", "memory", "timeout", "fps",
        "battery", "heating", "stuck", "smooth", "faster", "good performance"
    ],
    "UI & User Experience": [
        "ui", "ux", "design", "layout", "button", "navigation", "theme", "dark mode",
        "interface", "cluttered", "font", "accessibility", "screen-reader", "larger text",
        "clean", "simple", "onboarding", "confusing", "setup", "ads", "advertisements"
    ],
    "Search & Filtering": [
        "search", "filter", "sort", "find", "query", "lookup", "pagination", "results",
        "inaccurate", "misses", "exact match"
    ],
    "Notifications & Alerts": [
        "notification", "email", "alert", "push", "message", "remind", "reminder",
        "webhook", "outdated information", "late", "delivered"
    ],
    "Data Management & Sync": [
        "import", "export", "csv", "json", "excel", "upload", "download", "file",
        "parsing", "format", "sync", "data sync", "backup", "appear"
    ],
    "Billing & Payments": [
        "billing", "price", "pricing", "plan", "subscription", "payment", "payment failed",
        "invoice", "cost", "upgrade", "deducted", "refund"
    ],
    "Customer Support & Service": [
        "support", "customer support", "helpful support", "support team", "responded", "solved my issue", "agent"
    ]
}


# Pre-compile domain topic matchers for ultra-fast performance on 10k+ records
_COMPILED_DOMAIN_TOPICS = []
for _topic, _kws in DOMAIN_TOPICS.items():
    _phrases = [k for k in _kws if " " in k]
    _singles = [k for k in _kws if " " not in k]
    _single_re = re.compile(r'\b(?:' + '|'.join(re.escape(k) for k in _singles) + r')\b') if _singles else None
    _COMPILED_DOMAIN_TOPICS.append((_topic, _phrases, _single_re))


def extract_ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """Generate n-grams from a list of tokens."""
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def extract_keywords_and_phrases(texts: List[str], top_k: int = 8) -> List[Tuple[str, int]]:
    """
    Extract most frequent relevant unigrams and bigrams.
    Samples representative items on large datasets (10k+) for sub-second execution.
    """
    unigram_counts = Counter()
    bigram_counts = Counter()

    # Subsample up to 400 representative texts to prevent CPU thrashing
    sample_texts = texts[:400] if len(texts) > 400 else texts

    for text in sample_texts:
        tokens = normalize(text)
        filtered_tokens = [t for t in tokens if len(t) > 2 and t not in STOPWORDS_SET]
        unigram_counts.update(filtered_tokens)
        bigrams = extract_ngrams(filtered_tokens, 2)
        bigram_counts.update(bigrams)

    combined = unigram_counts.most_common(top_k) + bigram_counts.most_common(top_k // 2)
    return sorted(combined, key=lambda x: x[1], reverse=True)[:top_k]


def match_domain_topic(text: str) -> str:
    """Find the best domain topic for a text string using pre-compiled regex."""
    if not text:
        return "General Product Usage"
    text_lower = text.lower()
    for topic_name, phrase_kws, single_re in _COMPILED_DOMAIN_TOPICS:
        for kw in phrase_kws:
            if kw in text_lower:
                return topic_name
        if single_re and single_re.search(text_lower):
            return topic_name
    return "General Product Usage"


def extract_themes_from_feedback(feedback_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract high-level product themes across feedback items.
    Groups feedback by detected topics and computes exact theme statistics.
    """
    if not feedback_list:
        return []

    topic_feedback = defaultdict(list)

    for item in feedback_list:
        content = item.get("content") or ""
        title = item.get("title") or ""
        full_text = f"{title} {content}".strip()
        topic = match_domain_topic(full_text)
        topic_feedback[topic].append(item)

    themes = []
    theme_idx = 1

    for topic_name, items in sorted(topic_feedback.items(), key=lambda x: len(x[1]), reverse=True):
        if not items:
            continue

        total_topic_items = len(items)
        pos = sum(1 for it in items if _resolve_sentiment(it) == "positive")
        neg = sum(1 for it in items if _resolve_sentiment(it) == "negative")
        neu = sum(1 for it in items if _resolve_sentiment(it) == "neutral")

        sentiment_score = round((pos - neg) / (total_topic_items if total_topic_items > 0 else 1), 2)

        # Dominant category
        category_counts = Counter(_resolve_category(it) for it in items)
        dominant_cat = category_counts.most_common(1)[0][0] if category_counts else "general_feedback"

        # Keywords
        topic_texts = [f"{it.get('title', '')} {it.get('content', '')}" for it in items]
        top_kws = [kw for kw, _ in extract_keywords_and_phrases(topic_texts, top_k=6)]

        # Deduplicated sample quotes
        seen_quotes = set()
        quotes = []
        for it in items:
            q = (it.get("content") or it.get("title") or "").strip()
            if q and q not in seen_quotes and len(quotes) < 3:
                seen_quotes.add(q)
                quotes.append(q[:130] + ("..." if len(q) > 130 else ""))

        desc = (
            f"Discussed across {total_topic_items} feedback records ({pos} positive, {neu} neutral, {neg} negative). "
            f"Primary focus relates to {dominant_cat.replace('_', ' ')}."
        )

        themes.append({
            "id": f"theme_{theme_idx}",
            "title": topic_name,
            "description": desc,
            "category": dominant_cat,
            "frequency": total_topic_items,
            "sentiment_breakdown": {
                "positive": pos,
                "neutral": neu,
                "negative": neg,
            },
            "sentiment_score": sentiment_score,
            "keywords": top_kws,
            "sample_quotes": quotes,
        })
        theme_idx += 1

    return themes


def extract_pain_points_from_feedback(feedback_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify and score customer pain points with deterministic, explainable impact formulas.
    """
    if not feedback_list:
        return []

    total_count = max(len(feedback_list), 1)

    # Filter items that are pain points
    issue_candidates = []
    for item in feedback_list:
        sentiment = _resolve_sentiment(item)
        category = _resolve_category(item)
        rating = item.get("rating")

        is_pain = (
            sentiment == "negative"
            or category in ("bug_report", "performance_issue")
            or (rating is not None and rating <= 2)
        )
        if is_pain:
            issue_candidates.append(item)

    if not issue_candidates:
        return []

    # Group issues by matched domain area
    grouped_issues = defaultdict(list)
    for item in issue_candidates:
        full_text = f"{(item.get('title') or '')} {(item.get('content') or '')}".strip()
        topic = match_domain_topic(full_text)
        if topic == "General Product Usage":
            topic = "System Usability & Stability"
        grouped_issues[topic].append(item)

    pain_points = []
    idx = 1

    recommendations_map = {
        "Authentication & Access": "Streamline password reset delivery, investigate token expirations, and test biometric login workflows.",
        "Performance & Stability": "Profile memory leaks on mobile devices, optimize UI render loops, and resolve crash-inducing timeouts.",
        "UI & User Experience": "Improve dark mode contrast, ensure screen reader accessibility, and simplify the onboarding flow.",
        "Search & Filtering": "Upgrade search indexing, enable fuzzy matching, and test exact keyword query relevance.",
        "Notifications & Alerts": "Optimize push notification queues, address dispatch delays, and verify email template accuracy.",
        "Data Management & Sync": "Add background retry for cloud data sync and provide clear progress indicators during file uploads.",
        "Billing & Payments": "Integrate real-time payment gateway error handling and verify automated receipt/invoice generation.",
        "System Usability & Stability": "Conduct usability testing and resolve blocking client-side exceptions.",
    }

    for group_name, items in sorted(grouped_issues.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(items)
        if count == 0:
            continue

        ratings = [it.get("rating") for it in items if it.get("rating") is not None]
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 2.0
        neg_count = sum(1 for it in items if _resolve_sentiment(it) == "negative")
        negative_pct = round((neg_count / count) * 100, 1)
        bug_count = sum(1 for it in items if _resolve_category(it) in ("bug_report", "performance_issue"))

        # Deterministic Impact Score Formula (0 to 100):
        # 1. Volume Factor (up to 35 pts)
        vol_factor = min(35.0, (count / total_count) * 100.0 * 2.0)
        # 2. Rating Penalty (up to 25 pts)
        rating_penalty = max(0.0, (5.0 - avg_rating) * 5.0)
        # 3. Negative Sentiment Ratio (up to 25 pts)
        neg_factor = (neg_count / count) * 25.0
        # 4. Bug Report Factor (up to 15 pts)
        bug_factor = (bug_count / count) * 15.0

        raw_score = vol_factor + rating_penalty + neg_factor + bug_factor
        impact_score = round(min(98.0, max(20.0, raw_score)), 1)

        # Severity
        if impact_score >= 60.0 or count >= 10 or (avg_rating <= 1.5 and neg_count > 5):
            severity = "high"
        elif impact_score >= 40.0 or count >= 3:
            severity = "medium"
        else:
            severity = "low"


        # Deduplicate sample quotes
        seen_quotes = set()
        quotes = []
        for it in items:
            q = (it.get("content") or it.get("title") or "").strip()
            if q and q not in seen_quotes and len(quotes) < 3:
                seen_quotes.add(q)
                quotes.append(q[:130] + ("..." if len(q) > 130 else ""))

        rec = recommendations_map.get(
            group_name,
            "Triage incoming issue tickets with engineering and prioritize stability fixes in the upcoming sprint."
        )

        pain_points.append({
            "id": f"pain_point_{idx}",
            "title": f"Friction in {group_name}",
            "description": f"Observed in {count} customer complaints ({neg_count} negative sentiment, avg rating {avg_rating}/5.0).",
            "severity": severity,
            "impact_score": impact_score,
            "affected_users_count": count,
            "category": items[0].get("category") or "bug_report",
            "recommended_action": rec,
            "sample_quotes": quotes,
            "distinct_sample_quotes": quotes,
            "score_breakdown": {
                "frequency": count,
                "negative_sentiment_pct": negative_pct,
                "avg_rating": avg_rating,
                "bug_count": bug_count,
                "severity_level": severity,
                "formula_weights": "Volume (35%) + Low Rating (25%) + Negative % (25%) + Bug Ratio (15%)"
            }
        })
        idx += 1

    pain_points.sort(key=lambda x: x["impact_score"], reverse=True)
    return pain_points
