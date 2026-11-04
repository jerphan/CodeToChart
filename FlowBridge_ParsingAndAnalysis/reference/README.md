# Reference material

`flowbridge_starter/` contains the supplied ZIP's source, tests, sample input and
generated JSON examples, preserved without modification. Python bytecode caches
were omitted. These files are inspiration, not production implementation or
instructions for contributors. Do not import them into the active package.

## Static inspection findings
Useful ideas: AST-based locations, pending branch exits, returns terminating a
path, independent overview graphs, and two projections sharing canonical IDs.

Gaps against the project requirements:
- One large implementation file instead of focused modules and typed models.
- Missing fields can raise KeyError; revisionId defaults instead of being required;
  input types are not fully checked.
- No symbol table; name-only call matching ignores local/parameter shadowing and
  walks nested scopes. Unresolved, ambiguous, builtin and external calls are omitted.
- Function metadata omits columns and variadic parameters.
- Loops, exception handling and module execution are not modeled. Unsupported
  expressions such as yield can occur inside accepted expression statements.
- Partial graphs have no graph-level accuracy status; diagnostics use `location`
  rather than the proposed `sourceLocation` field and omit explicit graph IDs.
- Status/node/edge enums differ from the proposed contract; do not adopt them silently.
- Syntax error columns are not converted to UTF-8 byte offsets.
- Five example tests provide narrow coverage, not evidence for the required matrix.

Inspection was read-only; starter code and tests were not executed. Its output
JSON is illustrative and is not an approved golden fixture for the new package.
