# Source mapping and navigation

Status: SourceLocation and SourceMapping models are implemented, with coordinate
ordering and referenced-node consistency checks. CFGBuilder now creates one mapping
per source-backed function node; synthetic nodes have no mappings. Parser/feature diagnostics now carry AST or normalized SyntaxError spans;
source bounds and editor conversion remain planned. See PARSING_FEATURES.md.

AST start/end lines are one-based. Columns are zero-based **UTF-8 byte offsets**;
end positions are exclusive. Editors may count UTF-16 code units or Unicode
characters, so Grace must convert against the exact revision's source text.
Do not derive positions from labels or assume bytes equal characters.

Attach SourceLocation from AST metadata when creating statement/expression nodes.
Start, End and joins may have null locations and no SourceMapping record.
Function spans use definition AST positions; document separately if decorators
are later included. ASTAnalyzer now copies these spans into FunctionInfo (excluding
decorator lines), parameter/binding AST spans into SymbolInfo, and full call spans
into CallSite. Parameter spans can include annotation text; assignment bindings
use the target Name span. Source expressions use ast.get_source_segment against
the exact snapshot. No node mappings are generated without CFGs.
File overview locations may be null where no meaningful AST
span exists. SyntaxError offsets require deliberate normalization: they are not
automatically interchangeable with AST UTF-8 byte columns. If reliable positions
are unavailable, emit null rather than fabricated coordinates.

Node-to-source lookup uses `(graphId, nodeId)`. Reverse lookup returns all mappings
whose half-open spans contain the requested position; overlapping/nested spans
are valid, so there is no promise of one unique match. Initial consumers may scan
the mapping array; a dedicated index is optional and deferred.

Project file nodes link to file graphs; file function nodes link to function
graphs. GraphReference is a navigation link, never an execution edge. Resolved
CallReference targets permit jumping to the called function graph; unresolved
calls must not fabricate links. Multiple calls may occur within one statement.

Validate that every mapping node exists, every reference source node and target
graph exists, and every resolved call targets known function metadata/graphs.
File IDs in locations must belong to the input. Check spans against source bounds,
including non-ASCII text, multiline statements, CRLF and empty source.

Each output includes revisionId. Analyze a fresh complete snapshot each request;
never reuse mappings from previous revisions. The frontend discards outdated
results. Stable node identity across edits is deferred.

## Phase 2 integrity checks
ProjectAnalysis builds a request-local (graphId, nodeId) index for checking
navigation and source mappings. Duplicate source mappings for one graph/node are
rejected, and each supplied mapping must equal the node's sourceLocation. Reusing
a nodeId in a different graph is valid. Different nodes may still map to overlapping
source spans. Nested locations are revalidated after mutation. Source text bounds
and complete mapping coverage still require the producer/integration stage.

## Phase 7 overview mappings and Phase 8 assembly
Project file nodes are structural with null source locations and no mappings.
File function nodes use the FunctionInfo definition span copied from AST metadata;
each receives exactly one SourceMapping. Those spans may overlap function CFG
node spans intentionally. Empty/failed files have no fabricated source positions.
GraphReferences connect project file nodes to file graphs and file function nodes
to existing CFGs, including explicitly unsupported empty targets. They are never
execution edges. The service verifies every source-backed node has exactly one
mapping; ProjectAnalysis validates each node/location and target identity.
Both consumer outputs preserve the canonical revision and IDs. Unicode/CRLF source
mapping integration is tested. General source-bound validation for arbitrary
externally constructed models and editor coordinate conversion remain deferred.

## Full-snapshot reanalysis lifecycle
Every service call creates a new RevisionIds context and new intermediate results.
No AST/table/CFG/mapping cache is retained. A changed revision rebuilds unchanged
files too; all generated IDs include project and revision. Removing a function or
file removes its current metadata, graphs and mappings. Syntax-invalid edited
files keep an empty failed file view and diagnostics, never previous executable
nodes. Valid siblings are rebuilt. Consumers must replace complete result sets.

The frontend should accept only responses whose projectId AND revisionId match
its current requested snapshot, and pair both projections from that same revision.
RevisionIds does not enforce monotonicity or detect reused revision numbers. The
caller must issue a distinct revision for changed content. See INTEGRATION_GUIDE.md.
