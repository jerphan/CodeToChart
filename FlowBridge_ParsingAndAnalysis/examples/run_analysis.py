"""Local demonstration runner: analyze JSON and export reviewable consumer files.

Run from the repository root with src on PYTHONPATH. This script writes example
artifacts only; the analysis service itself remains entirely in memory.
"""
import argparse
import json
from pathlib import Path
from flowbridge_analysis import CodeManagerInputAdapter, ParsingAnalysisService, FlowchartOutput, MappingOutput


def main() -> None:
    """Analyze one supplied JSON snapshot and print its result location/diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Path to a project input JSON file')
    parser.add_argument('--revision-id', type=int, help='Normalize Code Manager input using this explicit revision')
    args = parser.parse_args()
    source = args.input.read_text(encoding='utf-8-sig')
    if args.revision_id is not None:
        try:
            source = CodeManagerInputAdapter().normalize(source, revision_id=args.revision_id)
        except ValueError as error:
            parser.error(str(error))
    analysis = ParsingAnalysisService().analyze_project(source)
    directory = Path(__file__).resolve().parent / 'results' / args.input.stem
    directory.mkdir(parents=True, exist_ok=True)
    outputs = {
        'analysis.json': analysis.to_dict(),
        'flowchart.json': FlowchartOutput(analysis).to_dict(),
        'mapping.json': MappingOutput(analysis).to_dict(),
    }
    for filename, data in outputs.items():
        (directory / filename).write_text(json.dumps(data, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    print(f'Status: {analysis.status} | Revision: {analysis.revision_id}')
    print(f'Files: {len(analysis.files)} | Functions: {len(analysis.functions)} | Graphs: {len(analysis.graphs)}')
    for diagnostic in analysis.diagnostics:
        location = diagnostic.source_location
        position = f' line {location.start_line}' if location is not None else ''
        print(f'{diagnostic.severity.upper()} {diagnostic.code} [{diagnostic.file_id}{position}]: {diagnostic.message}')
    print(f'Output folder: {directory}')


if __name__ == '__main__':
    main()
