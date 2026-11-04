"""FunctionInfo contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel
from .ParameterInfo import ParameterInfo
from .SourceLocation import SourceLocation


@dataclass(kw_only=True)
class FunctionInfo(JsonModel):
    """Function identity, lexical scope, parameters, source span and CFG link."""
    function_id: str
    function_name: str
    qualified_name: str
    file_id: str
    parameters: list[ParameterInfo]
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    graph_id: str
    scope_id: str

    def __post_init__(self) -> None:
        super().__post_init__()
        SourceLocation(file_id=self.file_id, start_line=self.start_line, end_line=self.end_line,
                       start_column=self.start_column, end_column=self.end_column)

