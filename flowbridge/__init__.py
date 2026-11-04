"""Keep the original import paths pointing to the current backend."""

import sys
from importlib import import_module

from FlowBridgeBackend import (
    CodeManager,
    FlowBridgePipeline,
    PyProject,
    SourceFile,
    pyProject,
    sourceFile,
)

__all__ = [
    "CodeManager",
    "FlowBridgePipeline",
    "PyProject",
    "SourceFile",
    "pyProject",
    "sourceFile",
]

# Aliases share the same classes and state; the implementation stays in FlowBridgeBackend.
for name in (
    "api",
    "cli",
    "config",
    "errors",
    "github",
    "models",
    "paths",
    "pipeline",
    "readers",
    "registry",
    "service",
):
    module = import_module(f"FlowBridgeBackend.{name}")
    sys.modules[f"{__name__}.{name}"] = module
    globals()[name] = module
