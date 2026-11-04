"""ParameterInfo contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel


@dataclass(kw_only=True)
class ParameterInfo(JsonModel):
    """Parameter spelling, calling convention and optional annotation text."""
    name: str
    kind: Literal['positionalOnly', 'positionalOrKeyword', 'varPositional', 'keywordOnly', 'varKeyword']
    has_default: bool
    annotation: str | None = None

