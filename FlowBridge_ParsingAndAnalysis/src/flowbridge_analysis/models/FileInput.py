"""FileInput contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from .JsonModel import JsonModel


@dataclass(kw_only=True)
class FileInput(JsonModel):
    """One Code Manager file snapshot, including uninterpreted source text."""
    file_id: str
    file_name: str
    file_path: str
    file_content: str

