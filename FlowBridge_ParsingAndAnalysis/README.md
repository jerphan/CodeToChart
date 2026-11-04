# FlowBridge Parsing & Analysis

In-memory Python source analysis for The Adaptables, CS 4366 Senior Capstone.
The bounded pipeline validates JSON, parses ASTs, extracts symbols/functions,
resolves supported calls, builds project/file/function graphs and emits shared
visualization/mapping JSON. Uploaded code is never executed or imported.

**Current verification: 219 tests pass on Python 3.12.14.** Full snapshots are
reanalyzed independently after edits. Invalid edited files produce diagnostics
and empty failed file views; old graphs are never reused as current results.

Start with [the integration guide](docs/INTEGRATION_GUIDE.md),
[contracts](docs/INPUT_OUTPUT_CONTRACT.md), [progress](docs/PROGRESS.md) and
[final review](docs/FINAL_REVIEW.md). Kevin consumes FlowchartOutput; Grace consumes
MappingOutput; both derive from one ProjectAnalysis with identical revision IDs.

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m unittest discover -s tests -q
python examples/generate_outputs.py
```

Examples include calculator, imported calculator and a three-file order-reporting
project. Each has input JSON and generated Kevin/Grace output JSON in examples/.
Absolute imports are supported static metadata. Module-execution CFGs remain
unsupported; ordinary absolute imports alone no longer cause partial analysis.

See [CFG design](docs/CFG_DESIGN.md), [feature support](docs/PARSING_FEATURES.md),
[call resolution](docs/CALL_RESOLUTION.md) and [mapping](docs/SOURCE_MAPPING.md).
Ready for controlled team integration; full Python semantics, resource/process
isolation and live consumer verification remain incomplete. No UI, database,
ZIP handling or incremental parsing belongs to this module.

Read [AGENTS.md](AGENTS.md) before changes. reference/ preserves historical starter
material; it is not the active implementation or a current contract.
