"""Result contract shared by every bot.

Every bot's ``skill.py`` has a module-level ``run()`` that returns a SkillResult
dict with a status, an output and an optional error. This module defines that
type and the helpers that build it.
"""

from typing import Any, TypedDict


class SkillResult(TypedDict, total=False):
    """Standard return type for every bot's ``run()`` function.

    Attributes:
        status: "ok" if the skill ran successfully, "error" otherwise.
        output: The primary result of the skill (any JSON-serializable type).
        error: Error message if status is "error"; None or absent otherwise.
    """

    status: str  # "ok" | "error"
    output: Any  # primary result
    error: str | None  # error message, if any


def ok(output: Any) -> SkillResult:
    """Build a successful SkillResult.

    Args:
        output: The primary result to return.

    Returns:
        A SkillResult with status "ok".
    """
    return SkillResult(status="ok", output=output, error=None)


def error(message: str) -> SkillResult:
    """Build an error SkillResult.

    Args:
        message: Human-readable description of what went wrong.

    Returns:
        A SkillResult with status "error".
    """
    return SkillResult(status="error", output=None, error=message)
