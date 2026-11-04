# Architecture and code audit — 2026-11-03

Historical snapshot: the findings/inventory below describe the named earlier
milestone, not current implementation. Service, resolver, hierarchy and outputs
are now implemented. See FINAL_REVIEW.md, PROGRESS.md and INTEGRATION_GUIDE.md
for the current status and verified limitations.

## Scope and evidence
Phase 0 snapshot, taken before Phase 1 application changes. Reviewed active Python
modules/classes, contracts, decisions and tests. No application code changed during
this phase. Baseline command with src on PYTHONPATH:
`python -m unittest discover -s tests -q` — 117 passed on the bundled Python runtime.
AST inventory found no duplicate class definitions and no cycles among explicit
relative module dependencies. Package import/alias tests also passed. This is not
a proof against every possible dynamic import or untested runtime behavior.

The approved UML images are not present in the supplied attachments/repository.
Responsibility comparisons below use the user's named classes and documented
architecture/contracts; exact UML signatures, multiplicities and relationships
remain unverified. No approved specification was changed to fit code.

## Component gap analysis

### ParsingAnalysisService
Missing: the file contains only a planning docstring, no class or orchestration.
Required role matches the proposed pipeline: fresh full-snapshot processing,
sibling failure isolation, status aggregation and ProjectAnalysis assembly.
Dependencies are not implemented; complexity and behavior tests cannot be assessed.
The integration test manually chains input/parser/feature stages, not this service.

### InputValidator (currently validator.py)
Implemented: validate_project and ValidationResult check all required project/file
fields, exact input values, nonnegative integer revisions excluding bool, duplicate
file IDs, malformed/duplicate-key/nonfinite JSON, non-JSON extensions and cycles.
Duplicate paths warn; source is untouched. Partial: class-aligned name/API missing.
Dependencies: models plus compatibility feature-validator exports; no parsing call.
Complexity: nested reporting/field helpers are justified; long conditions could be
formatted more clearly without redesign. Fifteen validation tests cover actual
acceptance, diagnostics, identity, roundtrip and isolation. Add explicit class API,
zero-revision and no-parser-call coverage in Phase 1. Structural diagnostics are
separate from PythonParser's SYNTAX_ERROR diagnostics.

### PythonParser and ParseResult
Implemented: ast.parse only, fresh AST/result, syntax/encoding/recursion diagnostics,
UTF-8 diagnostic spans and null/point fallback. Matches parsing responsibility;
models dependency is correct. Partial: parser acceptance is not compiler validation;
resource isolation and limits are missing. Span normalization is necessary complexity.
Twelve tests verify positions, invalid source, reuse and absence of execution side
effects; no full compiler validity claim is warranted.

### FeatureValidator and FeatureValidationResult
Implemented: explicit expression/statement allowlist and contextual loop/try checks,
unsupported diagnostics, conservative exception warning. Matches feature inspection;
imports parser location helper and Diagnostic, not input validation. Partial by
design: unsupported constructs are rejected, not implemented. Six-element traversal
work tuples and the long validate method are readability candidates, not a reason
to rewrite semantics. Fourteen focused tests plus CFG cases check behavior and AST
immutability. No full Python exception/type semantics.

### ASTAnalyzer, ASTAnalysis, CallSite and _FileAnalyzer
Implemented: direct function metadata, parameters, scopes, binding occurrences,
imports as metadata, syntactic calls and deterministic IDs. Dependencies on models,
RevisionIds, parser spans, FeatureValidator and SymbolTable match the architecture.
Partial: loop/try subtrees are omitted and flagged incomplete despite CFG support;
nested/class/async scopes and global/nonlocal resolution remain bounded omissions.
CallSite is not a resolved CallReference. Work stacks prevent scope leakage; compact
parameter/header expressions and long methods could be clarified incrementally.
Sixteen tests check ownership, shadowing, duplicate declarations, Unicode, header
calls and revision isolation; no service or runtime resolution coverage is implied.

### SymbolTable, ScopeInfo and BindingLookup
Implemented: scope/name index, all occurrences, nearest lexical lookup, incomplete
scope stop, ownership checks. Matches lexical lookup rather than call resolution;
models are its only internal dependency. Four tests verify shadowing, duplicates,
incomplete fallback and ownership. Mutable scope records require caller discipline:
changing parent IDs after insertion can invalidate the acyclic parent invariant.
No definite assignment, builtin index or complete Python name resolution. Three
indexes serve different lookup/order needs and are not duplicate implementations.

### CallResolver
Missing: planning docstring only, no class, dependencies or resolution algorithm.
CallReference records exist but do not resolve calls. Reserved test_call_resolver.py
contains no tests. Same-file direct calls are the first planned bounded subset.

### CFGBuilder, CFGResult, _Loop and _FunctionBuilder
Implemented: sequence/if/return, for/while/break/continue, bounded try/except,
unsupported empty graphs, deterministic IDs, spans and mappings at node creation.
Models/RevisionIds/parser spans/FeatureValidator dependencies are correct. Matches
function control-flow responsibility. Partial: expression-internal paths, nested
try/finally/else/raise and full exception semantics are unsupported; exceptions are
conservative possible paths. Thirty-three tests assert edges, joins, exits, handler
routing, IDs, mappings and reuse. Pending predecessors and loop/exception contexts
are necessary complexity; several important worker methods lack full input/output
docstrings. Do not replace them with a simpler but incorrect sequential traversal.

