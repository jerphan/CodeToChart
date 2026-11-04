"""SourceMapping contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel
from .SourceLocation import SourceLocation


@dataclass(kw_only=True)
class SourceMapping(JsonModel):
    """Connect a graph-local node to a source span."""
    graph_id: str
    node_id: str
    location: SourceLocation

