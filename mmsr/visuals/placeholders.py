"""Visualization placeholder interfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualSpec:
    """A visual specification independent of rendering backend."""

    title: str
    metric_names: list[str]
    visual_type: str
    group_by: list[str]
