"""Parsing and diagnostic-coordinate tests; uploaded source is never run."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from flowbridge_analysis import PythonParser
from flowbridge_analysis.models import FileInput


def file_input(source, file_id='F'):
    return FileInput(file_id=file_id, file_name='sample.py', file_path='sample.py', file_content=source)


class ParserTests(unittest.TestCase):
    def test_valid_function_and_ast_positions(self):
        result = PythonParser().parse(file_input('def f(x):\n    y = x + 1\n    return y\n'))
        self.assertTrue(result.syntax_valid)
        self.assertIsInstance(result.tree, ast.Module)
        self.assertEqual(result.diagnostics, [])
        self.assertEqual(result.tree.body[0].body[1].lineno, 3)

    def test_empty_comments_and_docstrings(self):
        for source in ['', '# empty\n', '"""module docs"""\n']:
            with self.subTest(source=source):
                self.assertTrue(PythonParser().parse(file_input(source)).syntax_valid)

    def test_syntax_and_indentation_errors(self):
        for source in ['def broken(:\n', 'def f():\nreturn 1\n', 'x = (', 'x = \x00']:
            with self.subTest(source=source):
                result = PythonParser().parse(file_input(source))
                self.assertFalse(result.syntax_valid)
                self.assertIsNone(result.tree)
                self.assertEqual(result.diagnostics[0].code, 'SYNTAX_ERROR')
                self.assertEqual(result.diagnostics[0].file_id, 'F')
                self.assertIsInstance(json.loads(result.diagnostics[0].to_json()), dict)

    def test_unicode_syntax_error_uses_byte_columns(self):
        source = 'é = @\n'
        error = PythonParser().parse(file_input(source)).diagnostics[0]
        self.assertEqual(error.source_location.start_column, len('é = '.encode('utf-8')))
        self.assertEqual(error.source_location.end_column, len('é = @'.encode('utf-8')))

    def test_point_error_is_not_expanded_into_invented_span(self):
        location = PythonParser().parse(file_input('é = )\n')).diagnostics[0].source_location
        self.assertEqual(location.start_column, len('é = '.encode('utf-8')))
        self.assertEqual(location.end_column, location.start_column)

    def test_crlf_and_multiline_errors(self):
        result = PythonParser().parse(file_input('def f():\r\n    é = )\r\n'))
        location = result.diagnostics[0].source_location
        self.assertEqual(location.start_line, 2)
        self.assertEqual(location.start_column, len('    é = '.encode('utf-8')))
        self.assertGreaterEqual((location.end_line, location.end_column),
                                (location.start_line, location.start_column))

    def test_missing_error_positions_remain_null(self):
        with patch('flowbridge_analysis.PythonParser.ast.parse', side_effect=SyntaxError('bad input')):
            result = PythonParser().parse(file_input('x'))
        self.assertIsNone(result.diagnostics[0].source_location)

    def test_resource_failure_is_not_syntax_rejection(self):
        with patch('flowbridge_analysis.PythonParser.ast.parse', side_effect=RecursionError):
            result = PythonParser().parse(file_input('x'))
        self.assertIsNone(result.syntax_valid)
        self.assertIsNone(result.tree)
        self.assertEqual(result.diagnostics[0].code, 'PARSER_LIMIT')

    def test_unencodable_text(self):
        result = PythonParser().parse(file_input('\ud800'))
        self.assertIsNone(result.syntax_valid)
        self.assertEqual(result.diagnostics[0].code, 'INVALID_SOURCE_ENCODING')

    def test_no_execution_imports_defaults_or_decorators(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'must-not-exist'
            source = (f'__import__("pathlib").Path({str(target)!r}).write_text("executed")\n'
                      'import module_that_does_not_exist\n'
                      '@missing_decorator()\ndef f(x=missing_default()):\n    return x\n')
            result = PythonParser().parse(file_input(source))
            self.assertTrue(result.syntax_valid)
            self.assertFalse(target.exists())

    def test_reuse_has_no_stale_tree_or_diagnostics(self):
        parser = PythonParser()
        bad = parser.parse(file_input('def f(:', 'bad'))
        good = parser.parse(file_input('def f():\n    return 1', 'good'))
        edited = parser.parse(file_input('def g():\n    return 2', 'good'))
        self.assertFalse(bad.syntax_valid)
        self.assertEqual(good.tree.body[0].name, 'f')
        self.assertEqual(edited.tree.body[0].name, 'g')
        self.assertEqual(good.diagnostics, [])
        self.assertIsNot(good.tree, edited.tree)

    def test_parse_acceptance_is_not_full_compiler_validation(self):
        # ast.parse accepts this AST; feature inspection separately rejects module return.
        self.assertTrue(PythonParser().parse(file_input('return 1')).syntax_valid)
