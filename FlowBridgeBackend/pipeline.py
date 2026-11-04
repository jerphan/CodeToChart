"""Pipeline connecting FlowBridge CodeManager and Parsing & Analysis modules."""

import sys
from pathlib import Path
from typing import Any

# Ensure FlowBridge_ParsingAndAnalysis src directory is on sys.path
_analysis_src = Path(__file__).resolve().parents[1] / "FlowBridge_ParsingAndAnalysis" / "src"
if _analysis_src.is_dir() and str(_analysis_src) not in sys.path:
    sys.path.insert(0, str(_analysis_src))

from flowbridge_analysis import (  # noqa: E402
    CodeManagerInputAdapter,
    FlowchartOutput,
    MappingOutput,
    ParsingAnalysisService,
)

from .models import PyProject  # noqa: E402
from .service import CodeManager  # noqa: E402


class FlowBridgePipeline:
    """Coordinate CodeManager source acquisition and static parsing/flowchart analysis."""

    def __init__(self, manager: CodeManager | None = None) -> None:
        self.manager = manager or CodeManager()
        self.adapter = CodeManagerInputAdapter()
        self.analysis_service = ParsingAnalysisService()

    def analyze_project(
        self, project: PyProject, *, revision_id: int = 1
    ) -> dict[str, Any]:
        """Normalize a PyProject snapshot from CodeManager and run static analysis."""
        payload = project.model_dump()
        normalized = self.adapter.normalize(payload, revision_id=revision_id)
        analysis = self.analysis_service.analyze_project(normalized)
        flowchart = FlowchartOutput(analysis)
        mapping = MappingOutput(analysis)

        return {
            "status": analysis.status,
            "revisionId": analysis.revision_id,
            "projectId": analysis.project_id,
            "projectName": analysis.project_name,
            "analysis": analysis.to_dict(),
            "flowchart": flowchart.to_dict(),
            "mapping": mapping.to_dict(),
        }

    def analyze_current(self, *, revision_id: int = 1) -> dict[str, Any]:
        """Analyze the current project loaded in this pipeline's CodeManager."""
        project = self.manager.getProject()
        return self.analyze_project(project, revision_id=revision_id)
