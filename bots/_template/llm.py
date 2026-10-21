"""LLM adapter (hybrid architecture).

There is no LLM API call in code. The agent routine does the searching and
judgement with its own tools and writes JSON files into a run directory;
FileLLM serves them so the pipeline and tests stay deterministic and offline.
"""

import json
from pathlib import Path
from typing import Protocol


class LLM(Protocol):
    """Anything that can return a JSON object for a named response."""

    def complete_json(self, name: str) -> dict:
        """Return the JSON object called ``name``."""
        ...


class FileLLM:
    """Serve ``<run_dir>/<name>.json`` files written by the agent routine."""

    def __init__(self, run_dir: Path) -> None:
        """Create the adapter.

        Args:
            run_dir: Directory holding the agent's JSON outputs for one run.
        """
        self.run_dir = Path(run_dir)

    def complete_json(self, name: str) -> dict:
        """Load one response file.

        Args:
            name: File stem, e.g. "items" reads ``items.json``.

        Returns:
            The parsed JSON object.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file does not hold a JSON object.
        """
        path = self.run_dir / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return data
