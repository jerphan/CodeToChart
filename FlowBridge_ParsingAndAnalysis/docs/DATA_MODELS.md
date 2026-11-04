# Data models and validation guide

These are in-memory records, not an analyzer. Constructors use keyword arguments.
Python attributes use snake_case; to_dict() and to_json() produce the existing
camelCase contract. Nothing here parses or executes Python source.

## Models and relationships
- **ProjectInput** holds project identity, revision and a list of **FileInput**
  snapshots. FileInput contains the supplied file identity, name, path and source
  text. It is separate from output metadata so source is not copied into results.
- **FileMetadata** describes an analyzed file and links to its overview graph.
  Its status uses complete/unsupported/failed. This is the Python name for the
  previously proposed FileInfo record; its JSON keys have not changed.
- **FunctionInfo** identifies a function within its file, records qualified name,
  scope, span and parameters, and links to its function graph. **ParameterInfo**
  records parameter name, kind, default presence and annotation text. No defaults
  or annotations are evaluated.
- **SourceLocation** is a half-open span tied to fileId: one-based lines, zero-based
  UTF-8 byte columns. It checks coordinate ordering, not actual source bounds.
- **FlowNode** describes a diagram node, type, label and optional SourceLocation.
  Synthetic Start/End nodes can have null locations.
- **FlowEdge** joins node IDs in the same graph and describes control flow.
  Storing an edge does not prove that its runtime path is valid.
- **GraphModel** owns nodes/edges and identifies a project/file/function view.
  It checks duplicate local IDs, endpoint existence and appropriate owner fields.
  Unsupported/failed graphs must be empty.
- **GraphReference** links a node in one graph to another graph for navigation.
  Opening a function view is not a runtime control-flow edge.
- **SourceMapping** links (graphId, nodeId) to a SourceLocation. In ProjectAnalysis,
  it must match the location attached to that node.
- **Diagnostic** carries severity, code, message and optional file/graph/source
  context. Input errors use JSON field paths in messages, not source coordinates.
- **SymbolInfo** stores binding name, kind, scope and optional declaration/import
  information. It is a typed record, not an implemented symbol table.
- **CallReference** records a call site, resolution category and optional targets.
  Both function and graph targets are mandatory only for resolved calls. This
  record does not perform call resolution.
- **ProjectAnalysis** groups metadata, graphs keyed by ID, symbols, calls, mappings,
  navigation and diagnostics for one revision. It rejects duplicate metadata IDs,
  mismatched graph keys/owners and dangling navigation/mapping/call targets.
  Failed envelopes may have unknown project identity fields set to null. Kevin's
  and Grace's adapters derive their outputs from this shared result.

## Design and serialization
Standard-library dataclasses expose readable, typed fields without a framework.
JsonModel checks types and enums on construction and serialization. Missing
constructor arguments raise TypeError; invalid values raise ValueError. Use
validate_project for untrusted input to receive diagnostics instead of exceptions.
Models are mutable for future graph construction and must not be shared across
requests. Collection defaults are fresh, serialization returns new containers,
null fields are retained, object keys are sorted and list/source order is preserved.
Models should form acyclic trees. Generic ProjectAnalysis JSON loading is not
implemented; construct output records explicitly. Input JSON can roundtrip through
validate_project.

## Validation algorithm
1. Decode JSON with duplicate-key and nonfinite-number rejection. Decoded dictionaries
   are also accepted, but all values must be acyclic JSON data, including extensions.
2. Check project and file fields without coercion; collect field diagnostics.
3. Track file IDs to reject duplicates. Exact duplicate paths warn about future
   import ambiguity while retaining both files. Paths are never read from disk.
4. Construct ProjectInput only when no errors remain. Warnings accompany valid
   input. Unknown fields are ignored; each request creates fresh state.

ValidationResult exposes project, diagnostics and is_valid. It is a Python helper,
not an additional downstream JSON contract.

```python
from flowbridge_analysis import RevisionIds, validate_project

result = validate_project({
    'projectId': 'P001', 'projectName': 'Calculator', 'revisionId': 1,
    'files': [{'fileId': 'F001', 'fileName': 'calculator.py',
               'filePath': 'calculator.py', 'fileContent': ''}],
})
if result.is_valid:
    snapshot_json = result.project.to_json()
    ids = RevisionIds(result.project.project_id, result.project.revision_id)
    graph_id = ids.make('graph', 'file', 'F001')
else:
    diagnostics_json = [item.to_dict() for item in result.diagnostics]
```

