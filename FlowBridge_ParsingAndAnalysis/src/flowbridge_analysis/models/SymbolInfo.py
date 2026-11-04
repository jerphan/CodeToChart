"""SymbolInfo contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel
from .SourceLocation import SourceLocation


@dataclass(kw_only=True)
class SymbolInfo(JsonModel):
    """Binding metadata only; constructing this record does not resolve names."""
    scope_id: str
    name: str
    kind: Literal['function', 'parameter', 'local', 'import', 'module']
    file_id: str
    location: SourceLocation | None = None
    function_id: str | None = None
    import_target: str | None = None

