"""FlowBridge models, input validation, safe AST parsing and feature inspection."""

from .RevisionIds import RevisionIds
from .CFGBuilder import CFGBuilder, CFGResult
from .ASTAnalyzer import ASTAnalysis, ASTAnalyzer, CallSite
from .CallResolver import CallResolver, CallResolution, CallRelationship
from .ImportRelationship import ImportRelationship
from .SymbolTable import BindingLookup, ScopeInfo, SymbolTable
from .PythonParser import ParseResult, PythonParser
from .FeatureValidator import FeatureValidationResult, FeatureValidator
from .InputValidator import InputValidator, ValidationResult, validate_project

__all__ = ['InputValidator', 'RevisionIds', 'ValidationResult', 'validate_project', 'ParseResult',
           'PythonParser', 'FeatureValidationResult', 'FeatureValidator',
           'ASTAnalysis', 'ASTAnalyzer', 'CallSite', 'BindingLookup', 'ScopeInfo', 'SymbolTable',
           'CFGBuilder', 'CFGResult', 'CallResolver', 'CallResolution',
           'CallRelationship', 'ImportRelationship']

# Legacy import paths share the canonical modules; no duplicate implementations.
import importlib as _importlib
import sys as _sys

_LEGACY_MODULES = {'validator': 'InputValidator', 'parser': 'PythonParser', 'ast_analyzer': 'ASTAnalyzer', 'symbol_table': 'SymbolTable', 'cfg_builder': 'CFGBuilder', 'ids': 'RevisionIds', 'service': 'ParsingAnalysisService', 'call_resolver': 'CallResolver', 'project_graph_builder': 'ProjectGraphBuilder'}
for _old, _new in _LEGACY_MODULES.items():
    _module = _importlib.import_module(f".{_new}", __name__)
    _sys.modules[f"{__name__}.{_old}"] = _module
    globals()[_old] = _module
del _old, _new, _module

from .ProjectGraphBuilder import ProjectGraphBuilder, ProjectGraphs
from .ParsingAnalysisService import ParsingAnalysisService
from .outputs import FlowchartOutput, MappingOutput
__all__ += ['ProjectGraphBuilder', 'ProjectGraphs', 'ParsingAnalysisService', 'FlowchartOutput', 'MappingOutput']

from .CodeManagerInputAdapter import CodeManagerInputAdapter
__all__ += ['CodeManagerInputAdapter']
