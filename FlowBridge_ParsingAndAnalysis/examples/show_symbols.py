"""Demonstrate calculator metadata without executing its source or building CFGs."""
import json
from pathlib import Path

from flowbridge_analysis import ASTAnalyzer, PythonParser, RevisionIds, validate_project


def main() -> None:
    """Print actual symbol/call records extracted from the calculator snapshot."""
    source = Path(__file__).with_name('calculator_input.json')
    validation = validate_project(source.read_text(encoding='utf-8-sig'))
    if not validation.is_valid:
        raise ValueError([item.to_dict() for item in validation.diagnostics])
    project = validation.project
    ids = RevisionIds(project.project_id, project.revision_id)
    for file in project.files:
        parsed = PythonParser().parse(file)
        if parsed.tree is None:
            print(json.dumps([item.to_dict() for item in parsed.diagnostics], indent=2))
            continue
        result = ASTAnalyzer().analyze(parsed.tree, file, ids)
        for scope in result.symbol_table.scopes:
            print(f'{scope.kind} scope: {scope.name} (complete={scope.is_complete})')
            for symbol in result.symbol_table.symbols:
                if symbol.scope_id == scope.scope_id:
                    position = symbol.location
                    print(f'  {symbol.name}: {symbol.kind}, line {position.start_line}, byte column {position.start_column}')
        print('Call sites (unresolved):')
        for call in result.call_sites:
            scope = result.symbol_table.scope(call.scope_id)
            print(f'  {scope.name}: {call.expression} at line {call.location.start_line}')
        print(f'Diagnostics: {len(result.diagnostics)}; no graphs constructed.')


if __name__ == '__main__':
    main()
