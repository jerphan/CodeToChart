"""Code Manager boundary normalization and pipeline compatibility."""
import copy
import json
from pathlib import Path
import unittest
from flowbridge_analysis import CodeManagerInputAdapter, ParsingAnalysisService, FlowchartOutput, MappingOutput


class AdapterTests(unittest.TestCase):
    def setUp(self):
        # Manual examples are editable. Keep this regression fixture independent
        # so changing the demonstration to five files does not break these tests.
        self.payload = {'projectID': 'adapter-test', 'projectName': 'sample_project', 'files': [
            {'fileID': 'F1', 'fileName': 'main.py', 'filePath': 'app/main.py',
             'fileContent': 'def greeting(name):\r\n    return f"Hello, {name}!"\r\n'},
            {'fileID': 'F2', 'fileName': 'formatting.py', 'filePath': 'app/utils/formatting.py',
             'fileContent': 'def format_title(title):\r\n    return title.strip().title()\r\n'},
            {'fileID': 'F3', 'fileName': 'main.py', 'filePath': 'tests/main.py',
             'fileContent': 'def expected_greeting():\r\n    return "Hello, FlowBridge!"\r\n'},
        ]}
        self.adapter = CodeManagerInputAdapter()

    def test_exact_snapshot_and_duplicate_basenames(self):
        original = copy.deepcopy(self.payload)
        normalized = self.adapter.normalize(self.payload, revision_id=4)
        self.assertEqual(self.payload, original)
        self.assertEqual(normalized['projectId'], original['projectID'])
        self.assertNotIn('projectID', normalized)
        for before, after in zip(original['files'], normalized['files']):
            self.assertEqual(after['fileId'], before['fileID'])
            for key in ('fileName', 'filePath', 'fileContent'):
                self.assertEqual(after[key], before[key])
        result = ParsingAnalysisService().analyze_project(normalized)
        self.assertEqual(result.status, 'success')
        self.assertEqual(len(result.graphs), 7)
        self.assertEqual(len(result.functions), 3)
        self.assertEqual(len({file.graph_id for file in result.files}), 3)
        for output in (result, FlowchartOutput(result), MappingOutput(result)):
            self.assertEqual(output.to_dict()['revisionId'], 4)

    def test_json_and_canonical_inputs(self):
        first = self.adapter.normalize(json.dumps(self.payload), revision_id=0)
        self.assertEqual(first, self.adapter.normalize(first, revision_id=0))

    def test_conflicting_aliases(self):
        self.payload['projectId'] = 'different'
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            self.adapter.normalize(self.payload, revision_id=1)
        del self.payload['projectId']
        self.payload['files'][0]['fileId'] = 'different'
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            self.adapter.normalize(self.payload, revision_id=1)

    def test_matching_aliases(self):
        self.payload['projectId'] = self.payload['projectID']
        self.payload['files'][0]['fileId'] = self.payload['files'][0]['fileID']
        self.adapter.normalize(self.payload, revision_id=1)

    def test_invalid_or_conflicting_revision(self):
        for value in (True, -1, 1.0, '1', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.adapter.normalize(self.payload, revision_id=value)
        self.payload['revisionId'] = 2
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            self.adapter.normalize(self.payload, revision_id=1)

    def test_invalid_input_and_duplicate_keys(self):
        for value in ('{', '{"projectID":"a","projectID":"b"}', [], {'extra': float('inf')}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.adapter.normalize(value, revision_id=1)
        self.payload['cycle'] = self.payload
        with self.assertRaises(ValueError):
            self.adapter.normalize(self.payload, revision_id=1)

    def test_required_fields_and_duplicate_file_ids(self):
        self.payload['files'][1]['fileID'] = self.payload['files'][0]['fileID']
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_FILE_ID'):
            self.adapter.normalize(self.payload, revision_id=1)
        del self.payload['projectName']
        with self.assertRaisesRegex(ValueError, 'MISSING_FIELD'):
            self.adapter.normalize(self.payload, revision_id=1)

    def test_no_counter_or_source_parsing_and_no_shared_objects(self):
        self.payload['files'][0]['fileContent'] = 'def broken(:'
        first = self.adapter.normalize(self.payload, revision_id=10)
        second = self.adapter.normalize(self.payload, revision_id=3)
        self.assertEqual(first['revisionId'], 10)
        self.assertEqual(second['revisionId'], 3)
        second['files'].clear()
        self.assertEqual(len(first['files']), 3)
        result = ParsingAnalysisService().analyze_project(first)
        self.assertTrue(any(d.code == 'SYNTAX_ERROR' for d in result.diagnostics))
