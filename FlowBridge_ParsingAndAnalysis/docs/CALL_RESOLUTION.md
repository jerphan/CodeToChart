# Static call resolution

## API and algorithm
`CallResolver.resolve(files, analyses) -> CallResolution` consumes the complete
FileInput snapshot and successful ASTAnalysis records. It never loads files,
executes source or imports uploaded modules. Failed files stay in the module index
so references to them are unresolved rather than classified as external.

For each extracted function-owned call, split a plain dotted callee into names.
Ask SymbolTable for the nearest lexical binding of the first name. Incomplete
scopes stop resolution; parameters/local assignments shadow outer declarations.
Repeated bindings are ambiguous because runtime assignment order is not modeled.
A unique function declaration supplies its existing functionId and graphId.
Missing unshadowed callable builtin names receive builtin status. Missing ordinary
names remain unresolved; there is no project-wide name search.

For an import binding, consult the exact ImportRelationship collected by
ASTAnalyzer. Only unconditional module-level absolute imports are supported:
`from calculator import add [as plus]` and `import calculator [as c]`.
Root-relative identifier-only .py paths define module names; pkg/calc.py is
pkg.calc, and pkg/__init__.py is pkg. Colliding module paths are ambiguous.
`import pkg.calc; pkg.calc.add()` is supported. Resolve only a direct function
binding in the selected module, never a re-export or arbitrary object attribute.
A module absent from this supplied index is external, not proven installed.
A present failed/incomplete module or missing export remains unresolved.

## Relationship ownership and contracts
CallRelationship is a Python alias of the existing CallReference, not a duplicate
class or new JSON schema. CallResolution.call_references contains those records;
import_relationships contains internal ImportRelationship dataclasses with file,
scope, binding name, module, member, relative level, source location and whether
the import is a direct module statement. ASTAnalysis.imports retains these records.
Its existing debug to_dict shape remains unchanged. Public ProjectAnalysis JSON
still uses callReferences and SymbolInfo.importTarget; no importRelationships key
has been added. These relationships are neither CFG edges nor GraphReferences.
Source positions remain one-based lines and zero-based UTF-8 byte columns.

Reserved target graph IDs do not create graphs. The service builds the
target graphs before placing resolved references into a validated ProjectAnalysis.
The caller must supply matching metadata from one project/revision and exact
snapshots, as with CFGBuilder; mixed revisions are not inferred or reconciled.

## Example
calculator.py defines `def add(a, b): return a + b`. main.py contains
`from calculator import add` and `def main(): return add(10, 5)`.
ASTAnalyzer records main's call site and the import binding. SymbolTable finds
that binding in main's module scope. The module index selects calculator.py;
lookup there finds its unique add declaration. The resulting CallReference uses
that declaration's functionId/graphId and main.py's original call location.
The import itself is metadata: module execution CFGs remain unsupported and their
existing feature diagnostics are retained.

## Limits
This is lexical candidate resolution, not proof of a runtime call target. No
module execution-order analysis, monkey-patching/attribute mutation analysis,
package initialization effects, dynamic sys.path, closures, assignment propagation,
relative/star imports, local/conditional imports, re-exports or dynamic callees.
Module-owned calls remain unresolved. Try and loop-else binding subtrees remain
omitted/incomplete; calls within those omitted subtrees are not fabricated.
Decorated/incomplete scopes do not acquire optimistic targets. Standard builtin
classification assumes the ordinary Python builtin namespace, without rebinding
through runtime namespace mutation. Imports can be analyzed as metadata even when
FeatureValidator reports module execution unsupported.


## Supported absolute imports — current behavior
Direct module-level `import module [as alias]` and
`from module import name [as alias]` (including multiple names) are accepted as
static metadata. They no longer produce UNSUPPORTED_FEATURE merely for being
imports. ASTAnalyzer records bindings/import relationships; CallResolver uses the
SymbolTable and project module index to resolve supported targets. No import is
executed and no module-execution CFG is claimed. Relative/star imports, future
directives, conditional imports and function-local imports remain unsupported.
Missing external modules have external call status rather than invented targets.
The calculator, imported calculator and order-reporting fixtures now return success.
Earlier partial-status observations for ordinary absolute imports are historical
and superseded by this correction. No input/output field names changed.
