"""Phase 2 model shape, graph-local identity and mutable-record integrity."""
import ast
import json
import unittest
from dataclasses import replace

from flowbridge_analysis.models import FlowEdge, FlowNode, GraphModel, ProjectAnalysis
from test_models import example_analysis


class CompleteModelTests(unittest.TestCase):
    def test_graph_type_and_legacy_keyword_share_one_field(self) -> None:
        graph = GraphModel(graph_id='g', graph_type='project', status='complete')
        legacy = GraphModel(graph_id='g', view_type='project', status='complete')
        self.assertEqual(graph, legacy)
        self.assertEqual(graph.to_dict(), {
            'graphId': 'g', 'graphType': 'project', 'status': 'complete',
            'fileId': None, 'functionId': None, 'nodes': [], 'edges': [],
        })
        self.assertEqual(graph.view_type, graph.graph_type)
        self.assertEqual(replace(graph, graph_id='other').graph_type, 'project')
        graph.view_type = 'unknown'
        with self.assertRaises(ValueError):
            graph.to_dict()

    def test_missing_invalid_and_conflicting_graph_types(self) -> None:
        with self.assertRaises(TypeError):
            GraphModel(graph_id='g', status='complete')
        for arguments in [dict(graph_type='unknown'), dict(graph_type='project', view_type='file')]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                GraphModel(graph_id='g', status='complete', **arguments)

    def test_edge_label_is_optional_typed_and_serialized(self) -> None:
        edge = FlowEdge(edge_id='e', source_id='a', target_id='b', edge_type='true')
        self.assertIsNone(edge.to_dict()['label'])
        self.assertEqual(replace(edge, label='yes').to_dict()['label'], 'yes')
        with self.assertRaises(ValueError):
            replace(edge, label=1)

    def test_graph_collection_defaults_are_independent(self) -> None:
        first = GraphModel(graph_id='a', graph_type='project', status='complete')
        second = GraphModel(graph_id='b', graph_type='project', status='complete')
        first.nodes.append(FlowNode(node_id='n', node_type='file', label='file'))
        self.assertEqual(second.nodes, [])
        self.assertEqual(second.edges, [])

    def test_mutated_child_records_rejected_on_parent_construction(self) -> None:
        analysis = example_analysis()
        node = analysis.graphs['function'].nodes[0]
        node.source_location.start_line = 0
        with self.assertRaises(ValueError):
            replace(analysis)
        analysis = example_analysis()
        edge = analysis.graphs['function'].edges[0]
        edge.edge_type = 'not-an-edge'
        with self.assertRaises(ValueError):
            replace(analysis.graphs['function'])

    def test_raw_asts_rejected_at_construction_and_serialization(self) -> None:
        tree = ast.parse('x = 1')  # Inspect source only; never execute it.
        with self.assertRaises(ValueError):
            FlowNode(node_id='n', node_type='statement', label=tree)
        for container in ('label', 'nodes', 'graphs'):
            with self.subTest(container=container):
                analysis = example_analysis()
                if container == 'label':
                    analysis.graphs['function'].nodes[0].label = tree
                elif container == 'nodes':
                    analysis.graphs['function'].nodes.append(tree)
                else:
                    analysis.graphs['ast'] = tree
                with self.assertRaises(ValueError):
                    analysis.to_dict()

    def test_dangling_navigation_source_graph_and_node_rejected(self) -> None:
        analysis = example_analysis()
        reference = analysis.graph_references[0]
        for change in (dict(source_graph_id='missing'), dict(source_node_id='missing'),
                       dict(target_graph_id='missing')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(analysis, graph_references=[replace(reference, **change)])

    def test_dangling_and_duplicate_source_mappings_rejected(self) -> None:
        analysis = example_analysis()
        mapping = analysis.source_mappings[0]
        for change in (dict(graph_id='missing'), dict(node_id='missing')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(analysis, source_mappings=[replace(mapping, **change)])
        with self.assertRaisesRegex(ValueError, 'Duplicate source mapping'):
            replace(analysis, source_mappings=[mapping, mapping])

    def test_node_ids_are_graph_local_and_mapping_lookup_is_unambiguous(self) -> None:
        analysis = example_analysis()
        overview_node = analysis.graphs['file'].nodes[0]
        # Deliberately reuse a local ID in another graph with a different span.
        overview_node.node_id = 'statement'
        overview_node.source_location = replace(overview_node.source_location, end_column=3)
        analysis.graph_references[0].source_node_id = 'statement'
        result = replace(analysis)
        self.assertEqual(result.source_mappings[0].location.end_column, 4)
        self.assertEqual(result.to_dict()['graphs']['file']['nodes'][0]['sourceLocation']['endColumn'], 3)

    def test_cross_graph_edge_endpoint_is_rejected(self) -> None:
        graph = example_analysis().graphs['function']
        edge = replace(graph.edges[0], target_id='function-node')
        with self.assertRaises(ValueError):
            replace(graph, edges=[edge])

    def test_call_source_and_caller_ownership_are_checked(self) -> None:
        analysis = example_analysis()
        call = analysis.call_references[0]
        changes = [dict(file_id='missing'), dict(caller_function_id='missing'),
                   dict(location=replace(call.location, file_id='missing'))]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(analysis, call_references=[replace(call, **change)])

    def test_complete_result_serializes_only_json_values(self) -> None:
        data = example_analysis().to_dict()
        def check(value: object) -> None:
            if isinstance(value, dict):
                self.assertTrue(all(isinstance(key, str) for key in value))
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
            else:
                self.assertIn(type(value), (str, int, bool, type(None)))
        check(data)
        self.assertEqual(json.loads(json.dumps(data)), data)
        self.assertEqual(data['graphs']['function']['graphType'], 'function')
        self.assertNotIn('viewType', data['graphs']['function'])
        self.assertIsNone(data['graphs']['function']['edges'][0]['label'])
