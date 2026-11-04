# AST metadata and symbol tables

## Public entry points
`ASTAnalyzer.analyze(tree, file_input, ids) -> ASTAnalysis` consumes a successfully
parsed ast.Module, its exact FileInput snapshot, and RevisionIds(projectId,
revisionId). It returns file-local metadata, a SymbolTable, unresolved CallSite
records and diagnostics. Each call creates a new worker/table; multiple files
share the same ID context but never accidentally share lexical namespaces.

ASTAnalysis is an intermediate result, not ProjectAnalysis. Its to_dict() provides
a serializable development view. No ASTs, graphs, mappings or navigation references
are emitted. FunctionInfo.graphId reserves a future graph identity; it must not be
advertised as an existing graph until the graph-building phase creates it.
The existing downstream JSON schema is unchanged.

## Metadata extraction, step by step
1. Create a module scope using the supplied fileId and revision-scoped ID helper.
   A normalized slash-separated path without its extension supplies the display
   module name: pkg/calculator.py becomes pkg.calculator. This is not Python import
   resolution; __init__, duplicate paths and package roots are not inferred.
2. For each direct top-level FunctionDef, record FunctionInfo with its AST span,
   qualified name, parameters, scopeId and reserved graphId. IDs use fileId,
   definition line/byte column and name, so duplicate names remain distinct.
3. Record the declaration in module scope, then create a child function scope.
   Extract positional-only, ordinary, variadic positional, keyword-only and
   variadic keyword parameters in signature order. Align trailing positional
   defaults and per-keyword defaults; preserve annotation source text without
   evaluating it. Parameter symbols use ast.arg spans (including annotations).
4. Inspect function bodies and module statements with a local work stack. Record
   Name/Store occurrences from assignments, including tuple/starred unpacking,
   annotations and augmented assignment. Attribute/subscript writes do not declare
   their receiver names. Keep every binding occurrence, including branch assignments
   and statements after return. This is lexical information, not execution order.
5. Record each Call node with its exact source expression, callee expression,
   span, scope and enclosing function ID. directName exists only for a Name callee;
   attribute/chained calls have null directName. Calls are sorted by source span,
   not asserted execution order. Header defaults/decorators belong to module scope;
   annotation evaluation is deliberately not modeled and annotation calls are omitted.

CallSite uses callId, fileId, scopeId, callerFunctionId, location, expression,
calleeExpression and directName. It is an internal/debug record, not a resolved
CallReference. No builtin/external classification or function target is guessed.

## SymbolTable and lookup
ScopeInfo identifies a module/function scope, its file, parent and optional owning
function; isComplete describes lexical extraction only. A feature-unsupported
module assignment/import can still have completely extracted bindings.
SymbolInfo is the existing serializable record. Symbols are indexed by scope and
name; repeated assignments/declarations are retained rather than overwritten.
For function declarations functionId identifies the declared function; for locals
and parameters it remains null and ownership is available through scopeId.

- add_scope requires unique IDs and an existing same-file parent for functions.
- bind checks scope/file ownership and retains the occurrence.
- bindings returns occurrences in exactly one scope.
- lookup returns BindingLookup(scope_id, bindings, is_complete), starting locally
  and walking outward only if the current scope has no binding and is complete.
- mark_incomplete prevents optimistic fallback through unknown bindings.

For example, a parameter named calculate hides the module declaration. A local
assignment to calculate makes it local throughout the function, even if a call
appears earlier. lookup returns the local group, not the module function. It does
not say the name has been initialized: UnboundLocalError and branch reachability
are outside this stage. Duplicate definitions produce a group of declarations,
not a guessed last winner. Builtins are not supplied by this table.

Parent/scope records are request-owned, mutable data; callers should not mutate
identity or parent fields after insertion. Table properties return new list
containers but retain these records. No cross-request cache or database exists.

## Conservative boundaries
Nested/conditional FunctionDef, async declarations and classes bind their names
but their bodies/signatures are not descended into. Only direct synchronous
module functions receive FunctionInfo. A nested function declaration has null
functionId; its enclosing scope is marked incomplete. This prevents inner locals,
parameters or calls from being incorrectly attributed to the outer function.

