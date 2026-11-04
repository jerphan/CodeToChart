"""Parse source snapshots into in-memory ASTs without executing source."""
import ast
from dataclasses import dataclass, field

from .models import Diagnostic, FileInput, SourceLocation


def ast_location(node: ast.AST, file_id: str) -> SourceLocation | None:
    """Copy AST byte offsets; return null for nodes without complete positions."""
    positions = [getattr(node, name, None) for name in
                 ('lineno', 'col_offset', 'end_lineno', 'end_col_offset')]
    if any(value is None for value in positions):
        return None
    return SourceLocation(file_id=file_id, start_line=positions[0], start_column=positions[1],
                          end_line=positions[2], end_column=positions[3])


def _syntax_location(error: SyntaxError, file: FileInput) -> SourceLocation | None:
    # SyntaxError columns count characters, starting at one. AST columns count
    # UTF-8 bytes, starting at zero: encode the prefix, not the whole line.
    lines = file.file_content.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    def position(line: int | None, offset: int | None) -> tuple[int, int] | None:
        if line is None or offset is None or not 1 <= line <= len(lines) or offset < 1:
            return None
        text = lines[line - 1]
        # Some EOF diagnostics point beyond the text; anchor them at end of line.
        column = min(offset - 1, len(text))
        return line, len(text[:column].encode('utf-8'))

    start = position(error.lineno, error.offset)
    if start is None:
        return None
    end = position(error.end_lineno, error.end_offset)
    if end is None or end < start:
        end = start  # A reliable point is better than an invented error range.
    return SourceLocation(file_id=file.file_id, start_line=start[0], start_column=start[1],
                          end_line=end[0], end_column=end[1])


@dataclass
class ParseResult:
    """Internal result; the AST is never included in public JSON contracts.

    syntax_valid means accepted by ast.parse, not full compiler/name validation.
    None means parsing could not establish validity (encoding/resource failure).
    """
    tree: ast.Module | None
    syntax_valid: bool | None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    file_id: str | None = None


class PythonParser:
    """Parse one validated FileInput, with no imports or evaluation of its source."""

    def parse(self, file_input: FileInput) -> ParseResult:
        """Return an AST or structured diagnostics; every call has fresh state."""
        file_input.__post_init__()
        if '\x00' in file_input.file_path:
            return ParseResult(file_id=file_input.file_id, tree=None, syntax_valid=None, diagnostics=[Diagnostic(
                severity='error', code='INVALID_SOURCE_PATH',
                message='Source filename contains a null character and cannot be passed to the AST parser.',
                file_id=file_input.file_id)])
        try:
            tree = ast.parse(file_input.file_content, filename=file_input.file_path, mode='exec')
        except SyntaxError as error:
            return ParseResult(file_id=file_input.file_id, tree=None, syntax_valid=False, diagnostics=[Diagnostic(
                severity='error', code='SYNTAX_ERROR', message=error.msg,
                file_id=file_input.file_id, source_location=_syntax_location(error, file_input))])
        except UnicodeEncodeError:
            return ParseResult(file_id=file_input.file_id, tree=None, syntax_valid=None, diagnostics=[Diagnostic(
                severity='error', code='INVALID_SOURCE_ENCODING',
                message='Source contains text that cannot be encoded as UTF-8.', file_id=file_input.file_id)])
        except RecursionError:
            return ParseResult(file_id=file_input.file_id, tree=None, syntax_valid=None, diagnostics=[Diagnostic(
                severity='error', code='PARSER_LIMIT',
                message='Source exceeds the Python AST parser recursion capacity.', file_id=file_input.file_id)])
        return ParseResult(file_id=file_input.file_id, tree=tree, syntax_valid=True)
