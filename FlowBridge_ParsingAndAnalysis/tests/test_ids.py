"""Deterministic revision and structural identity tests."""
import unittest
from flowbridge_analysis.RevisionIds import RevisionIds


class IdTests(unittest.TestCase):
    def test_repeatable_without_shared_counters(self):
        first = RevisionIds('P', 1)
        expected = first.make('node', 'F', 'f', 1)
        first.make('node', 'other', 100)
        self.assertEqual(expected, RevisionIds('P', 1).make('node', 'F', 'f', 1))

    def test_project_revision_kind_and_key_are_distinct(self):
        values = [RevisionIds('P', 1).make('node', 'F', 1),
                  RevisionIds('Q', 1).make('node', 'F', 1),
                  RevisionIds('P', 2).make('node', 'F', 1),
                  RevisionIds('P', 1).make('edge', 'F', 1),
                  RevisionIds('P', 1).make('node', 'F', 2)]
        self.assertEqual(len(set(values)), len(values))

    def test_delimiters_unicode_and_types_do_not_collide(self):
        ids = RevisionIds('P:é', 0)
        values = [ids.make('graph', 'a:b', 'c'), ids.make('graph', 'a', 'b:c'),
                  ids.make('graph', 1), ids.make('graph', '1'), ids.make('graph', 'é')]
        self.assertEqual(len(set(values)), len(values))
        self.assertTrue(all(value.isascii() for value in values))

    def test_invalid_identity_and_keys(self):
        for project, revision in [('', 1), ('P', True), ('P', -1), ('P', '1')]:
            with self.assertRaises(ValueError):
                RevisionIds(project, revision)
        for key in [(), (True,), (None,), ([],)]:
            with self.assertRaises(ValueError):
                RevisionIds('P', 1).make('node', *key)

class IdScopeTests(unittest.TestCase):
    def test_all_production_kinds_have_distinct_repeatable_ids(self) -> None:
        kinds = ('function', 'graph', 'node', 'edge', 'call', 'scope')
        identifiers = [RevisionIds('P', 0).make(kind, 'F', 1) for kind in kinds]
        self.assertEqual(len(set(identifiers)), len(kinds))
        self.assertEqual(identifiers, [RevisionIds('P', 0).make(kind, 'F', 1) for kind in kinds])

    def test_graph_owners_separate_local_node_and_edge_ordinals(self) -> None:
        identifiers = RevisionIds('P', 1)
        graphs = [identifiers.make('graph', 'function', file_id, 1, 0, 'f') for file_id in ('A', 'B')]
        local_ids = []
        for graph in graphs:
            for kind in ('node', 'edge'):
                for ordinal in range(3):
                    local_ids.append(identifiers.make(kind, graph, ordinal))
        self.assertEqual(len(set(local_ids)), 12)
        self.assertEqual(identifiers.make('node', graphs[0], 0), local_ids[0])

    def test_existing_fb1_format_is_preserved(self) -> None:
        self.assertEqual(RevisionIds('P', 1).make('node', 'F', 1),
                         'fb1_WyJQIiwxLCJub2RlIiwiRiIsMV0')

    def test_invalid_kinds_are_rejected(self) -> None:
        for kind in ('', '  ', None, 1, True):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                RevisionIds('P', 1).make(kind, 'F')

    def test_structural_tuple_boundaries_are_preserved(self) -> None:
        identifiers = RevisionIds('P', 1)
        keys = [('a', 'b'), ('a,b',), ('a', '', 'b'), ('[a,b]',), ('a', 1), ('a', '1')]
        values = [identifiers.make('call', *key) for key in keys]
        self.assertEqual(len(set(values)), len(keys))