### ProjectGraphBuilder
Missing: planning docstring only. No project/file overview or navigation construction.
Role is documented; no imports/algorithm to verify. test_project_graphs.py is reserved
and contains no tests. Hand-built model fixtures are not builder coverage.

### RevisionIds
Implemented: immutable project/revision context; versioned, reversible compact-JSON
and URL-safe-base64 encoding of kind and structural key. No randomness or counters.
Standard-library dependencies only; matches supporting identity responsibility.
Four tests cover repeatability, distinct contexts/kinds/keys, delimiter/type/Unicode
separation and invalid inputs. Missing explicit tests for every production kind,
owner-scoped node/edge keys and a fixed format regression. Algorithm replacement
is unnecessary. Unique IDs require unique caller-supplied tuples; repeat calls with
the same tuple intentionally reuse the same ID. No stable identity across edits.

### ProjectAnalysis
Implemented: canonical dataclass, JSON serialization and checks for duplicate IDs,
graph ownership, navigation/mapping targets and resolved call targets. Concrete model
imports are acyclic. Matches the result-container role, not project orchestration.
Partial integrity: no full symbol/scope/caller/diagnostic ownership validation,
source-bound validation or one-mapping-per-source-node enforcement. Repeated scans
of graph nodes can cost O(mappings * nodes); acceptable small inputs, worth indexing
when integration establishes scale. Fourteen model tests exercise real serialization
and rejection behavior; they do not demonstrate generated project output.

### FlowchartOutput and MappingOutput
Both missing: outputs/__init__.py is a docstring-only scaffold. Documented projections
have not been implemented; no classes, dependencies, adapter behavior or tests exist.
They must derive from ProjectAnalysis without regenerating IDs.

## Remaining model classes (all inspected)
All use JsonModel and concrete sibling dependencies; no duplicate definitions.
Their documented JSON field shapes match the current input/output contract.
- JsonModel: recursive type checks and deterministic camelCase serialization; necessary
  reflection, not a general-purpose validation framework. No cyclic model support.
- ProjectInput: input identity/revision and unique file IDs; FileInput: source snapshot.
- FileMetadata: file/overview link and status; no overview generation.
- FunctionInfo: identity, parameters, source span and graph/scope links; validates span.
- ParameterInfo: parameter kind/default flag/annotation text; no expression evaluation.
- FlowNode: node kind/label/location; FlowEdge: edge kind/endpoints, no topology algorithm.
- GraphModel: local uniqueness, owner/view rules, endpoints, empty unsupported graphs.
- SourceLocation: ordered UTF-8 byte span; does not know source bounds.
- SourceMapping: graph/node/location; cross-record checks belong to ProjectAnalysis.
- GraphReference: navigation record, separate from control-flow edges.
- Diagnostic: typed severity/message/context; does not aggregate project status.
- SymbolInfo: binding record, not a resolver.
- CallReference: resolution category/targets; validates target presence, not inference.
Model tests cover JSON shape and integrity; analyzer/CFG tests cover production of
many records. Dedicated test_source_mapping.py is empty; mapping coverage currently
lives in model/parser/CFG tests. There is no output-adapter coverage.

## Cross-cutting findings and priorities
1. High: project-level pipeline and both downstream projections are absent. Do not
   describe the module as an end-to-end analyzer yet.
2. Medium: CFG support is broader than lexical extraction. Keep INCOMPLETE_SCOPE
   diagnostics until loop/handler bindings are implemented; resolution must not guess.
3. Medium: canonical integrity checks are incomplete (see ProjectAnalysis). Establish
   additional invariants with tests before exposing integrated results.
4. Low: InputValidator class/module naming is inconsistent with the requested list.
   Phase 1 can fix this while keeping validate_project and legacy imports.
5. Low: model extraction left unused field and Literal imports in multiple files.
   Public re-exports in initializers/validator are intentional, not dead code.
   Old __pycache__ entries are artifacts, not duplicate source classes. No broad
   dead-code proof was attempted; public helpers may have external callers.
6. Low: compatibility module aliases add import machinery, but preserve the existing
   API with one implementation. Runtime import/identity checks pass.
7. Documentation: DATA_MODELS calls 60 tests current; PARSING_FEATURES calls 113 current;
   ARCHITECTURE uses present tense for the absent service entry point; the plan says
   typed output records exist even though projection classes do not. Historical
   counts should be labeled historical, with TESTING/PROGRESS authoritative.
   DECISIONS' opening says all entries are October 29 despite D017's later date.

## Smallest next tasks
At the audit boundary: rename validator.py to InputValidator.py, expose a stateless
InputValidator.validate API backed by the existing behavior, retain compatibility,
and strengthen ID tests/documentation. This is the user's authorized Phase 1.
After Phase 1: implement only ProjectGraphBuilder's project/file overviews and
GraphReferences using existing function metadata/CFG IDs. Test empty/multiple files,
unsupported function targets, deterministic navigation and endpoint integrity before
adding service orchestration, projections or call resolution.

## Phase 1 disposition
The InputValidator naming/API gap is now resolved, with legacy imports preserved.
ID scope/format tests and documentation were expanded; 127 tests pass. Stale current
counts and service/output status wording were corrected in the relevant docs.
Unused model imports and broader semantic/integrity gaps remain intentionally
outside Phase 1. No claim of exact UML image verification is made.
