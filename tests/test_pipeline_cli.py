import json
import subprocess
import sys
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


@pytest.mark.parametrize("relative", [True, False])
def test_pipeline_runner_saves_matching_outputs_outside_repository(tmp_path, relative):
    source = tmp_path / "demo.py"
    source.write_bytes(b"def add(a, b):\r\n    return a + b\r\n")
    output = Path("results") if relative else tmp_path / "absolute-results"
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "file",
            str(source),
            "--revision-id",
            "3",
            "--output-dir",
            str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    directory = tmp_path / output
    flowchart = json.loads((directory / "demo_flowchart.json").read_text(encoding="utf-8"))
    mapping = json.loads((directory / "demo_mapping.json").read_text(encoding="utf-8"))
    analysis = json.loads((directory / "demo_analysis.json").read_text(encoding="utf-8"))
    assert flowchart["projectId"] == mapping["projectId"] == analysis["projectId"]
    assert flowchart["revisionId"] == mapping["revisionId"] == analysis["revisionId"] == 3
    assert flowchart["graphs"]
    assert mapping["sourceMappings"]


def test_pipeline_runner_rejects_negative_revision_before_writing_results(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "file",
            "unused.py",
            "--revision-id",
            "-1",
            "--output-dir",
            str(tmp_path / "results"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "--revision-id must be nonnegative" in result.stderr
    assert not (tmp_path / "results").exists()
