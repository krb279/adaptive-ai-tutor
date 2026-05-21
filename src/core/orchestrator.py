from __future__ import annotations

from src.core.router import Router
from src.core.types import TutorRequest, TutorResponse
from src.plugins.registry import build_default_registry
from src.services.memory import LocalMemory
from src.services.rag import SimpleRAG


class TutorOrchestrator:
    def __init__(self, memory: LocalMemory | None = None, rag: SimpleRAG | None = None) -> None:
        self.registry = build_default_registry()
        self.router = Router(self.registry)
        self.memory = memory or LocalMemory()
        self.rag = rag or SimpleRAG()

    def handle(self, request: TutorRequest) -> TutorResponse:
        context = self.memory.load(request.context.student_id if request.context else "default")
        request.context = context

        plugin = self.router.route(request)
        response = plugin.handle(request)

        self.memory.add_history(
            context.student_id,
            {
                "subject": response.subject,
                "action": response.action.value,
                "message": request.message,
                "answer": request.answer,
                "response": response.message,
            },
        )
        return response

    def subjects(self) -> list[str]:
        return self.registry.subjects()
