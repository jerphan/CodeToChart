"""FileMetadata contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import GraphStatus, JsonModel


@dataclass(kw_only=True)
class FileMetadata(JsonModel):
    """Output file description and overview-graph link; excludes source text."""
    file_id: str
    file_name: str
    file_path: str
    graph_id: str
    status: GraphStatus

