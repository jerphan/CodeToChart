"""FlowEdge contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import EdgeType, JsonModel


@dataclass(kw_only=True)
class FlowEdge(JsonModel):
    """Control-flow connection between nodes in the same graph."""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    label: str | None = None

