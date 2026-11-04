"""Internal import metadata; this is not a new downstream JSON contract."""
from dataclasses import dataclass
from .models import SourceLocation


@dataclass
class ImportRelationship:
    """An explicit import binding, retaining module/member distinctions."""
    file_id: str
    scope_id: str
    binding_name: str
    module: str
    member: str | None
    level: int
    location: SourceLocation
    is_module_level: bool
