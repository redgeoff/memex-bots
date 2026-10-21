"""Data model for a bot (TODO(bot): replace Item/Candidate with your own)."""

from typing import TypedDict


class Item(TypedDict):
    """One piece of public evidence collected by the agent routine.

    Attributes:
        id: Stable id within the run.
        url: Source link (required; items without one are dropped).
        quote: Short verbatim excerpt.
        source: Where it came from (e.g. "hn", "web").
        candidate: Id of the candidate this evidence supports.
    """

    id: str
    url: str
    quote: str
    source: str
    candidate: str


class Candidate(TypedDict, total=False):
    """Something the bot judges each run.

    Attributes:
        id: Stable id across weeks (so week-over-week diffs work).
        title: Short human name.
        score: Integer computed in code from stored fields, never by the LLM.
        verdict: "advance", "watch" or "drop", computed in code from score.
        item_ids: Evidence supporting the candidate.
    """

    id: str
    title: str
    score: int
    verdict: str
    item_ids: list[str]
