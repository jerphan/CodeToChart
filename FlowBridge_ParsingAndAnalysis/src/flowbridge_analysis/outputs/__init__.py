"""Explicit downstream projections of validated canonical analysis."""
from ..models import ProjectAnalysis


def _snapshot(analysis: ProjectAnalysis) -> dict[str, object]:
    """Validate canonical integrity before copying its serializable values."""
    analysis.__post_init__()
    return analysis.to_dict()


from .FlowchartOutput import FlowchartOutput
from .MappingOutput import MappingOutput

__all__ = ['FlowchartOutput', 'MappingOutput']
