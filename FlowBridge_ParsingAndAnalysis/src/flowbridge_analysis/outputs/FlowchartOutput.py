"""Kevin's approved graph projection of one canonical analysis."""
import json
from . import _snapshot
from ..models import ProjectAnalysis


class FlowchartOutput:
    """Capture a validated JSON snapshot without generating new identities."""

    def __init__(self, analysis: ProjectAnalysis) -> None:
        data = _snapshot(analysis)
        self._data = {key: data[key] for key in (
            'projectId', 'projectName', 'revisionId', 'status', 'graphs',
            'graphReferences', 'diagnostics', 'files', 'functions', 'callReferences', 'symbols')}

    def to_dict(self) -> dict[str, object]:
        """Return an independent JSON-compatible projection."""
        return json.loads(self.to_json())

    def to_json(self) -> str:
        """Serialize deterministically without exposing mutable canonical records."""
        return json.dumps(self._data, ensure_ascii=True, sort_keys=True, indent=2)
