"""Diagnostic contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel
from .SourceLocation import SourceLocation


@dataclass(kw_only=True)
class Diagnostic(JsonModel):
    """Structured problem with optional file, source and graph context."""
    severity: Literal['info', 'warning', 'error']
    code: str
    message: str
    file_id: str | None = None
    source_location: SourceLocation | None = None
    graph_id: str | None = None

