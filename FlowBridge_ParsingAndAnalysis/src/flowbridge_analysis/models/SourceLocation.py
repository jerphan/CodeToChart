"""SourceLocation contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel


@dataclass(kw_only=True)
class SourceLocation(JsonModel):
    """Half-open span: one-based lines, zero-based UTF-8 byte columns."""
    file_id: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def __post_init__(self) -> None:
        super().__post_init__()
        if min(self.start_line, self.end_line) < 1 or min(self.start_column, self.end_column) < 0:
            raise ValueError('Invalid source coordinates')
        if (self.end_line, self.end_column) < (self.start_line, self.start_column):
            raise ValueError('Source span ends before it starts')

