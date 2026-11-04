"""Translate Code Manager snapshots to the existing analysis input contract."""
from copy import deepcopy
from .InputValidator import InputValidator, _check_json_value, _decode_json


class CodeManagerInputAdapter:
    """Normalize field names without storing source, results or revision counters."""

    def normalize(self, payload: str | dict[str, object], *, revision_id: int) -> dict[str, object]:
        """Return validated canonical JSON values; raise ValueError for bad input.

        The coordinating backend (or local CLI) supplies revision_id before analysis.
        This adapter inserts that value; it never guesses ordering or increments it.
        Source text, paths and user ID values are preserved exactly. Input is not mutated.
        """
        if type(revision_id) is not int or revision_id < 0:
            raise ValueError('revision_id must be a nonnegative integer, not a boolean')
        try:
            decoded = _decode_json(payload) if isinstance(payload, str) else payload
            _check_json_value(decoded, set())
            if not isinstance(decoded, dict):
                raise ValueError('Code Manager input must be a JSON object')
            normalized = deepcopy(decoded)
        except RecursionError as error:
            raise ValueError('Code Manager input exceeds nesting capacity') from error
        self._rename(normalized, 'projectID', 'projectId', '$')
        if 'revisionId' in normalized:
            existing = normalized['revisionId']
            if type(existing) is not int or existing != revision_id:
                raise ValueError('Payload revisionId conflicts with supplied revision_id')
        normalized['revisionId'] = revision_id
        records = normalized.get('files')
        if isinstance(records, list):
            for index, record in enumerate(records):
                if isinstance(record, dict):
                    self._rename(record, 'fileID', 'fileId', f'$.files[{index}]')
        # Reuse the contract validator rather than maintaining a second set of
        # field/type/uniqueness rules. Python syntax is checked later by the parser.
        validation = InputValidator().validate(normalized)
        if validation.project is None:
            raise ValueError('; '.join(f'{item.code}: {item.message}' for item in validation.diagnostics))
        # Retain extensions so normal service validation also retains its warnings.
        return normalized

    @staticmethod
    def _rename(record: dict[str, object], incoming: str, canonical: str, path: str) -> None:
        """Accept either spelling, but never silently choose conflicting identities."""
        if incoming not in record:
            return
        if canonical in record and (type(record[incoming]) is not type(record[canonical])
                                    or record[incoming] != record[canonical]):
            raise ValueError(f'{path}: conflicting {incoming} and {canonical}')
        record[canonical] = record.pop(incoming)
