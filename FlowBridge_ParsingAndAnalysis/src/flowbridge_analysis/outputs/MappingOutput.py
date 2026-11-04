"""Grace's approved mapping/navigation projection."""
import json
from . import _snapshot
from ..models import ProjectAnalysis


class MappingOutput:
    """Preserve canonical source positions, navigation and call identities."""

    def __init__(self, analysis: ProjectAnalysis) -> None:
        data = _snapshot(analysis)
        self._data = {key: data[key] for key in (
            'projectId', 'revisionId', 'status', 'files', 'functions',
            'sourceMappings', 'graphReferences', 'callReferences', 'diagnostics')}

    def to_dict(self) -> dict[str, object]:
        """Return independent JSON values suitable for the mapping consumer."""
        return json.loads(self.to_json())

    def to_json(self) -> str:
        """Serialize deterministically with no ASTs or persistence."""
        return json.dumps(self._data, ensure_ascii=True, sort_keys=True, indent=2)
