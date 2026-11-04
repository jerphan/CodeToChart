"""Class API, compatibility and structural-versus-syntax boundaries."""
import copy
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from flowbridge_analysis import InputValidator, PythonParser
from flowbridge_analysis.InputValidator import validate_project


class InputValidatorBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(Path('examples/calculator_input.json').read_text(encoding='utf-8-sig'))

    def test_class_function_and_legacy_paths_preserve_results(self) -> None:
        legacy = importlib.import_module('flowbridge_analysis.validator')
        canonical = importlib.import_module('flowbridge_analysis.InputValidator')
        self.assertIs(legacy, canonical)
        inputs = [self.payload, json.dumps(self.payload), {}, '{', dict(self.payload, revisionId=-1)]
        for payload in inputs:
            with self.subTest(payload=payload):
                self.assertEqual(InputValidator().validate(payload), validate_project(payload))
                self.assertEqual(legacy.validate_project(payload), validate_project(payload))

    def test_zero_revision_and_exact_identity_are_preserved(self) -> None:
        self.payload.update(projectId=' P:é ', revisionId=0)
        before = copy.deepcopy(self.payload)
        result = InputValidator().validate(json.dumps(self.payload))
        self.assertTrue(result.is_valid)
        self.assertEqual(result.project.to_dict(), before)
        self.assertEqual(self.payload, before)

    def test_input_validation_never_invokes_python_parser(self) -> None:
        self.payload['files'][0]['fileContent'] = 'def broken(:'
        with patch('ast.parse', side_effect=AssertionError('Input validation parsed source')):
            result = InputValidator().validate(self.payload)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.diagnostics, [])
        parsed = PythonParser().parse(result.project.files[0])
        self.assertFalse(parsed.syntax_valid)
        self.assertEqual(parsed.diagnostics[0].code, 'SYNTAX_ERROR')

    def test_structural_errors_have_no_source_location(self) -> None:
        self.payload['files'][0].pop('fileContent')
        result = InputValidator().validate(self.payload)
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.project)
        self.assertEqual(result.diagnostics[0].code, 'MISSING_FIELD')
        self.assertIsNone(result.diagnostics[0].source_location)

    def test_reused_validator_has_fresh_result_state(self) -> None:
        validator = InputValidator()
        bad = validator.validate({})
        good = validator.validate(self.payload)
        self.assertTrue(good.is_valid)
        self.assertEqual(good.diagnostics, [])
        self.assertFalse(bad.is_valid)
        self.assertTrue(bad.diagnostics)
