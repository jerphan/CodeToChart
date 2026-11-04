"""Model invariants and JSON serialization without AST construction."""
import json
import unittest
from dataclasses import replace

from flowbridge_analysis.models import (
    CallReference, Diagnostic, FileInput, FileMetadata, FlowEdge, FlowNode,
    FunctionInfo, GraphModel, GraphReference, ParameterInfo, ProjectAnalysis,
    ProjectInput, SourceLocation, SourceMapping, SymbolInfo,
)


def example_analysis():
    location = SourceLocation(file_id='F', start_line=1, start_column=0, end_line=1, end_column=4)
    file_node = FlowNode(node_id='function-node', node_type='function', label='f', source_location=location)
    function_node = FlowNode(node_id='statement', node_type='statement', label='café', source_location=location)
    overview = GraphModel(graph_id='file', view_type='file', file_id='F', status='complete', nodes=[file_node])
    cfg = GraphModel(graph_id='function', view_type='function', file_id='F', function_id='fn',
                     status='complete', nodes=[function_node, FlowNode(node_id='end', node_type='end', label='End')],
                     edges=[FlowEdge(edge_id='e', source_id='statement', target_id='end', edge_type='next')])
    function = FunctionInfo(function_id='fn', function_name='f', qualified_name='module.f', file_id='F',
                            parameters=[ParameterInfo(name='x', kind='positionalOrKeyword', has_default=False)],
                            start_line=1, end_line=1, start_column=0, end_column=4,
                            graph_id='function', scope_id='scope')
    return ProjectAnalysis(project_id='P', project_name='Project', revision_id=1, status='success',
        files=[FileMetadata(file_id='F', file_name='m.py', file_path='m.py', graph_id='file', status='complete')],
        functions=[function], graphs={'file': overview, 'function': cfg},
        source_mappings=[SourceMapping(graph_id='function', node_id='statement', location=location)],
        graph_references=[GraphReference(source_graph_id='file', source_node_id='function-node', target_graph_id='function')],
        symbols=[SymbolInfo(scope_id='scope', name='x', kind='parameter', file_id='F')],
        call_references=[CallReference(call_id='c', file_id='F', caller_function_id='fn', location=location,
            expression='f()', resolution='resolved', reason='test fixture', target_function_id='fn', target_graph_id='function')],
        diagnostics=[Diagnostic(severity='info', code='FIXTURE', message='Manually constructed example')])


