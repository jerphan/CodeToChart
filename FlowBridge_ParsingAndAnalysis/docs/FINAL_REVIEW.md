# Final implementation review — 2026-11-03

## Outcome
The bounded Parsing & Analysis pipeline is ready for controlled teammate integration.
It is not a complete Python analyzer or a production-isolated untrusted-source
service. Public input/output fields were preserved in this review. D023 remains
the approved FlowchartOutput extension. See INTEGRATION_GUIDE.md for actual usage.

## Defects found and fixed
1. Blocking hierarchy API mismatch: the current builder exported ProjectGraphResult
   and accepted only dictionaries, while package/service expected ProjectGraphs and
   a list. Baseline: 64 discovered test entries, 14 import errors. Restored compatible
   aliases/list-or-dictionary inputs and complete graph assembly without overwrites.
   During work another editor replaced the file with a placeholder: 65 entries,
   15 import errors. User paused that editor; builder restored and reverified.
2. Root-only filePath values accepted by the input contract crashed PurePosixPath
   suffix removal. AST metadata now uses fileName as display fallback; resolver
   skips paths without a module filename. No path is opened or imported.
3. Null-containing filename metadata raised ValueError inside ast.parse. Parser
   now returns INVALID_SOURCE_PATH and a failed file view through the service.
4. Duplicate function parameters were accepted by ast.parse and then emitted as
   successful executable CFGs. FeatureValidator rejects duplicate names before CFG
   construction, including positional-only/vararg/keyword variants. This is a
   bounded compiler-context check, not a claim of complete compiler validation.
5. Structurally invalid JSON text lost valid project/revision fields while the same
   decoded dictionary retained them. Failure identity now uses the same strict JSON
   decoder, preserving valid fields without accepting duplicate JSON keys.
6. Builder consistency: reject duplicate/missing/unowned graphs and owner mismatch;
   retain complete structural views for feature-unsupported files; failed files
   remain empty; noncomplete project graphs cannot emit dangling source references.

## Review of required areas
1. Input validation: required JSON fields/types, nonnegative nonboolean revisions,
   duplicate file IDs/object keys, nonfinite values and cycles tested. Unknown JSON
   extensions ignored. Duplicate paths warn. Resource quotas remain undecided.
2. IDs: deterministic reversible tuple encoding includes project/revision/type/owner.
   No random/global counters. Identical structural keys intentionally reuse IDs;
   callers must never reuse a revision for different text if response ordering matters.
3. Parsing: ast.parse only; syntax/encoding/recursion/path diagnostics. No uploaded
   execution/import/evaluation. AST acceptance is not full compiler acceptance.
4. Feature validation: explicit allowlist and scope/loop/try context; rejects
   unsupported constructs, including unreachable unsupported syntax. Duplicate
   parameters now rejected. Other compiler-context gaps remain (e.g. __debug__ writes).
5. Function extraction: direct module functions, signatures, locations, declarations
   and calls. Nested/class/async bodies omitted explicitly. Defaults/decorators use
   defining scope; annotations retained as source, not evaluated.
6. Symbols: nearest lexical binding groups, shadowing and incomplete-scope guards.
   Duplicate occurrences retained. No dataflow, definite assignment or full closures.
7. Calls: same-file and explicit absolute import/alias targets; statuses and reasons
   preserved. No project-wide name guessing. No re-exports/relative imports/dynamic
   dispatch or monkey-patching inference; syntactic candidate resolution only.
8. CFG: exact-connectivity tests for branches, terminal returns, loop back/exit,
   nearest break/continue, loop-else and bounded try/except. Expressions remain atomic;
   exception edges are conservative alternatives, not runtime type proofs.
9. Hierarchy: one project view, one file view per supplied file, existing function
   CFGs, navigation-only references. Empty/failed/unsupported states tested.
10. Mapping: AST UTF-8 byte offsets, exclusive ends, one mapping per source-backed
    generated node, integrity and Unicode/CRLF/line-edit tests. Arbitrary externally
    constructed spans are not checked against source text; editor conversion deferred.
11. Canonical consistency: node/edge/metadata/reference/mapping/call ownership checks
    and serialization revalidation. Model constructors are not full semantic proofs;
    service owns fresh assembly and mapping completeness.
12. Outputs: explicit canonical projections; approved camelCase fields, shared IDs,
    no ASTs. Independent captured JSON values; downstream consumer execution not tested.
13. Reanalysis: every full snapshot reparsed/rebuilt; edits/additions/removals/line
    shifts/failed edits/recovery and old/reused revisions tested. No latest-state cache.
14. Diagnostics: invalid files isolated, valid siblings retained, partial status and
    non-executable failed/unsupported views. Unexpected programmer errors are not
    concealed by a blanket exception handler. No hard memory/time isolation yet.
15. Maintainability: standard library, typed records, explicit stages and comments.
    Hierarchy groups functions by file. Compatibility aliases avoid duplicate classes.
    Some helper status annotations are broad strings; source extraction and repeated
    nested validation can be expensive on large inputs. Profiling remains future work.

## Verification evidence
- Baseline: 64 entries, 14 import errors (no assertion failures).
- After first hierarchy repair: 194 tests passed.
- Concurrent placeholder replacement: 65 entries, 15 import errors.
- After restoration and edit regressions: 205 passed.
- Final suite: **207 passed**, zero failures/errors, Python 3.12.14 (1.306 seconds).
- Ran examples/generate_outputs.py and read back all six JSON projections.
  Calculator: success, 4 graphs/3 navigation links.
  Imported calculator: partial, 5 graphs/4 links.
  Order reporting: partial, 7 graphs/6 links, two resolved cross-file calls and builtin print.
  Partial import examples explicitly retain unsupported module-execution diagnostics.
- Tests are behavioral counts, not a measured line/branch coverage percentage.
  Historical milestone counts in documentation are not current totals.

## Remaining integration risks and next step
No database/UI/debounce/incremental parsing. Unsupported: module execution CFGs,
classes/nested functions/async/comprehensions, full compiler and scope semantics,
finally/try-else/nested try/aliases/explicit raise/except-star, dynamic call resolution.
Try/loop-else lexical extraction remains incomplete even where CFGs are supported.
Cross-file imports can resolve while the module remains feature-unsupported.
Long IDs and repeated serialization need profiling before large uploads.
Resource quotas/process isolation, full source-bound verification and packaging
installation tests remain unverified. Exact UML diagrams were unavailable.
Next: Justin/Kevin/Grace exercise the supplied fixtures together, agree transport
and status handling, then implement bounded resource/compiler hardening before
public untrusted uploads. Revision matching must gate both display and highlights.

Final post-documentation verification repeated the full suite: 207 passed in
1.463 seconds; all six consumer JSON fixtures regenerated and round-trip checked.
