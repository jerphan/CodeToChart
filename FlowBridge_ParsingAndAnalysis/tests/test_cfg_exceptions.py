"""Additional fail-closed and exact exception topology checks."""
import unittest
from test_cfg_builder import build, links

class ExceptionSubsetTests(unittest.TestCase):
    def test_bare_handler_exact_paths(self):
        result = build('def f():\n    try:\n        work()\n    except:\n        recover()\n    pass')
        self.assertEqual(links(result), {
            ('Start', 'work()', 'next'), ('work()', 'Exception dispatch', 'exception'),
            ('Exception dispatch', 'except', 'exception'), ('except', 'recover()', 'next'),
            ('recover()', 'Exceptional End', 'exception'), ('work()', 'pass', 'next'),
            ('recover()', 'pass', 'next'), ('pass', 'End', 'next')})

    def test_nested_handler_try_rejected_without_paths(self):
        result = build('def f():\n    try:\n        work()\n    except:\n        try:\n            recover()\n        except:\n            pass')
        self.assertEqual(result.graph.status, 'unsupported')
        self.assertEqual(result.graph.edges, [])
        self.assertEqual(result.graph.nodes, [])
        self.assertTrue(any(d.code == 'UNSUPPORTED_FEATURE' for d in result.diagnostics))
