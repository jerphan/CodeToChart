# Module responsibilities

- **Justin — Code Manager:** intake, uploads/ZIP handling, source snapshots and
  projectId, projectName, revisionId, fileId, fileName, filePath, fileContent.
  Analysis consumes these values and does not replace identifiers.
- **Parsing & Analysis owner:** input validation, AST parsing, feature validation,
  metadata, symbols, bounded call resolution, CFGs, overview graphs, generated IDs,
  source mappings, graph references, diagnostics, and canonical/consolidated outputs.
- **Kevin — Visualization:** render the supplied graphs. Analysis supplies nodes,
  edges, and navigation information; Kevin owns layout, coordinates and styling.
- **Grace — Source Mapping / Navigation:** consume source locations, function
  metadata, mappings and references to implement editor/diagram interactions and
  call navigation. Analysis owns the accuracy and consistency of that data.
- **Jerry — Website Management:** website and supporting responsibilities.

Changes to another teammate's module require approval. Proposed output additions,
coordinate conversion, and status behavior need integration agreement; do not
change Justin's input contract as a shortcut.
