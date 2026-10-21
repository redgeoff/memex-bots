"""Validation and scoring: deterministic, no LLM (TODO(bot): your rubric)."""

from .models import Candidate, Item


def valid_items(items: list[Item], max_quote_words: int) -> tuple[list[Item], int]:
    """Keep items that satisfy the citation rule.

    An item needs an http(s) URL and a quote of at most ``max_quote_words``.

    Args:
        items: Raw items from the agent.
        max_quote_words: Longest allowed quote.

    Returns:
        Tuple of (valid items, number dropped).
    """
    kept = [
        i
        for i in items
        if str(i.get("url", "")).startswith(("http://", "https://"))
        and len(str(i.get("quote", "")).split()) <= max_quote_words
    ]
    return kept, len(items) - len(kept)


def score_candidate(candidate: Candidate, items: list[Item]) -> int:
    """Score a candidate from its evidence.

    TODO(bot): replace with your rubric. The default counts distinct sources.

    Args:
        candidate: The candidate being scored.
        items: Valid items.

    Returns:
        An integer score.
    """
    return len({i["source"] for i in items if i["candidate"] == candidate["id"]})


def verdict(score: int, advance: int, watch: int) -> str:
    """Map a score to a verdict using the configured thresholds.

    Args:
        score: Candidate score.
        advance: Minimum score to advance.
        watch: Minimum score to watch.

    Returns:
        "advance", "watch" or "drop".
    """
    if score >= advance:
        return "advance"
    return "watch" if score >= watch else "drop"
