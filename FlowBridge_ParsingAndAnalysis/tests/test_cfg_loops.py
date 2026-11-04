"""Loop completion, terminal controls and loop-else ownership regression tests."""
from collections import Counter
import unittest
from test_cfg_builder import build, links, node
from test_cfg_branches import connectivity


class LoopCompletionTests(unittest.TestCase):
    def test_while_else_exact_connectivity(self) -> None:
        result = build('def f(x):\n    while x:\n        work()\n    else:\n        exhausted()\n    done()')
        self.assertEqual(connectivity(result), Counter([
            (('Start', None), ('x', 2), 'next'), (('x', 2), ('work()', 3), 'true'),
            (('work()', 3), ('Loop back', None), 'next'), (('Loop back', None), ('x', 2), 'back'),
            (('x', 2), ('exhausted()', 5), 'false'), (('exhausted()', 5), ('done()', 6), 'next'),
            (('done()', 6), ('End', None), 'next')]))

    def test_for_else_break_and_continue_exact_connectivity(self) -> None:
        result = build('def f(xs):\n    for x in xs:\n        if x:\n            break\n'
                       '        continue\n        dead()\n    else:\n        exhausted()\n    done()')
        self.assertEqual(connectivity(result), Counter([
            (('Start', None), ('Iterate: xs', 2), 'next'),
            (('Iterate: xs', 2), ('Next: x', 2), 'next'),
            (('Next: x', 2), ('x', 3), 'true'), (('x', 3), ('break', 4), 'true'),
            (('x', 3), ('continue', 5), 'false'), (('continue', 5), ('Next: x', 2), 'continue'),
            (('Next: x', 2), ('exhausted()', 8), 'false'),
            (('exhausted()', 8), ('done()', 9), 'next'), (('break', 4), ('done()', 9), 'break'),
            (('done()', 9), ('End', None), 'next')]))
        self.assertEqual([(d.code, d.source_location.start_line) for d in result.diagnostics],
                         [('UNREACHABLE_STATEMENT', 6)])

    def test_literal_false_runs_else_without_body(self) -> None:
        result = build('def f():\n    while False:\n        dead()\n    else:\n        exhausted()\n    done()')
        self.assertEqual(links(result), {('Start', 'False', 'next'), ('False', 'exhausted()', 'false'),
                                       ('exhausted()', 'done()', 'next'), ('done()', 'End', 'next')})
        self.assertEqual(result.diagnostics[0].source_location.start_line, 3)

    def test_literal_true_break_bypasses_unreachable_else(self) -> None:
        result = build('def f():\n    while True:\n        break\n    else:\n        dead_else()\n    done()')
        self.assertEqual(links(result), {('Start', 'True', 'next'), ('True', 'break', 'true'),
                                       ('break', 'done()', 'break'), ('done()', 'End', 'next')})
        self.assertEqual(result.diagnostics[0].source_location.start_line, 5)

    def test_infinite_continue_omits_else_and_following_statement(self) -> None:
        result = build('def f():\n    while True:\n        continue\n    else:\n        dead_else()\n    dead_after()')
        self.assertEqual(links(result), {('Start', 'True', 'next'), ('True', 'continue', 'true'),
                                       ('continue', 'True', 'continue')})
        self.assertEqual([d.source_location.start_line for d in result.diagnostics], [5, 6])

    def test_early_return_never_enters_else(self) -> None:
        result = build('def f(xs):\n    for x in xs:\n        return x\n    else:\n        return 0\n    dead()')
        self.assertEqual(links(result), {('Start', 'Iterate: xs', 'next'), ('Iterate: xs', 'Next: x', 'next'),
                                       ('Next: x', 'return x', 'true'), ('return x', 'End', 'return'),
                                       ('Next: x', 'return 0', 'false'), ('return 0', 'End', 'return')})
        self.assertEqual(result.diagnostics[0].source_location.start_line, 6)

    def test_inner_break_bypasses_only_inner_else(self) -> None:
        result = build('def f(xs, ys):\n    for x in xs:\n        for y in ys:\n            break\n'
                       '        else:\n            inner_done()\n        after_inner()\n'
                       '    else:\n        outer_done()\n    done()')
        edges = links(result)
        self.assertIn(('break', 'after_inner()', 'break'), edges)
        self.assertNotIn(('break', 'inner_done()', 'break'), edges)
        self.assertNotIn(('break', 'done()', 'break'), edges)
        self.assertIn(('Next: y', 'inner_done()', 'false'), edges)
        self.assertIn(('Next: x', 'outer_done()', 'false'), edges)
        self.assertIn(('Loop back', 'Next: x', 'back'), edges)

    def test_inner_else_controls_outer_loop(self) -> None:
        for control, target in [('break', 'done()'), ('continue', 'Next: x')]:
            with self.subTest(control=control):
                result = build('def f(xs, ys):\n    for x in xs:\n        for y in ys:\n            work()\n'
                               '        else:\n            ' + control + '\n        dead()\n'
                               '    else:\n        outer_done()\n    done()')
                self.assertEqual(result.graph.status, 'complete')
                edges = links(result)
                self.assertIn((control, target, control), edges)
                self.assertNotIn((control, 'Next: y', control), edges)
                self.assertNotIn((control, 'outer_done()', control), edges)
                self.assertNotIn('dead()', [item.label for item in result.graph.nodes])

    def test_loop_else_control_without_outer_loop_is_rejected(self) -> None:
        for control in ('break', 'continue'):
            result = build('def f(xs):\n    for x in xs:\n        pass\n    else:\n        ' + control)
            self.assertEqual(result.graph.status, 'unsupported')
            self.assertEqual(result.graph.nodes, [])
            self.assertEqual(result.source_mappings, [])
            self.assertTrue(any(d.code == 'UNSUPPORTED_FEATURE' for d in result.diagnostics))

    def test_nested_loop_inside_else_has_its_own_context(self) -> None:
        result = build('def f(xs, ys):\n    for x in xs:\n        pass\n    else:\n'
                       '        for y in ys:\n            break\n        after_nested()\n    done()')
        self.assertEqual(result.graph.status, 'complete')
        self.assertIn(('break', 'after_nested()', 'break'), links(result))
        self.assertNotIn(('break', 'done()', 'break'), links(result))

    def test_exception_path_bypasses_loop_else(self) -> None:
        result = build('def f(xs):\n    try:\n        for x in xs:\n            work()\n'
                       '        else:\n            exhausted()\n    except:\n        recover()\n    done()')
        self.assertEqual(result.graph.status, 'complete')
        edges = links(result)
        self.assertIn(('work()', 'Exception dispatch', 'exception'), edges)
        self.assertIn(('Next: x', 'exhausted()', 'false'), edges)
        self.assertNotIn(('Exception dispatch', 'exhausted()', 'exception'), edges)
        self.assertIn(('recover()', 'done()', 'next'), edges)

    def test_loop_else_integrity_determinism_and_revision_isolation(self) -> None:
        source = 'def f(xs):\n    for x in xs:\n        use(x)\n    else:\n        done()'
        first, second, revised = build(source), build(source), build(source, 2)
        self.assertEqual(first.graph.to_json(), second.graph.to_json())
        self.assertNotEqual(first.graph.graph_id, revised.graph.graph_id)
        nodes = {item.node_id: item for item in first.graph.nodes}
        self.assertEqual(len(nodes), len(first.graph.nodes))
        self.assertEqual(len({item.edge_id for item in first.graph.edges}), len(first.graph.edges))
        for edge in first.graph.edges:
            self.assertIn(edge.source_id, nodes)
            self.assertIn(edge.target_id, nodes)
        for mapping in first.source_mappings:
            self.assertEqual(mapping.location, nodes[mapping.node_id].source_location)
            self.assertEqual(mapping.graph_id, first.graph.graph_id)
        self.assertEqual({m.node_id for m in first.source_mappings},
                         {n.node_id for n in first.graph.nodes if n.source_location is not None})
