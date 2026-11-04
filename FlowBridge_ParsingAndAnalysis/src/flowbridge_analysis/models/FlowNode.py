"""FlowNode contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel, NodeType
from .SourceLocation import SourceLocation


@dataclass(kw_only=True)
class FlowNode(JsonModel):
    """Diagram node; synthetic nodes may have no source span."""
    node_id: str
    node_type: NodeType
    label: str
    source_location: SourceLocation | None = None

