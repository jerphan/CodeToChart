"""Input-to-parse-to-feature integration; no analysis service implied."""
import unittest
from flowbridge_analysis import FeatureValidator, PythonParser, validate_project


class ParsingIntegrationTests(unittest.TestCase):
    def test_sibling_files_keep_syntax_and_support_separate(self):
        sources = ['def f():\n    return 1', 'def f(:', 'def f():\n    with resource():\n        return 1']
        payload = {'projectId': 'P', 'projectName': 'P', 'revisionId': 1,
                   'files': [dict(fileId=str(i), fileName=f'{i}.py', filePath=f'{i}.py', fileContent=s)
                             for i, s in enumerate(sources)]}
        input_result = validate_project(payload)
        self.assertTrue(input_result.is_valid)
        parser = PythonParser()
        validator = FeatureValidator()
        parsed = [parser.parse(file) for file in input_result.project.files]
        self.assertEqual([item.syntax_valid for item in parsed], [True, False, True])
        supported = [validator.validate(item.tree, str(i)).is_supported if item.tree is not None else None
                     for i, item in enumerate(parsed)]
        self.assertEqual(supported, [True, None, False])
        self.assertEqual(parsed[2].diagnostics, [])
        self.assertEqual(parsed[1].diagnostics[0].code, 'SYNTAX_ERROR')
