"""Generate reviewable consumer examples from source JSON, without running uploads."""
import json
from pathlib import Path
from flowbridge_analysis import ParsingAnalysisService, FlowchartOutput, MappingOutput


def main():
    directory = Path(__file__).resolve().parent
    multi = {'projectId': 'P002', 'projectName': 'Imported calculator', 'revisionId': 1,
             'files': [
                 {'fileId': 'calculator', 'fileName': 'calculator.py', 'filePath': 'calculator.py',
                  'fileContent': 'def add(a, b):\n    return a + b\n'},
                 {'fileId': 'main', 'fileName': 'main.py', 'filePath': 'main.py',
                  'fileContent': 'from calculator import add\n\ndef main():\n    return add(10, 5)\n'}]}
    (directory / 'multifile_input.json').write_text(json.dumps(multi, indent=2) + '\n', encoding='utf-8')
    for name in ('calculator', 'multifile', 'orders'):
        source = (directory / f'{name}_input.json').read_text(encoding='utf-8')
        result = ParsingAnalysisService().analyze_project(source)
        for consumer, output in [('kevin', FlowchartOutput(result)), ('grace', MappingOutput(result))]:
            path = directory / f'{name}_{consumer}_output.json'
            path.write_text(output.to_json() + '\n', encoding='utf-8')
            assert json.loads(path.read_text(encoding='utf-8')) == output.to_dict()
        print(f'{name}: {result.status}, {len(result.graphs)} graphs, {len(result.graph_references)} navigation links')


if __name__ == '__main__':
    main()

