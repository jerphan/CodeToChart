# Run and inspect FlowBridge in VS Code

Open the parsing_Analysis repository folder in VS Code. Open a PowerShell terminal
at that folder. Use Python 3.12 or newer; check with `python --version`.

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python examples/run_analysis.py examples/manual_inputs/conditions.json
```

Set PYTHONPATH again in each new terminal. If python is unavailable, use `py -3.12`
in place of python if that interpreter is installed. The runner is a CLI example;
there is no server or graphical flowchart window. Uploaded Python is never executed.

## Input files
Six ready-to-edit JSON files are in examples/manual_inputs/. Keep your own test
snapshots there too. The service accepts a project JSON, not a bare .py file.
Each fileContent field contains Python source; JSON represents newlines as \n.
Use the supplied examples as templates. Keep project/file IDs; increment revisionId
when editing source. Only source in fileContent is analyzed; filePath is metadata.

Verified cases:
- conditions.json: one choose function with if/return; success, 3 graphs.
- loops.json: a for loop, condition and continue; success, 3 graphs.
- syntax_error.json: def broken(:; partial, 2 graphs, SYNTAX_ERROR. File graph failed/empty.
- class_unsupported.json: Calculator class with add method; partial, 2 graphs,
  UNSUPPORTED_FEATURE + INCOMPLETE_SCOPE; no method/function CFG extracted.
- unsupported_statement.json: result += value in a function; partial, 3 graphs,
  UNSUPPORTED_FEATURE; the function graph exists with status unsupported and empty nodes/edges.
- basic_try.json: bounded try/except; partial, 3 graphs. CFG complete for conservative
  exception abstraction, with CONSERVATIVE_EXCEPTIONS and INCOMPLETE_SCOPE warnings.
- ../orders_input.json: realistic three-file imports/aliases; partial, 7 graphs,
  two resolved cross-file calls. Module imports remain unsupported as runtime CFGs.

Replace the final input argument to run any case. For example:
```powershell
python examples/run_analysis.py examples/manual_inputs/class_unsupported.json
python examples/run_analysis.py examples/orders_input.json
```

## Actual output location
The runner prints status, revision, counts and diagnostics in the terminal. It writes
three JSON files to examples/results/<input filename without .json>/:
- analysis.json: complete canonical analysis, including symbols and diagnostics.
- flowchart.json: Kevin's graph/navigation/metadata projection.
- mapping.json: Grace's source locations, function information and navigation/calls.

For conditions.json, open examples/results/conditions/flowchart.json or mapping.json
in VS Code. Search for graphType, status, label, sourceLocation and diagnostics.
The project/file/function views are data, not rendered diagrams. The graph dictionary
uses long opaque IDs; these are normal. Supported examples do not print computed
return values: this analyzes code instead of running choose, total or add.

Rerunning the same input filename replaces that example's three output files. To
keep comparisons, copy the input under another filename before running. This export
is demonstration file writing; the actual analysis service has no persistence.

## Unsupported syntax and how it appears
Classes and their methods, nested functions, decorators/generic functions, async/
await/yield, lambdas, comprehensions, with, match, assert, del, global/nonlocal,
walrus assignments, annotated assignments and augmented assignments are unsupported.
For ordinary assignment use result = result + value; result += value is not supported.
Signature annotations are retained as text; x: int = 1 is an unsupported statement.

Exception support excludes finally, try-else, nested try, except-as aliases,
except-star, explicit raise and dynamic handler-type expressions. Only the documented
basic try/except subset has CFG support. Loop-else has CFG support, but loop-else and
try lexical extraction remain incomplete and can cause partial analysis.

Absolute imports/aliases can resolve call metadata, but module execution is not
modeled. Relative/star/dynamic imports and dynamic call targets are not resolved.
An unresolved call alone need not make a valid CFG partial. Expressions such as
and/or remain atomic inside statement CFGs, not expanded into expression branches.

Syntax errors use SYNTAX_ERROR; valid Python outside the subset uses
UNSUPPORTED_FEATURE. The terminal and both output JSON files include diagnostics
with severity, message, fileId and optional sourceLocation/graphId. Unsupported
function graphs are empty; class methods are not extracted. A complete structural
file overview does not imply that its executable module code is supported.
Structurally invalid project JSON instead produces failed status with no graphs.

## Verification
All six manual inputs and orders_input.json were run with the bundled Python 3.12
runtime. Outcomes above were observed, not just predicted. For the regression suite:
```powershell
python -m unittest discover -s tests -q
```

## Actual Code Manager sample
examples/code_manager_input.json contains the three-file uppercase-ID snapshot,
including app/main.py and tests/main.py. Run:
```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python examples/run_analysis.py examples/code_manager_input.json --revision-id 1
```
Expected/verified: success; revision 1; 3 files; 3 functions; 7 graphs.
Outputs: examples/results/code_manager_input/{analysis,flowchart,mapping}.json.
Increase --revision-id when editing the snapshot. The adapter adds that supplied
value and does not maintain its own counter. Without this flag the runner retains
its existing canonical-input mode requiring projectId/fileId/revisionId in JSON.


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
