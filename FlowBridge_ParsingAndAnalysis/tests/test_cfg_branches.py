"""Exact sequence/branch/return connectivity, disambiguated by source location."""
from collections import Counter
import unittest
from test_cfg_builder import build


def connectivity(result) -> Counter:
    """Retain edge multiplicity and distinguish repeated labels on different lines."""
    positions = {}
    for node in result.graph.nodes:
        line = node.source_location.start_line if node.source_location else None
        positions[node.node_id] = (node.label, line)
    return Counter((positions[edge.source_id], positions[edge.target_id], edge.edge_type)
                   for edge in result.graph.edges)


class BranchConnectivityTests(unittest.TestCase):
    def assert_edges(self, source: str, expected: list) -> object:
        result = build(source)
        self.assertEqual(result.graph.status, 'complete')
        self.assertEqual(connectivity(result), Counter(expected))
        return result

    def test_sequence_and_implicit_end(self) -> None:
        self.assert_edges('def f():\n    x = 1\n    use(x)', [
            (('Start', None), ('x = 1', 2), 'next'),
            (('x = 1', 2), ('use(x)', 3), 'next'),
            (('use(x)', 3), ('End', None), 'next')])

    def test_if_else_merges_before_return(self) -> None:
        self.assert_edges('def f(x):\n    if x:\n        y = 1\n    else:\n        y = 2\n    return y', [
            (('Start', None), ('x', 2), 'next'),
            (('x', 2), ('y = 1', 3), 'true'), (('x', 2), ('y = 2', 5), 'false'),
            (('y = 1', 3), ('return y', 6), 'next'), (('y = 2', 5), ('return y', 6), 'next'),
            (('return y', 6), ('End', None), 'return')])

    def test_missing_else_preserves_false_edge(self) -> None:
        self.assert_edges('def f(x):\n    if x:\n        return 1\n    work()', [
            (('Start', None), ('x', 2), 'next'),
            (('x', 2), ('return 1', 3), 'true'), (('return 1', 3), ('End', None), 'return'),
            (('x', 2), ('work()', 4), 'false'), (('work()', 4), ('End', None), 'next')])

    def test_explicit_pass_else_preserves_source_backed_noop(self) -> None:
        self.assert_edges('def f(x):\n    if x:\n        work()\n    else:\n        pass\n    done()', [
            (('Start', None), ('x', 2), 'next'),
            (('x', 2), ('work()', 3), 'true'), (('x', 2), ('pass', 5), 'false'),
            (('work()', 3), ('done()', 6), 'next'), (('pass', 5), ('done()', 6), 'next'),
            (('done()', 6), ('End', None), 'next')])

    def test_nested_repeated_conditions_and_returns_stay_distinct(self) -> None:
        result = self.assert_edges('def f(x):\n    if x:\n        if x:\n            return 1\n'
                                  '        else:\n            return 1\n    else:\n        work()\n    done()', [
            (('Start', None), ('x', 2), 'next'), (('x', 2), ('x', 3), 'true'),
            (('x', 3), ('return 1', 4), 'true'), (('x', 3), ('return 1', 6), 'false'),
            (('return 1', 4), ('End', None), 'return'), (('return 1', 6), ('End', None), 'return'),
            (('x', 2), ('work()', 8), 'false'), (('work()', 8), ('done()', 9), 'next'),
            (('done()', 9), ('End', None), 'next')])
        self.assertEqual(len({node.node_id for node in result.graph.nodes}), len(result.graph.nodes))

    def test_elif_multiple_returns_omit_unreachable_statements(self) -> None:
        result = self.assert_edges('def f(x):\n    if x > 0:\n        return 1\n'
                                  '    elif x < 0:\n        return -1\n    else:\n        return 0\n'
                                  '    dead()\n    other()', [
            (('Start', None), ('x > 0', 2), 'next'),
            (('x > 0', 2), ('return 1', 3), 'true'), (('return 1', 3), ('End', None), 'return'),
            (('x > 0', 2), ('x < 0', 4), 'false'),
            (('x < 0', 4), ('return -1', 5), 'true'), (('return -1', 5), ('End', None), 'return'),
            (('x < 0', 4), ('return 0', 7), 'false'), (('return 0', 7), ('End', None), 'return')])
        self.assertEqual([(item.code, item.source_location.start_line) for item in result.diagnostics],
                         [('UNREACHABLE_STATEMENT', 8), ('UNREACHABLE_STATEMENT', 9)])
        self.assertFalse(any(mapping.location.start_line in (8, 9) for mapping in result.source_mappings))

    def test_bare_return_terminates_sequence(self) -> None:
        self.assert_edges('def f():\n    return\n    dead()', [
            (('Start', None), ('return', 2), 'next'), (('return', 2), ('End', None), 'return')])
