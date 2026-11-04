"""ProjectInput contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel, _unique
from .FileInput import FileInput


@dataclass(kw_only=True)
class ProjectInput(JsonModel):
    """Complete source snapshot with Code Manager identity and revision."""
    project_id: str
    project_name: str
    revision_id: int
    files: list[FileInput]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.revision_id < 0:
            raise ValueError('revision_id must be nonnegative')
        _unique([item.file_id for item in self.files], 'file IDs')

