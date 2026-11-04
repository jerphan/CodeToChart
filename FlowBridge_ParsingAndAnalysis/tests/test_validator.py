"""Input validation tests; source strings are data, never executed."""
import copy
import json
from pathlib import Path
import unittest

from flowbridge_analysis.InputValidator import InputValidator

# Exercise the public class with the entire existing behavioral test matrix.
validate_project = InputValidator().validate


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(Path('examples/calculator_input.json').read_text(encoding='utf-8-sig'))

    def test_sample_roundtrip_and_identity(self):
        result = validate_project(self.payload)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.diagnostics, [])
        self.assertEqual(json.loads(result.project.to_json()), self.payload)
        self.assertEqual(validate_project(result.project.to_json()).project, result.project)

    def test_multifile_and_empty_source(self):
        second = dict(self.payload['files'][0], fileId='F002', filePath='empty.py', fileContent='')
        self.payload['files'].append(second)
        result = validate_project(self.payload)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.project.files), 2)

    def test_empty_project(self):
        self.payload['files'] = []
        self.assertTrue(validate_project(self.payload).is_valid)

    def test_missing_project_fields(self):
        for name in self.payload:
            with self.subTest(name=name):
                payload = copy.deepcopy(self.payload)
                del payload[name]
                result = validate_project(payload)
                self.assertFalse(result.is_valid)
                self.assertTrue(any(d.code == 'MISSING_FIELD' and name in d.message for d in result.diagnostics))

    def test_missing_file_fields(self):
        for name in self.payload['files'][0]:
            with self.subTest(name=name):
                payload = copy.deepcopy(self.payload)
                del payload['files'][0][name]
                self.assertFalse(validate_project(payload).is_valid)

    def test_invalid_project_fields(self):
        for key, value in [('projectId', ''), ('projectName', '  '), ('projectId', 12),
                           ('revisionId', True), ('revisionId', -1), ('revisionId', 1.0),
                           ('revisionId', '1'), ('files', {}), ('files', None)]:
            with self.subTest(key=key, value=value):
                self.assertFalse(validate_project(dict(self.payload, **{key: value})).is_valid)

    def test_invalid_file_fields(self):
        for name in self.payload['files'][0]:
            for value in [None, 42, [], {}, True]:
                with self.subTest(name=name, value=value):
                    payload = copy.deepcopy(self.payload)
                    payload['files'][0][name] = value
                    self.assertFalse(validate_project(payload).is_valid)
        for name in ['fileId', 'fileName', 'filePath']:
            payload = copy.deepcopy(self.payload)
            payload['files'][0][name] = ' \t'
            self.assertFalse(validate_project(payload).is_valid)

    def test_invalid_top_level_and_file_records(self):
        for value in [None, True, 1, [], 'null', '[]', '"text"']:
            self.assertFalse(validate_project(value).is_valid)
        self.payload['files'] = [None, 'file', [], 3]
        self.assertEqual(len(validate_project(self.payload).diagnostics), 4)

    def test_duplicate_ids(self):
        self.payload['files'].append(dict(self.payload['files'][0], filePath='other.py'))
        result = validate_project(self.payload)
        self.assertIsNone(result.project)
        self.assertIn('DUPLICATE_FILE_ID', [d.code for d in result.diagnostics])

    def test_duplicate_paths_warn_without_dropping_files(self):
        self.payload['files'].append(dict(self.payload['files'][0], fileId='F002'))
        result = validate_project(self.payload)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.project.files), 2)
        self.assertEqual(result.diagnostics[0].severity, 'warning')

    def test_malformed_and_duplicate_json_keys(self):
        for value in ['{', '{"x":1,"x":2}', '{"files":[{"x":1,"x":2}]}',
                      '{"revisionId":NaN}', '{"revisionId":Infinity}']:
            with self.subTest(value=value):
                self.assertEqual(validate_project(value).diagnostics[0].code, 'INVALID_JSON')

    def test_unknown_fields_ignored_no_coercion_or_mutation(self):
        self.payload['projectId'] = ' P:001 '
        self.payload['extra'] = 'ignored'
        before = copy.deepcopy(self.payload)
        result = validate_project(self.payload)
        self.assertEqual(result.project.project_id, ' P:001 ')
        self.assertNotIn('extra', result.project.to_dict())
        self.assertEqual(self.payload, before)

    def test_source_not_parsed(self):
        self.payload['files'][0]['fileContent'] = 'def broken(:\nraise RuntimeError("must not run")'
        self.assertTrue(validate_project(self.payload).is_valid)

    def test_revision_requests_do_not_share_state(self):
        first = validate_project(self.payload)
        self.payload['revisionId'] = 2
        self.payload['files'] = []
        second = validate_project(self.payload)
        self.assertEqual(first.project.revision_id, 1)
        self.assertEqual(len(first.project.files), 1)
        self.assertEqual(second.project.files, [])

    def test_non_json_extension_values_and_cycles(self):
        for value in [float('nan'), float('inf'), object(), {1: 'bad key'}]:
            with self.subTest(value=value):
                payload = dict(self.payload, extra=value)
                self.assertEqual(validate_project(payload).diagnostics[0].code, 'INVALID_JSON')
        self.payload['extra'] = self.payload
        self.assertEqual(validate_project(self.payload).diagnostics[0].code, 'INVALID_JSON')
        text = '{"projectId":"P","projectName":"P","revisionId":1,"files":[],"extra":1e999}'
        self.assertEqual(validate_project(text).diagnostics[0].code, 'INVALID_JSON')