## Deterministic ID algorithm
RevisionIds encodes [projectId, revisionId, kind, ...structuralKey] as compact JSON
and URL-safe base64 prefixed with fb1_. This is reversible rather than hashed:
different tuples do not collide. JSON preserves boundaries and types (integer 1
is different from string '1'). No global counter exists. Use explicit owner and
position keys, e.g. make('node', graph_id, 3). Same tuple intentionally means the
same ID; callers must supply distinct keys for distinct objects. Source identity
is not discovered automatically. Revision changes change IDs; user IDs stay intact.
IDs may be long, are not secret and have no cross-revision stability guarantee.

## Tests and limits
33 unittest cases cover missing/invalid fields, duplicate IDs/keys, nonfinite JSON
and cycles, identity preservation, empty/multiple files, roundtrip, output JSON,
model relationships, source spans, dangling references, state isolation and IDs.
Those 33 tests describe the original foundation milestone. See TESTING.md for
the current suite. PythonParser and FeatureValidator
now exist (see PARSING_FEATURES.md). ASTAnalyzer and SymbolTable now implement
metadata and conservative lexical lookup (see AST_ANALYSIS.md). CFGBuilder now
generates function graphs (see CFG_DESIGN.md). Overview graphs, call resolution,
output adapters and full-snapshot reanalysis are now implemented. Source bounds, editor coordinate conversion, complete symbol/call/source
consistency and semantic graph correctness remain later tasks. Packaging installation
and resource limits are not validated. Starter code/tests remain reference-only.

## Class entry point and ID example — 2026-11-03
InputValidator validates structure; RevisionIds assigns deterministic analysis IDs.
For example (source text is data, even when syntactically invalid):
```python
from flowbridge_analysis import InputValidator, RevisionIds

result = InputValidator().validate({
    'projectId': 'P', 'projectName': 'Demo', 'revisionId': 0,
    'files': [{'fileId': 'F', 'fileName': 'demo.py',
               'filePath': 'demo.py', 'fileContent': 'def broken(:'}],
})
assert result.is_valid  # Syntax is checked later by PythonParser.
ids = RevisionIds(result.project.project_id, result.project.revision_id)
graph_id = ids.make('graph', 'function', 'F', 1, 0, 'f')
first_node = ids.make('node', graph_id, 0)
assert first_node == ids.make('node', graph_id, 0)
assert first_node != ids.make('edge', graph_id, 0)
```
Validation first checks JSON representability, then required fields/types and
uniqueness, then constructs a complete ProjectInput only when there are no errors.
The ID helper encodes the full tuple as JSON before base64, so separators inside
names cannot confuse boundaries and integer 1 differs from string '1'. No random
state, shared counters or changes to the existing fb1_ format were introduced.

## Phase 2 completion and simple relationship example
All nine core records are implemented. GraphModel stores graph_type (JSON graphType),
not a second copy of its former view_type field. FlowEdge.label is optional.
The shared serializer uses an explicit field loop, converts names to camelCase,
recursively copies supported containers, and invokes each model's validation.
It never serializes an AST or an object's arbitrary __dict__.

Think of ProjectAnalysis as the folder for one revision. Each GraphModel is one
diagram in the folder; FlowNodes are its boxes and FlowEdges connect those boxes.
Here is a manually constructed structural diagram, not a new parsing algorithm:
```python
from flowbridge_analysis.models import ProjectAnalysis, GraphModel, FlowNode, FlowEdge

start = FlowNode(node_id='start', node_type='start', label='Start')
end = FlowNode(node_id='end', node_type='end', label='End')
edge = FlowEdge(edge_id='next', source_id='start', target_id='end',
                edge_type='next', label='continue')
graph = GraphModel(graph_id='demo', graph_type='project', status='complete',
                   nodes=[start, end], edges=[edge])
analysis = ProjectAnalysis(project_id='P', project_name='Demo', revision_id=1,
                           status='success', graphs={'demo': graph})
assert analysis.to_dict()['graphs']['demo']['graphType'] == 'project'
assert analysis.to_dict()['graphs']['demo']['edges'][0]['label'] == 'continue'
```
This minimal model example illustrates containment and endpoint checking; implemented
project/file overview builders emit their documented file/function nodes and
navigation references rather than these illustrative Start/End boxes.
Changing target_id to a missing node makes graph validation fail. GraphReference
connects a node to another diagram; it does not assert a control-flow path.
SourceMapping connects a graph/node pair to a source span. ProjectAnalysis checks
those relationships after all referenced graphs have been supplied.

Existing supporting records remain Diagnostic, FileInput, CallReference and
SymbolInfo (including import_target). No AnalysisDiagnostic, SourceFile,
CallRelationship duplicate class is introduced. CallRelationship aliases CallReference,
and ImportRelationship now exists as internal metadata (see CALL_RESOLUTION.md). Exact UML images were
not available, so completion is against the explicit Phase 2 fields and documented
contracts, not an asserted verification of unseen diagram details.
