from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TutorAction(str, Enum):
    EXPLAIN = "explain"
    HINT = "hint"
    PRACTICE = "practice"
    GRADE = "grade"


@dataclass
class StudentContext:
    student_id: str = "default"
    level: str = "beginner"
    preferences: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TutorRequest:
    message: str
    action: TutorAction
    subject: Optional[str] = None
    answer: Optional[str] = None
    context: Optional[StudentContext] = None


@dataclass
class TutorResponse:
    message: str
    subject: str = "general"
    action: TutorAction = TutorAction.EXPLAIN
    confidence: float = 0.75
    metadata: Dict[str, Any] = field(default_factory=dict)
