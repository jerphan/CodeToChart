# Python file organization — 2026-11-03

Historical snapshot: the findings/inventory below describe the named earlier
milestone, not current implementation. Service, resolver, hierarchy and outputs
are now implemented. See FINAL_REVIEW.md, PROGRESS.md and INTEGRATION_GUIDE.md
for the current status and verified limitations.

Structural refactoring only; classes, algorithms and JSON contracts are unchanged.
The attachment supplied a filename list, but no UML images were available for comparison.

## Original package files

- `__init__.py`
- `ast_analyzer.py`
- `call_resolver.py`
- `cfg_builder.py`
- `ids.py`
- `models.py`
- `outputs.py`
- `parser.py`
- `project_graph_builder.py`
- `service.py`
- `symbol_table.py`
- `validator.py`

## Renamed or moved files

- `parser.py` → `PythonParser.py`
- `ast_analyzer.py` → `ASTAnalyzer.py`
- `symbol_table.py` → `SymbolTable.py`
- `cfg_builder.py` → `CFGBuilder.py`
- `ids.py` → `RevisionIds.py`
- `service.py` → `ParsingAnalysisService.py`
- `call_resolver.py` → `CallResolver.py`
- `project_graph_builder.py` → `ProjectGraphBuilder.py`
- `models.py` → `models/` (class files below and re-exporting `__init__.py`).
- `outputs.py` → `outputs/__init__.py` (existing docstring-only scaffold).
- `validator.py` retains JSON validation; FeatureValidator and FeatureValidationResult moved to `FeatureValidator.py`. Its old exports remain available.

## Classes extracted from models.py

- `JsonModel` → `models/JsonModel.py`
- `FileInput` → `models/FileInput.py`
- `ProjectInput` → `models/ProjectInput.py`
- `FileMetadata` → `models/FileMetadata.py`
- `SourceLocation` → `models/SourceLocation.py`
- `ParameterInfo` → `models/ParameterInfo.py`
- `FunctionInfo` → `models/FunctionInfo.py`
- `FlowNode` → `models/FlowNode.py`
- `FlowEdge` → `models/FlowEdge.py`
- `GraphModel` → `models/GraphModel.py`
- `GraphReference` → `models/GraphReference.py`
- `SourceMapping` → `models/SourceMapping.py`
- `Diagnostic` → `models/Diagnostic.py`
- `SymbolInfo` → `models/SymbolInfo.py`
- `CallReference` → `models/CallReference.py`
- `ProjectAnalysis` → `models/ProjectAnalysis.py`

Shared type aliases and serialization/validation helpers remain in `models/JsonModel.py`.
Each model imports concrete dependency modules, avoiding package-level cycles.
Component helper/result classes stay beside their owning component.

## New package files

- `__init__.py`
- `ASTAnalyzer.py`
- `CallResolver.py`
- `CFGBuilder.py`
- `FeatureValidator.py`
- `models/__init__.py`
- `models/CallReference.py`
- `models/Diagnostic.py`
- `models/FileInput.py`
- `models/FileMetadata.py`
- `models/FlowEdge.py`
- `models/FlowNode.py`
- `models/FunctionInfo.py`
- `models/GraphModel.py`
- `models/GraphReference.py`
- `models/JsonModel.py`
- `models/ParameterInfo.py`
- `models/ProjectAnalysis.py`
- `models/ProjectInput.py`
- `models/SourceLocation.py`
- `models/SourceMapping.py`
- `models/SymbolInfo.py`
- `outputs/__init__.py`
- `ParsingAnalysisService.py`
- `ProjectGraphBuilder.py`
- `PythonParser.py`
- `RevisionIds.py`
- `SymbolTable.py`
- `validator.py`

## Imports and compatibility

Internal imports and active tests use PascalCase component paths. Package-level
exports and `flowbridge_analysis.models` exports remain available. Old component
module paths alias the same module objects in package initialization, preserving
existing callers without duplicate classes. JSON validation remains in validator.py
because it exposes a function, not a UML-named validator class.

## Differences and limitations

FlowchartOutput and MappingOutput classes do not exist yet; no empty class files
were invented. Service, call resolver and project graph builder remain renamed
docstring-only scaffolds. Existing names Diagnostic, ProjectInput and FileInput
are preserved rather than renamed to AnalysisDiagnostic, InputFromCodeManager or
SourceFile. ProjectAnalysis construction/serialization exists; automated project
assembly and output projections remain pending. No teammate/reference code changed.

## Validation

Before refactoring: `python -m unittest discover -s tests -q`: 113 tests passed.
After refactoring: the same command passed 117 tests (zero failures/errors).
`python examples/show_symbols.py` succeeded with zero diagnostics.
See TESTING.md for the exact runtime path and commands. Recommended next task: phase 6 overview
graphs and canonical output integration.

## Phase 1 follow-up — 2026-11-03
The inventory above records the earlier refactor. Subsequently `validator.py` was
renamed to `InputValidator.py`, with InputValidator.validate delegating to the
existing validate_project function. Old validator imports alias the new module.
The class is exported from the package; FeatureValidator remains separate.