Lambda/comprehension bodies and unsupported control-flow subtrees are omitted,
with an INCOMPLETE_SCOPE warning and isComplete=False. Try/loop-else/with/match and other
statements omitted by lexical extraction may introduce bindings, so lookup must not fall back
through them. A function containing global/nonlocal omits its entire body to avoid
mislabeling redirected assignments. Parameters are still retained.
Decorated/generic functions keep metadata but mark their function/module scopes
incomplete. Their targets are not resolved. No closure or dynamic dispatch support.

Imports are informational bindings: import a.b binds a, aliases bind the alias,
and from-imports retain a dotted importTarget (relative dots preserved). Nothing
is imported or resolved. Star imports mark scopes incomplete. Import statements
remain feature-unsupported for CFG purposes.
FeatureValidator diagnostics are included unchanged. Additional extraction warnings
explain incomplete scopes. Extraction of metadata from a feature-unsupported file
does not make its control flow supported. Syntax errors are handled by PythonParser
before this API. The caller must pair the AST with the exact source snapshot.

## Demonstration: calculator.py
Run `examples/show_symbols.py` with src on PYTHONPATH. Observed output:

- Module calculator: function calculate at line 1 and function main at line 8.
- Function calculator.calculate: parameter a at line 1, byte column 14; parameter b
  at byte column 17; local result assignments at lines 3 and 5, byte column 8.
- Function calculator.main: local answer at line 9, byte column 4.
- Unresolved calls in main: calculate(10, 5) at line 9 and print(answer) at line 10.
- All three scopes complete; zero diagnostics; no graphs constructed.

Both result bindings are retained because if/else branches may assign the same
local. print is a call spelling, not a module declaration or proven builtin target.

## Evidence and next work
16 analyzer tests cover calculator, parameter kinds/defaults, empty functions,
shadowing, assignment targets, duplicate declarations, files/revisions, Unicode
multiline spans, nested definitions, header evaluation scopes, annotations, imports,
global handling, expression scopes, chained calls and fresh state/JSON output.
Four table tests cover nearest-scope lookup, incomplete fallback, occurrence lists
and ownership. These joined an 80-test suite at that stage. CFGBuilder now adds
function graphs (113 total tests); call resolution is now implemented separately (CALL_RESOLUTION.md). Ordinary loop lexical bindings are now extracted; try bindings remain
conservatively incomplete even though basic try CFGs are supported.

## Requested Phase 4 refinement — 2026-11-03
Ordinary for/while loops are now walked in the same module/function scope. For
example `for item in values: result = use(item)` records item and result as local
bindings and use(item) as a call. Tests and iterable expressions are inspected too.
Break/continue do not introduce bindings. Loop-else remains conservatively omitted.
Even `while False: x = work()` contributes a lexical x binding and a syntactic
work call: extraction is not a reachability or definite-initialization claim.
Nested functions inside loops still bind their names but omit inner bodies and
mark the enclosing extraction incomplete. Try/with/match and inner expression
scopes retain their existing bounded omissions.
SymbolTable.lookup tracks visited scope IDs and raises ValueError on a cyclic
parent chain caused by external mutation. Callers must still not mutate indexed
identity/name/parent fields; this guard does not make arbitrary mutation safe.

## Exact user example
```python
def calculate(a, b):
    result = a + b
    return result

def main():
    answer = calculate(10, 5)
    print(answer)
```
For file F at calculator.py, tested metadata is:
- calculator.calculate: parameters a and b; start (line 1, byte column 0), end
  (line 3, byte column 17); deterministic function/scope IDs owned by file F.
- calculator.main: no parameters; start (5, 0), end (7, 17).
- calculate scope: a and b are parameters, result is a local assigned on line 2.
- main scope: answer is local. Calls calculate(10, 5) and print(answer) belong to main.

ASTAnalyzer discovers declarations/Name Store nodes and calls, then asks SymbolTable
to store each binding under its scope ID. `lookup(calculate.scope_id, 'result')`
finds the local result. `lookup(main.scope_id, 'calculate')` finds no local binding,
then checks module scope and returns the calculate declaration. It does not resolve
the call or prove a runtime target. A main parameter named calculate would shadow
that declaration. Duplicate local spellings in other functions/files stay separate.
No CFGs are created by this extraction or demonstration.
