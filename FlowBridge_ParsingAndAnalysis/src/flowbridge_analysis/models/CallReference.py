"""CallReference contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel
from .SourceLocation import SourceLocation


@dataclass(kw_only=True)
class CallReference(JsonModel):
    """Call-site metadata with explicit resolution state and optional target."""
    call_id: str
    file_id: str
    caller_function_id: str | None
    location: SourceLocation
    expression: str
    resolution: Literal['resolved', 'unresolved', 'ambiguous', 'builtin', 'external']
    reason: str
    target_function_id: str | None = None
    target_graph_id: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        targets = (self.target_function_id, self.target_graph_id)
        if self.resolution == 'resolved' and any(target is None for target in targets):
            raise ValueError('Resolved calls require function and graph targets')
        if self.resolution != 'resolved' and any(target is not None for target in targets):
            raise ValueError('Nonresolved calls cannot assert targets')

