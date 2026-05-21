from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.core.types import TutorAction, TutorRequest, TutorResponse


class SubjectPlugin(ABC):
    subject: str = "base"
    keywords: List[str] = []

    def can_handle(self, request: TutorRequest) -> bool:
        if request.subject and request.subject.lower() == self.subject:
            return True
        text = request.message.lower()
        return any(keyword.lower() in text for keyword in self.keywords)

    def handle(self, request: TutorRequest) -> TutorResponse:
        if request.action == TutorAction.EXPLAIN:
            return self.explain(request)
        if request.action == TutorAction.HINT:
            return self.hint(request)
        if request.action == TutorAction.PRACTICE:
            return self.generate_practice(request)
        if request.action == TutorAction.GRADE:
            return self.grade(request)
        return TutorResponse(
            message="I do not recognize that tutoring action yet.",
            subject=self.subject,
            action=request.action,
            confidence=0.2,
        )

    @abstractmethod
    def explain(self, request: TutorRequest) -> TutorResponse:
        raise NotImplementedError

    @abstractmethod
    def hint(self, request: TutorRequest) -> TutorResponse:
        raise NotImplementedError

    @abstractmethod
    def generate_practice(self, request: TutorRequest) -> TutorResponse:
        raise NotImplementedError

    @abstractmethod
    def grade(self, request: TutorRequest) -> TutorResponse:
        raise NotImplementedError
