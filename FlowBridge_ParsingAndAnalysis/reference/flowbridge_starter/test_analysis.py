"""Run with: python -m unittest discover -s . -p 'test_*.py' -v"""
import json
import unittest
from pathlib import Path
from flowbridge_analysis import analyze_project, split_outputs

BASE = Path(__file__).resolve().parent


class FlowBridgeTests(unittest.TestCase):
    def setUp(self):
        self.project = json.loads((BASE / "sample_input.json").read_text(encoding="utf-8"))

    def test_sample_contract(self):
        result = analyze_project(self.project)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["graphs"]), 4)
        self.assertEqual(len(result["functions"]), 2)
        self.assertEqual(len(result["sourceMappings"]), 8)
        self.assertEqual(len(result["diagnostics"]), 0)
        self.assertEqual(len(result["callReferences"]), 1)
        output = split_outputs(result)
        self.assertIn("graphs", output["flowchartOutput"])
        self.assertIn("sourceMappings", output["mappingOutput"])

    def test_if_edges_and_locations(self):
        result = analyze_project(self.project)
        graph = result["graphs"]["P001:F001:FN001:FUNC"]
        edges = [e["edgeType"] for e in graph["edges"]]
        self.assertIn("true", edges)
        self.assertIn("false", edges)
        decision = next(n for n in graph["nodes"] if n["nodeType"] == "decision")
        self.assertEqual(decision["sourceLocation"]["startLine"], 2)

    def test_invalid_code_reports_error(self):
        self.project["files"][0]["fileContent"] = "def f(:\n"
        result = analyze_project(self.project)
        self.assertEqual(result["status"], "partial")
        self.assertIn("SYNTAX_ERROR", [d["code"] for d in result["diagnostics"]])

    def test_unsupported_loop_does_not_claim_valid_cfg(self):
        self.project["files"][0]["fileContent"] = "def f():\n    while True:\n        pass\n"
        result = analyze_project(self.project)
        self.assertEqual(result["status"], "partial")
        self.assertIn("UNSUPPORTED_STATEMENT", [d["code"] for d in result["diagnostics"]])

    def test_empty_if_branch_connects_correctly(self):
        self.project["files"][0]["fileContent"] = "def f(x):\n    if x:\n        pass\n    return x\n"
        result = analyze_project(self.project)
        self.assertEqual(result["status"], "ok")
        graph = result["graphs"]["P001:F001:FN001:FUNC"]
        self.assertTrue(any(e["edgeType"] == "false" for e in graph["edges"]))


if __name__ == "__main__":
    unittest.main()
