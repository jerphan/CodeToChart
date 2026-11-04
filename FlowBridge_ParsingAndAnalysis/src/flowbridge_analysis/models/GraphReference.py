"""GraphReference contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel


@dataclass(kw_only=True)
class GraphReference(JsonModel):
    """Cross-view navigation, not an executable control-flow edge."""
    source_graph_id: str
    source_node_id: str
    target_graph_id: str

