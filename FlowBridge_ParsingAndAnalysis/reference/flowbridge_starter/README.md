# FlowBridge Parsing & Analysis Starter

## Requirements
Python 3.10+ (no third-party dependencies).

## Run
From this directory:

```bash
python flowbridge_analysis.py sample_input.json --output-dir output
python -m unittest discover -s . -p 'test_*.py' -v
```

## Files
- `sample_input.json`: mock data from Justin's Code Manager.
- `flowbridge_analysis.py`: annotated Python implementation.
- `output/project_analysis.json`: complete analysis.
- `output/flowchart_output.json`: graph contract for Kevin.
- `output/mapping_output.json`: source mapping contract for Grace.
- `test_analysis.py`: five example tests.

## Supported scope (important)
- Top-level `def` functions (no nested functions, async, or classes).
- Assignments, expression statements, `pass`, `return`, and `if`/`elif`/`else` inside functions.
- Basic unique same-file direct-name function-call resolution.
- Syntax diagnostics and unsupported-construct diagnostics.
- Project, file, and function view graphs.
- Source locations (1-based lines, zero-based UTF-8 byte column offsets).

**Not yet supported:** `for`, `while`, `break`, `continue`, `try/except`, comprehensions as control-flow paths, nested functions, class methods, imports/cross-file calls, short-circuit condition subgraphs, or module-level executable code. In particular, an unsupported control-flow statement creates an error diagnostic; the partial graph must not be displayed as a complete accurate CFG. The parser never executes user source code.

`revisionId` allows the client to discard responses that belong to older editor revisions. IDs are unique within the analysis response but are not stable across edits.
