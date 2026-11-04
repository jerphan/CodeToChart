"""Stateless IDs derived from a project revision and explicit structural key."""
import base64
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class RevisionIds:
    """Generate repeatable IDs within a project revision without changing user IDs.

    The complete identity is (project_id, revision_id, kind, *structural_key).
    Different supported tuples have distinct encodings; the same tuple reuses
    its ID. Callers must include the owning file/function/graph in their keys.
    No registry detects accidental reuse of a key for two different objects.
    """
    project_id: str
    revision_id: int

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError('project_id must be a nonblank string')
        if type(self.revision_id) is not int or self.revision_id < 0:
            raise ValueError('revision_id must be a nonnegative integer')

    def make(self, kind: str, *structural_key: str | int) -> str:
        """Return an ASCII fb1_ ID for a nonblank kind and string/integer key parts.

        Use file ID plus definition position/name for functions, graph ID plus
        local ordinal for nodes/edges, and file ID plus source span for calls.
        Kind separates categories; project and revision separate snapshots.
        Booleans are rejected as key parts. This is reversible encoding, not
        hashing, encryption or a promise of stable identity across source edits.
        """
        if not isinstance(kind, str) or not kind.strip() or not structural_key:
            raise ValueError('A kind and structural key are required')
        if any(type(part) not in (str, int) for part in structural_key):
            raise ValueError('Structural key parts must be strings or integers')
        # JSON preserves boundaries and types: ['a:b', 'c'] differs from
        # ['a', 'b:c']. Base64 is reversible, avoiding hash collisions entirely.
        payload = json.dumps([self.project_id, self.revision_id, kind, *structural_key],
                             ensure_ascii=True, separators=(',', ':')).encode('ascii')
        return 'fb1_' + base64.urlsafe_b64encode(payload).decode('ascii').rstrip('=')
