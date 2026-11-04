"""ProjectAnalysis contract, extracted without changing its fields or validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from .JsonModel import AnalysisStatus, JsonModel, _unique
from .CallReference import CallReference
from .Diagnostic import Diagnostic
from .FileMetadata import FileMetadata
from .FunctionInfo import FunctionInfo
from .GraphModel import GraphModel
from .FlowNode import FlowNode
from .GraphReference import GraphReference
from .SourceMapping import SourceMapping
from .SymbolInfo import SymbolInfo


@dataclass(kw_only=True)
class ProjectAnalysis(JsonModel):
    """Canonical in-memory result; construction does not perform analysis."""
    project_id: str | None
    project_name: str | None
    revision_id: int | None
    status: AnalysisStatus
    files: list[FileMetadata] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    graphs: dict[str, GraphModel] = field(default_factory=dict)
    symbols: list[SymbolInfo] = field(default_factory=list)
    call_references: list[CallReference] = field(default_factory=list)
    source_mappings: list[SourceMapping] = field(default_factory=list)
    graph_references: list[GraphReference] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.revision_id is not None and self.revision_id < 0:
            raise ValueError('revision_id must be nonnegative')
        if self.status != 'failed' and None in (self.project_id, self.project_name, self.revision_id):
            raise ValueError('Nonfailed results require project metadata')
        _unique([item.file_id for item in self.files], 'file IDs')
        _unique([item.function_id for item in self.functions], 'function IDs')
        _unique([item.call_id for item in self.call_references], 'call IDs')
        for graph_id, graph in self.graphs.items():
            if graph_id != graph.graph_id:
                raise ValueError('Graph dictionary key does not match graph_id')
        for item in self.files + self.functions:
            if item.graph_id not in self.graphs:
                raise ValueError('Metadata refers to a nonexistent graph')
        files_by_id = {item.file_id: item for item in self.files}
        functions_by_id = {item.function_id: item for item in self.functions}
        for item in self.files:
            graph = self.graphs[item.graph_id]
            if graph.graph_type != 'file' or graph.file_id != item.file_id:
                raise ValueError('File metadata and graph ownership disagree')
        for item in self.functions:
            graph = self.graphs[item.graph_id]
            if (item.file_id not in files_by_id or graph.graph_type != 'function'
                    or graph.function_id != item.function_id or graph.file_id != item.file_id):
                raise ValueError('Function metadata and graph ownership disagree')
        for graph in self.graphs.values():
            if graph.file_id is not None and graph.file_id not in files_by_id:
                raise ValueError('Graph owner file does not exist')
            if graph.function_id is not None and graph.function_id not in functions_by_id:
                raise ValueError('Graph owner function does not exist')
            for node in graph.nodes:
                if node.source_location is not None and node.source_location.file_id not in files_by_id:
                    raise ValueError('Node source file does not exist')
        # A node ID is local to a graph. Tuple keys avoid delimiter ambiguity and
        # let every reference use the same checked lookup rather than rescanning.
        nodes_by_key: dict[tuple[str, str], FlowNode] = {}
        for graph in self.graphs.values():
            for node in graph.nodes:
                nodes_by_key[(graph.graph_id, node.node_id)] = node
        for reference in self.graph_references:
            self._require_node(nodes_by_key, reference.source_graph_id, reference.source_node_id)
            if reference.target_graph_id not in self.graphs:
                raise ValueError('Navigation target graph does not exist')
        mapped_nodes: set[tuple[str, str]] = set()
        for mapping in self.source_mappings:
            node = self._require_node(nodes_by_key, mapping.graph_id, mapping.node_id)
            mapping_key = (mapping.graph_id, mapping.node_id)
            if mapping_key in mapped_nodes:
                raise ValueError('Duplicate source mapping for graph/node')
            mapped_nodes.add(mapping_key)
            if mapping.location != node.source_location:
                raise ValueError('Mapping differs from its node source location')
        function_ids = {function.function_id for function in self.functions}
        for call in self.call_references:
            if call.file_id not in files_by_id or call.location.file_id != call.file_id:
                raise ValueError('Call source file does not match an existing file')
            if call.caller_function_id is not None:
                caller = functions_by_id.get(call.caller_function_id)
                if caller is None or caller.file_id != call.file_id:
                    raise ValueError('Call caller does not belong to its source file')
            if call.resolution == 'resolved' and (
                call.target_function_id not in function_ids or call.target_graph_id not in self.graphs
            ):
                raise ValueError('Resolved call target does not exist')
            if call.resolution == 'resolved' and functions_by_id[call.target_function_id].graph_id != call.target_graph_id:
                raise ValueError('Resolved call graph does not belong to target function')

    @staticmethod
    def _require_node(
        nodes_by_key: dict[tuple[str, str], FlowNode], graph_id: str, node_id: str,
    ) -> FlowNode:
        """Return the exact graph-local node or reject a dangling reference."""
        node = nodes_by_key.get((graph_id, node_id))
        if node is None:
            raise ValueError('Referenced node does not exist')
        return node
