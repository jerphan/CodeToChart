# Project context

## Purpose and users
FlowBridge is The Adaptables' Python source-code-to-flowchart web application for
CS 4366 Senior Capstone. Users upload Python files or repositories through the
Code Manager and navigate project, file, and function diagrams linked to source.
Future editing will submit updated snapshots and regenerate diagrams.

## Current requirements
- Analyze multiple Python source files supplied as structured JSON.
- Preserve project/file identifiers and return the input revision.
- Produce graph data, function metadata, symbols, calls, source mappings,
  navigation references, and diagnostics.
- Derive Visualization and Mapping contracts from one canonical ProjectAnalysis.
- Validate and parse untrusted source text without executing it.
- Analyze full snapshots independently in memory; invalid edits produce diagnostics.

## Non-goals and ownership
No SQL or other analysis database, saved workspace reopening, incremental parsing,
UI, layout, authentication, or upload/ZIP handling. SQL belongs only to account
and authentication features outside this module. Keep serializable models suitable
for future persistence without implementing storage now.

## Baseline inspection — 2026-10-29
The workspace contained no files, including no AGENTS.md, docs, source, tests,
package configuration, or reference starter. The parent directory contained only
this project directory. No implementation capabilities can therefore be verified.
The supplied master prompt is requirements text, not starter code.

## Evolution
The model/validation foundation is now implemented and verified with 33 tests.
PythonParser and initial FeatureValidator are now implemented (60 total tests);
ASTAnalyzer and SymbolTable now add metadata and conservative lexical lookup
(80 tests at that stage). CFGBuilder now generates function graphs (113 total
tests); full project orchestration is now implemented (see the current progress report). Consult PROGRESS.md
for current evidence and DATA_MODELS.md for implemented model relationships.

After the initial setup, the user supplied flowbridge_starter.zip as inspiration
and requested the modular directory layout. Source/reference separation and
the modular package now implements the bounded pipeline. The starter was inspected but not executed
or adopted as production code; see reference/README.md for its limitations.

First establish documentation; next implement validation, parsing, metadata,
CFGs, navigation, and call resolution in tested stages. Exception handling and
cross-file resolution require bounded, documented subsets. Future saved workspaces
remain deferred. Proposed defaults are identified in DECISIONS and are not
finalized teammate agreements.
