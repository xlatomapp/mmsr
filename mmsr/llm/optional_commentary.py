"""Optional LLM commentary adapter.

This module intentionally contains no concrete SDK dependency. Integrations should be
added behind optional extras and must only polish deterministic facts/comments.
"""

from __future__ import annotations


class OptionalLLMCommentary:
    """Interface for optional LLM commentary polishing."""

    def polish(self, comments: list[str]) -> str:
        """Polish deterministic comments without adding new facts."""
        raise NotImplementedError("LLM commentary is optional and disabled by default")