class ModelTests(unittest.TestCase):
    def test_nested_serialization(self):
        analysis = example_analysis()
        data = json.loads(analysis.to_json())
        self.assertEqual(data['graphs']['function']['nodes'][0]['label'], 'café')
        self.assertIsNone(data['graphs']['function']['nodes'][1]['sourceLocation'])
        self.assertEqual(data['functions'][0]['parameters'][0]['hasDefault'], False)
        self.assertEqual(data['sourceMappings'][0]['location']['fileId'], 'F')
        self.assertEqual(data['callReferences'][0]['targetGraphId'], 'function')
        self.assertEqual(analysis.to_json(), analysis.to_json())
        data['graphs'].clear()
        self.assertEqual(len(analysis.graphs), 2)

    def test_serialization_order_is_deterministic(self):
        first = example_analysis()
        second = example_analysis()
        second.graphs = dict(reversed(list(second.graphs.items())))
        self.assertEqual(first.to_json(), second.to_json())

    def test_source_spans(self):
        valid = SourceLocation(file_id='F', start_line=1, start_column=10, end_line=2, end_column=0)
        self.assertEqual(valid.to_dict()['endColumn'], 0)
        for updates in [dict(start_line=0), dict(start_column=-1), dict(end_line=0),
                        dict(end_line=1, end_column=9), dict(start_line=True)]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                replace(valid, **updates)

    def test_required_and_invalid_typed_fields(self):
        with self.assertRaises(TypeError):
            FlowNode(node_id='n')
        with self.assertRaises(ValueError):
            FlowNode(node_id='n', node_type='invented', label='x')
        with self.assertRaises(ValueError):
            ProjectInput(project_id='P', project_name='P', revision_id=True, files=[])
        with self.assertRaises(ValueError):
            Diagnostic(severity='fatal', code='X', message='x')
        with self.assertRaises(ValueError):
            FlowNode(node_id='', node_type='end', label='x')

    def test_duplicate_input_ids_direct_construction(self):
        file = FileInput(file_id='F', file_name='f.py', file_path='f.py', file_content='')
        with self.assertRaises(ValueError):
            ProjectInput(project_id='P', project_name='P', revision_id=0, files=[file, file])

    def test_duplicate_graph_node_and_edge_ids(self):
        graph = example_analysis().graphs['function']
        with self.assertRaises(ValueError):
            replace(graph, nodes=graph.nodes + [graph.nodes[0]])
        with self.assertRaises(ValueError):
            replace(graph, edges=graph.edges * 2)

    def test_missing_edge_endpoints_and_owners(self):
        graph = example_analysis().graphs['function']
        with self.assertRaises(ValueError):
            replace(graph, edges=[replace(graph.edges[0], target_id='missing')])
        with self.assertRaises(ValueError):
            replace(graph, function_id=None)
        with self.assertRaises(ValueError):
            replace(graph, status='unsupported')

    def test_duplicate_result_ids_and_graph_key(self):
        analysis = example_analysis()
        for field_name in ['files', 'functions', 'call_references']:
            with self.subTest(field_name=field_name), self.assertRaises(ValueError):
                replace(analysis, **{field_name: getattr(analysis, field_name) * 2})
        with self.assertRaises(ValueError):
            replace(analysis, graphs={'wrong': analysis.graphs['file']})

    def test_missing_mapping_and_navigation_targets(self):
        analysis = example_analysis()
        with self.assertRaises(ValueError):
            replace(analysis, source_mappings=[replace(analysis.source_mappings[0], node_id='missing')])
        with self.assertRaises(ValueError):
            replace(analysis, graph_references=[replace(analysis.graph_references[0], target_graph_id='missing')])
        with self.assertRaises(ValueError):
            replace(analysis, functions=[replace(analysis.functions[0], graph_id='missing')])

    def test_calls_require_complete_resolved_targets(self):
        call = example_analysis().call_references[0]
        with self.assertRaises(ValueError):
            replace(call, target_graph_id=None)
        with self.assertRaises(ValueError):
            replace(call, resolution='unresolved')
        with self.assertRaises(ValueError):
            replace(example_analysis(), call_references=[replace(call, target_function_id='missing')])

    def test_independent_mutable_defaults(self):
        first = ProjectAnalysis(project_id='P', project_name='P', revision_id=1, status='success')
        second = replace(first, revision_id=2, diagnostics=[])
        first.diagnostics.append(Diagnostic(severity='info', code='X', message='x'))
        self.assertEqual(second.diagnostics, [])
        third = ProjectAnalysis(project_id='Q', project_name='Q', revision_id=1, status='success')
        self.assertEqual(third.diagnostics, [])

    def test_serialization_revalidates_mutation(self):
        analysis = example_analysis()
        analysis.graphs['function'].nodes.append(analysis.graphs['function'].nodes[0])
        with self.assertRaises(ValueError):
            analysis.to_json()
        analysis = example_analysis()
        analysis.functions[0].parameters[0].has_default = 'wrong'
        with self.assertRaises(ValueError):
            analysis.to_json()

    def test_failure_envelope_can_have_unknown_identity(self):
        result = ProjectAnalysis(project_id=None, project_name=None, revision_id=None, status='failed')
        self.assertIsNone(json.loads(result.to_json())['projectId'])
        with self.assertRaises(ValueError):
            replace(result, status='success')

    def test_inconsistent_metadata_mapping_and_call_graph(self):
        analysis = example_analysis()
        for updates in [
            {'files': [replace(analysis.files[0], file_id='unknown')]},
            {'functions': [replace(analysis.functions[0], file_id='unknown')]},
            {'source_mappings': [replace(analysis.source_mappings[0],
                location=replace(analysis.source_mappings[0].location, end_column=3))]},
            {'call_references': [replace(analysis.call_references[0], target_graph_id='file')]},
        ]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                replace(analysis, **updates)
