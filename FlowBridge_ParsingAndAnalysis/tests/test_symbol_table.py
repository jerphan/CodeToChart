"""Lexical lookup semantics and symbol-table ownership invariants."""
import unittest
from flowbridge_analysis import ScopeInfo, SymbolTable
from flowbridge_analysis.models import SymbolInfo


class SymbolTableTests(unittest.TestCase):
    def setUp(self):
        self.table = SymbolTable()
        self.table.add_scope(ScopeInfo(scope_id='m', name='module', kind='module', file_id='F'))
        self.table.add_scope(ScopeInfo(scope_id='f', name='module.f', kind='function', file_id='F',
                                      parent_scope_id='m', function_id='fn'))

    def bind(self, scope, name, kind):
        self.table.bind(SymbolInfo(scope_id=scope, name=name, kind=kind, file_id='F'))

    def test_nearest_scope_shadows_parent(self):
        self.bind('m', 'x', 'module')
        self.assertEqual(self.table.lookup('f', 'x').scope_id, 'm')
        self.bind('f', 'x', 'parameter')
        self.bind('f', 'x', 'local')
        self.assertEqual([s.kind for s in self.table.lookup('f', 'x').bindings], ['parameter', 'local'])
        self.assertEqual(len(self.table.bindings('m', 'x')), 1)

    def test_incomplete_scope_stops_fallback(self):
        self.bind('m', 'x', 'module')
        self.table.mark_incomplete('f')
        result = self.table.lookup('f', 'x')
        self.assertEqual(result.bindings, [])
        self.assertFalse(result.is_complete)

    def test_missing_name_and_snapshot_lists(self):
        self.assertIsNone(self.table.lookup('f', 'missing').scope_id)
        self.assertTrue(self.table.lookup('f', 'missing').is_complete)
        self.bind('m', 'x', 'module')
        self.table.bindings('m', 'x').clear()
        self.table.symbols.clear()
        self.assertEqual(len(self.table.symbols), 1)

    def test_invalid_scope_and_symbol_ownership(self):
        with self.assertRaises(ValueError):
            self.table.add_scope(ScopeInfo(scope_id='m', name='duplicate', kind='module', file_id='F'))
        with self.assertRaises(ValueError):
            self.table.add_scope(ScopeInfo(scope_id='other', name='other', kind='function', file_id='G',
                                          parent_scope_id='m', function_id='fn2'))
        with self.assertRaises(ValueError):
            self.table.bind(SymbolInfo(scope_id='m', name='x', kind='module', file_id='G'))
        with self.assertRaises(KeyError):
            self.table.lookup('missing', 'x')
