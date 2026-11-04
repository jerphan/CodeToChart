"""End-to-end runner connecting CodeManager source acquisition and ParsingAnalysis."""

import argparse
import io
import json
from pathlib import Path
import sys

# Ensure repository root is in sys.path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from FlowBridgeBackend.pipeline import FlowBridgePipeline
from FlowBridgeBackend.service import CodeManager


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run CodeManager and FlowBridge Parsing & Analysis end-to-end."
    )
    parser.add_argument("kind", choices=("file", "zip", "github"), help="Input type")
    parser.add_argument(
        "source", help="Path to Python file/ZIP archive, or public GitHub repo URL"
    )
    parser.add_argument("--project-name", default=None, help="Optional project name")
    parser.add_argument(
        "--revision-id", type=int, default=1, help="Revision ID for analysis (default: 1)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "examples" / "pipeline_results",
        help="Directory to save output JSON files",
    )
    args = parser.parse_args()

    manager = CodeManager()
    print(f"1. Ingesting {args.kind}: {args.source} via CodeManager...")

    if args.kind == "github":
        manager.loadGit(args.source, projectName=args.project_name)
    else:
        path = Path(args.source)
        if not path.is_file():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        with path.open("rb") as stream:
            if args.kind == "file":
                manager.loadFile(stream, fileName=path.name, projectName=args.project_name)
            else:
                manager.loadZip(stream, fileName=path.name, projectName=args.project_name)

    project = manager.getProject()
    print(f"   [CodeManager] Project '{project.projectName}' loaded with {len(project.files)} file(s).")

    print("\n2. Running Parsing & Analysis pipeline...")
    pipeline = FlowBridgePipeline(manager)
    results = pipeline.analyze_current(revision_id=args.revision_id)

    print(f"   [Parsing & Analysis] Status: {results['status']} | Revision: {results['revisionId']}")
    print(f"   [Flowchart] Graphs generated: {len(results['flowchart']['graphs'])}")
    print(f"   [Mapping] Source mappings generated: {len(results['mapping']['sourceMappings'])}")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    flowchart_path = output_dir / f"{project.projectName}_flowchart.json"
    mapping_path = output_dir / f"{project.projectName}_mapping.json"
    analysis_path = output_dir / f"{project.projectName}_analysis.json"

    flowchart_path.write_text(json.dumps(results["flowchart"], indent=2), encoding="utf-8")
    mapping_path.write_text(json.dumps(results["mapping"], indent=2), encoding="utf-8")
    analysis_path.write_text(json.dumps(results["analysis"], indent=2), encoding="utf-8")

    print("\n3. Saved consumer outputs:")
    print(f"   - Kevin's Flowchart: {flowchart_path.relative_to(root)}")
    print(f"   - Grace's Mapping:   {mapping_path.relative_to(root)}")
    print(f"   - Full Analysis:     {analysis_path.relative_to(root)}")


if __name__ == "__main__":
    main()
