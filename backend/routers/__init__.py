from .projects import router as projects_router
from .components import router as components_router
from .copilot import router as copilot_router
from .parsers import router as parsers_router
from .knowledge import router as knowledge_router
from .export import router as export_router

__all__ = [
    "projects_router", "components_router", "copilot_router",
    "parsers_router", "knowledge_router", "export_router",
]
