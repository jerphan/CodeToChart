"""Lexical binding records, not Python runtime name or call resolution."""
from dataclasses import dataclass, field
from typing import Literal

from .models import JsonModel, SymbolInfo


@dataclass(kw_only=True)
class ScopeInfo(JsonModel):
    """One module/function namespace; incomplete means lookup must not guess."""
    scope_id: str
    name: str
    kind: Literal['module', 'function']
    file_id: str
    parent_scope_id: str | None = None
    function_id: str | None = None
    is_complete: bool = True


@dataclass
class BindingLookup:
    """Nearest lexical bindings, preserving ambiguity and incomplete analysis."""
    scope_id: str | None
    bindings: list[SymbolInfo] = field(default_factory=list)
    is_complete: bool = True


class SymbolTable:
    """Index all binding occurrences by scope/name without overwriting duplicates."""

    def __init__(self) -> None:
        self._scopes: dict[str, ScopeInfo] = {}
        self._bindings: dict[str, dict[str, list[SymbolInfo]]] = {}
        self._symbols: list[SymbolInfo] = []

    @property
    def scopes(self) -> list[ScopeInfo]:
        """Return scopes in insertion order; records belong to this request."""
        return list(self._scopes.values())

    @property
    def symbols(self) -> list[SymbolInfo]:
        """Return binding occurrences in insertion order."""
        return list(self._symbols)

    def add_scope(self, scope: ScopeInfo) -> None:
        """Add a unique scope after its parent, preventing cycles and cross-file parents."""
        scope.__post_init__()
        if scope.scope_id in self._scopes:
            raise ValueError('Duplicate scope ID')
        if scope.kind == 'module':
            if scope.parent_scope_id is not None or scope.function_id is not None:
                raise ValueError('Module scopes cannot have a parent or function owner')
        else:
            parent = self._scopes.get(scope.parent_scope_id)
            if parent is None or parent.file_id != scope.file_id or scope.function_id is None:
                raise ValueError('Function scope requires an existing same-file parent and function owner')
        self._scopes[scope.scope_id] = scope
        self._bindings[scope.scope_id] = {}

    def scope(self, scope_id: str) -> ScopeInfo:
        """Get a known scope; unknown IDs are programmer errors."""
        return self._scopes[scope_id]

    def mark_incomplete(self, scope_id: str) -> None:
        """Prevent optimistic lookup through an incompletely inspected namespace."""
        self._scopes[scope_id].is_complete = False

    def bind(self, symbol: SymbolInfo) -> None:
        """Record a declaration/parameter/assignment, retaining repeated names."""
        symbol.__post_init__()
        scope = self._scopes[symbol.scope_id]
        if symbol.file_id != scope.file_id:
            raise ValueError('Symbol and scope file IDs disagree')
        self._bindings[symbol.scope_id].setdefault(symbol.name, []).append(symbol)
        self._symbols.append(symbol)

    def bindings(self, scope_id: str, name: str) -> list[SymbolInfo]:
        """Return only this scope's occurrences, without consulting its parent."""
        return list(self._bindings[scope_id].get(name, []))

    def lookup(self, scope_id: str, name: str) -> BindingLookup:
        """Find the nearest binding group, without interpreting execution order.

        A function assignment shadows a module name throughout the function,
        even before that assignment executes. Missing names in an incomplete
        scope stop lookup: silently falling back could invent a false target.
        """
        current = self._scopes[scope_id]
        visited: set[str] = set()
        while True:
            # Scope records are mutable. Detect a broken parent chain instead of
            # hanging forever if a caller changes one after insertion.
            if current.scope_id in visited:
                raise ValueError('Cycle in scope parent chain')
            visited.add(current.scope_id)
            bindings = self.bindings(current.scope_id, name)
            if bindings or not current.is_complete:
                return BindingLookup(current.scope_id, bindings, current.is_complete)
            if current.parent_scope_id is None:
                return BindingLookup(None)
            current = self._scopes[current.parent_scope_id]

    def to_dict(self) -> dict[str, object]:
        """Expose a JSON-compatible debug view, separate from downstream schemas."""
        return {'scopes': [scope.to_dict() for scope in self.scopes],
                'symbols': [symbol.to_dict() for symbol in self.symbols]}
