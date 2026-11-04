"""Validate Code Manager JSON without interpreting uploaded source text."""
import json
import math
from dataclasses import dataclass, field
from typing import Literal

from .models import Diagnostic, FileInput, ProjectInput
from .FeatureValidator import FeatureValidator, FeatureValidationResult


@dataclass
class ValidationResult:
    """Complete typed input or diagnostics; invalid partial inputs are not exposed."""
    project: ProjectInput | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Warnings do not invalidate an otherwise complete snapshot."""
        return self.project is not None


def _object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON object key: {key}')
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f'Nonfinite JSON number: {value}')


def _decode_json(payload: str) -> object:
    """Decode consistently for validation and safe failure-envelope identity."""
    return json.loads(payload, object_pairs_hook=_object_pairs, parse_constant=_reject_constant)


def _check_json_value(value: object, ancestors: set[int]) -> None:
    """Reject non-JSON Python objects and cycles, even in ignored extension fields."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if not isinstance(value, (list, dict)):
        raise ValueError('Input contains a non-JSON or nonfinite value')
    if id(value) in ancestors:
        raise ValueError('Input contains a circular container')
    ancestors.add(id(value))
    try:
        if isinstance(value, dict) and any(not isinstance(key, str) for key in value):
            raise ValueError('JSON object keys must be strings')
        for item in value.values() if isinstance(value, dict) else value:
            _check_json_value(item, ancestors)
    finally:
        ancestors.remove(id(value))


def validate_project(payload: str | dict[str, object]) -> ValidationResult:
    """Validate JSON text or a decoded object; retain exact supplied IDs and text."""
    result = ValidationResult()

    def report(code: str, message: str, file_id: str | None = None,
               severity: Literal['error', 'warning'] = 'error') -> None:
        result.diagnostics.append(Diagnostic(severity=severity, code=code, message=message, file_id=file_id))

    if isinstance(payload, str):
        try:
            payload = _decode_json(payload)
        except (ValueError, RecursionError) as error:
            report('INVALID_JSON', str(error))
            return result
    if not isinstance(payload, dict):
        report('INVALID_FIELD', '$ must be an object')
        return result
    try:
        _check_json_value(payload, set())
    except (ValueError, RecursionError) as error:
        report('INVALID_JSON', str(error))
        return result

    def string_fields(record: dict, names: tuple[str, ...], path: str,
                      file_id: str | None = None) -> bool:
        valid = True
        for name in names:
            if name not in record:
                report('MISSING_FIELD', f'{path}.{name} is required', file_id)
                valid = False
            elif not isinstance(record[name], str) or (name != 'fileContent' and not record[name].strip()):
                qualifier = '' if name == 'fileContent' else 'nonblank '
                report('INVALID_FIELD', f'{path}.{name} must be a {qualifier}string', file_id)
                valid = False
        return valid

    string_fields(payload, ('projectId', 'projectName'), '$')
    if 'revisionId' not in payload:
        report('MISSING_FIELD', '$.revisionId is required')
    elif type(payload['revisionId']) is not int or payload['revisionId'] < 0:
        report('INVALID_FIELD', '$.revisionId must be a nonnegative integer, not a boolean')
    if 'files' not in payload:
        report('MISSING_FIELD', '$.files is required')
    elif not isinstance(payload['files'], list):
        report('INVALID_FIELD', '$.files must be an array')

    files: list[FileInput] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    records = payload.get('files', [])
    for index, record in enumerate(records if isinstance(records, list) else []):
        path = f'$.files[{index}]'
        if not isinstance(record, dict):
            report('INVALID_FIELD', f'{path} must be an object')
            continue
        file_id = record.get('fileId')
        known_id = file_id if isinstance(file_id, str) and file_id.strip() else None
        if not string_fields(record, ('fileId', 'fileName', 'filePath', 'fileContent'), path, known_id):
            continue
        if file_id in seen_ids:
            report('DUPLICATE_FILE_ID', f'{path}.fileId duplicates {file_id!r}', file_id)
        seen_ids.add(file_id)
        if record['filePath'] in seen_paths:
            report('DUPLICATE_FILE_PATH', f'{path}.filePath is ambiguous for future import resolution',
                   file_id, 'warning')
        seen_paths.add(record['filePath'])
        files.append(FileInput(file_id=file_id, file_name=record['fileName'],
                               file_path=record['filePath'], file_content=record['fileContent']))
    if not any(item.severity == 'error' for item in result.diagnostics):
        result.project = ProjectInput(project_id=payload['projectId'], project_name=payload['projectName'],
                                      revision_id=payload['revisionId'], files=files)
    return result




class InputValidator:
    """Validate Code Manager structure independently of Python syntax/features.

    Instances hold no request state. Source text and supplied identities are
    preserved; invalid input produces diagnostics rather than a partial project.
    """

    def validate(self, payload: str | dict[str, object]) -> ValidationResult:
        """Return a complete ProjectInput or structural validation diagnostics.

        Accept JSON text or a decoded JSON object. This delegates to the existing
        function API so both entry points enforce exactly the same contract.
        Python source is neither parsed nor executed here.
        """
        return validate_project(payload)
