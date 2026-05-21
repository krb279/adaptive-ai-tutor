from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from src.core.types import StudentContext


class LocalMemory:
    def __init__(self, memory_dir: str | Path = "data/memory") -> None:
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, student_id: str) -> Path:
        safe_id = student_id.replace("/", "_").replace("\\", "_")
        return self.memory_dir / f"{safe_id}.json"

    def load(self, student_id: str = "default") -> StudentContext:
        path = self._path(student_id)
        if not path.exists():
            return StudentContext(student_id=student_id)
        data: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return StudentContext(**data)

    def save(self, context: StudentContext) -> None:
        self._path(context.student_id).write_text(
            json.dumps(asdict(context), indent=2),
            encoding="utf-8",
        )

    def add_history(self, student_id: str, event: Dict[str, Any]) -> None:
        context = self.load(student_id)
        context.history.append(event)
        context.history = context.history[-50:]
        self.save(context)
