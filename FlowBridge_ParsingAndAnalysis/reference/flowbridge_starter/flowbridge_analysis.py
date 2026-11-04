"""FlowBridge Parsing & Analysis: deliberately small, executable starter.

Supported function CFG statements: assignments, expression statements,
if/elif/else, return, pass. Other statements produce diagnostics and
are NOT presented as accurate control flow.

No uploaded code is executed. AST parsing inspects its syntax only.
"""
from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path


def location(node: ast.AST, file_id: str) -> dict:
    """AST column offsets are UTF-8 byte offsets, zero-based; lines are 1-based."""
    return {
        "fileId": file_id,
        "startLine": getattr(node, "lineno", None),
        "startColumn": getattr(node, "col_offset", None),
        "endLine": getattr(node, "end_lineno", None),
        "endColumn": getattr(node, "end_col_offset", None),
    }


def label(node: ast.AST) -> str:
    """Short source-like labels without executing uploaded Python."""
    return ast.unparse(node)


class CFGBuilder:
    """Build a graph for one function, with exact source mappings."""

    def __init__(self, graph_id: str, function_id: str, file_id: str):
        self.graph = {"graphId": graph_id, "viewType": "function", "functionId": function_id,
                      "nodes": [], "edges": []}
        self.file_id = file_id
        self.mappings = []
        self.diagnostics = []
        self._counter = 0
        self._edge_counter = 0

    def node(self, typ: str, text: str, ast_node: ast.AST | None = None) -> str:
        self._counter += 1
        node_id = f"{self.graph['graphId']}:N{self._counter:03d}"
        loc = location(ast_node, self.file_id) if ast_node is not None else None
        self.graph["nodes"].append({"nodeId": node_id, "nodeType": typ,
                                    "label": text, "sourceLocation": loc})
        if loc is not None:
            self.mappings.append({"graphId": self.graph["graphId"], "nodeId": node_id,
                                  "location": loc})
        return node_id

    def connect(self, source: str, target: str, kind: str = "normal") -> None:
        self._edge_counter += 1
        self.graph["edges"].append({"edgeId": f"{self.graph['graphId']}:E{self._edge_counter:03d}",
                                    "sourceId": source, "targetId": target,
                                    "edgeType": kind})

    def warn(self, statement: ast.stmt) -> None:
        self.diagnostics.append({"severity": "error", "code": "UNSUPPORTED_STATEMENT",
                                 "message": f"CFG does not support {type(statement).__name__}; no executable path is asserted for it",
                                 "location": location(statement, self.file_id)})

    def block(self, statements: list[ast.stmt], incoming: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Incoming is a list of (predecessor node ID, outgoing edge label).

        Empty list means every path has returned, or analysis is blocked.
        """
        for stmt in statements:
            if not incoming:
                # Unreachable after return; do not invent a reachable path.
                break
            if isinstance(stmt, ast.If):
                decision = self.node("decision", label(stmt.test), stmt.test)
                for previous, edge_type in incoming:
                    self.connect(previous, decision, edge_type)
                true_exits = self.block(stmt.body, [(decision, "true")])
                false_exits = (self.block(stmt.orelse, [(decision, "false")])
                               if stmt.orelse else [(decision, "false")])
                incoming = true_exits + false_exits
            elif isinstance(stmt, ast.Return):
                current = self.node("return", label(stmt), stmt)
                for previous, edge_type in incoming:
                    self.connect(previous, current, edge_type)
                self.connect(current, self.end, "return")
                incoming = []
            elif isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Pass)):
                current = self.node("process", label(stmt), stmt)
                for previous, edge_type in incoming:
                    self.connect(previous, current, edge_type)
                incoming = [(current, "normal")]
            else:
                # Fail closed: do not silently draw an inaccurate graph.
                self.warn(stmt)
                incoming = []
        return incoming

    def build(self, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[dict, list, list]:
        start = self.node("start", "Start")
        self.end = self.node("end", "End")
        exits = self.block(fn.body, [(start, "normal")])
        for previous, edge_type in exits:
            self.connect(previous, self.end, edge_type)
        return self.graph, self.mappings, self.diagnostics


def analyze_project(project: dict) -> dict:
    """Rebuild the entire analysis from one input snapshot (no SQL needed)."""
    if not isinstance(project, dict) or not isinstance(project.get("files"), list):
        raise ValueError("Expected JSON object containing a files array")
    project_id = project["projectId"]
    file_ids = [f["fileId"] for f in project["files"]]
    if len(set(file_ids)) != len(file_ids):
        raise ValueError("Duplicate fileId values")

    result = {"projectId": project_id, "projectName": project["projectName"],
              "revisionId": project.get("revisionId", 1), "rootGraphId": f"{project_id}:PROJECT",
              "status": "ok", "graphs": {}, "files": [], "functions": [],
              "callReferences": [], "graphReferences": [], "sourceMappings": [], "diagnostics": []}
    root = {"graphId": result["rootGraphId"], "viewType": "project", "nodes": [], "edges": []}
    result["graphs"][root["graphId"]] = root
    all_functions = []

    for file_index, file in enumerate(project["files"], 1):
        fid, path = file["fileId"], file["filePath"]
        file_graph_id = f"{project_id}:{fid}:FILE"
        project_node_id = f"{root['graphId']}:N{file_index:03d}"
        root["nodes"].append({"nodeId": project_node_id, "nodeType": "file",
                              "label": path, "sourceLocation": None})
        result["graphReferences"].append({"sourceGraphId": root["graphId"],
                                          "sourceNodeId": project_node_id,
                                          "targetGraphId": file_graph_id})
        fg = {"graphId": file_graph_id, "viewType": "file", "fileId": fid,
              "nodes": [], "edges": []}
        result["graphs"][file_graph_id] = fg
        result["files"].append({"fileId": fid, "fileName": file["fileName"],
                                "filePath": path, "graphId": file_graph_id})
        try:
            # This parses code; it does not import or run it.
            tree = ast.parse(file["fileContent"], filename=path)
        except SyntaxError as err:
            result["diagnostics"].append({"severity": "error", "code": "SYNTAX_ERROR",
                "message": err.msg, "location": {"fileId": fid, "startLine": err.lineno,
                "startColumn": (err.offset - 1) if err.offset else None,
                "endLine": err.end_lineno, "endColumn": (err.end_offset - 1) if err.end_offset else None}})
            continue

        # This starter only supports top-level function definitions and does
        # not represent module-level executable statements or nested defs.
        for item in tree.body:
            if not isinstance(item, ast.FunctionDef):
                result["diagnostics"].append({"severity": "warning", "code": "UNSUPPORTED_TOP_LEVEL",
                    "message": f"Top-level {type(item).__name__} is not modeled",
                    "location": location(item, fid)})
                continue
            index = len(fg["nodes"]) + 1
            function_id = f"{fid}:FN{index:03d}"
            graph_id = f"{project_id}:{function_id}:FUNC"
            node_id = f"{file_graph_id}:N{index:03d}"
            fg["nodes"].append({"nodeId": node_id, "nodeType": "function",
                                "label": item.name, "sourceLocation": location(item, fid)})
            result["graphReferences"].append({"sourceGraphId": file_graph_id,
                                              "sourceNodeId": node_id, "targetGraphId": graph_id})
            info = {"functionId": function_id, "functionName": item.name,
                    "qualifiedName": f"{Path(path).with_suffix('').as_posix().replace('/', '.')}.{item.name}",
                    "fileId": fid, "parameters": [a.arg for a in item.args.posonlyargs + item.args.args + item.args.kwonlyargs],
                    "startLine": item.lineno, "endLine": item.end_lineno,
                    "graphId": graph_id}
            result["functions"].append(info)
            result["sourceMappings"].append({"graphId": file_graph_id, "nodeId": node_id,
                                              "location": location(item, fid)})
            builder = CFGBuilder(graph_id, function_id, fid)
            graph, mappings, diagnostics = builder.build(item)
            result["graphs"][graph_id] = graph
            result["sourceMappings"].extend(mappings)
            result["diagnostics"].extend(diagnostics)
            all_functions.append((item, info))

    # Basic same-file, uniquely named function-call resolution. More complex
    # Python scoping, imports, methods, dynamic dispatch are future work.
    functions_by_file = defaultdict(lambda: defaultdict(list))
    for info in result["functions"]:
        functions_by_file[info["fileId"]][info["functionName"]].append(info)
    for ast_fn, caller in all_functions:
        for node in ast.walk(ast_fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                matches = functions_by_file[caller["fileId"]].get(node.func.id, [])
                if len(matches) == 1:
                    result["callReferences"].append({"callerFunctionId": caller["functionId"],
                        "calleeFunctionId": matches[0]["functionId"],
                        "location": location(node, caller["fileId"])})

    if any(d["severity"] == "error" for d in result["diagnostics"]):
        result["status"] = "partial"
    elif result["diagnostics"]:
        result["status"] = "warnings"
    return result


def split_outputs(result: dict) -> dict:
    """Two views of the SAME analysis; IDs must not be regenerated here."""
    return {
        "flowchartOutput": {"projectId": result["projectId"], "revisionId": result["revisionId"],
                            "rootGraphId": result["rootGraphId"], "graphs": result["graphs"],
                            "graphReferences": result["graphReferences"], "diagnostics": result["diagnostics"]},
        "mappingOutput": {"projectId": result["projectId"], "revisionId": result["revisionId"],
                          "files": result["files"], "functions": result["functions"],
                          "sourceMappings": result["sourceMappings"],
                          "graphReferences": result["graphReferences"],
                          "callReferences": result["callReferences"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSON from Code Manager")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()
    project = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze_project(project)
    outputs = split_outputs(result)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, payload in [("project_analysis.json", result),
                              ("flowchart_output.json", outputs["flowchartOutput"]),
                              ("mapping_output.json", outputs["mappingOutput"])]:
        (args.output_dir / filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Analysis status: {result['status']}")
    print(f"Graphs: {len(result['graphs'])}, functions: {len(result['functions'])}, "
          f"mappings: {len(result['sourceMappings'])}, diagnostics: {len(result['diagnostics'])}")


if __name__ == "__main__":
    main()
