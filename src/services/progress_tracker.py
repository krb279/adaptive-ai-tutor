from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class GuideAttempt:
    guide_number: int
    topic: str
    score_percent: float
    missed_topics: List[str]
    saved_path: str


@dataclass
class StudentProgress:
    student_id: str = "default"
    completed_guides: int = 0
    weak_topics: Dict[str, int] = field(default_factory=dict)
    strengths: Dict[str, int] = field(default_factory=dict)
    attempts: List[Dict[str, Any]] = field(default_factory=list)


class ProgressTracker:
    """Stores student progress locally as JSON.

    This is the adaptive memory loop for the app. It remembers which astronomy
    topics the student missed and passes those weak areas into the next study
    guide prompt.
    """

    def __init__(self, progress_dir: str | Path = "data/progress") -> None:
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, student_id: str) -> Path:
        safe_id = student_id.replace("/", "_").replace("\\", "_").strip() or "default"
        return self.progress_dir / f"{safe_id}.json"

    def load(self, student_id: str = "default") -> StudentProgress:
        path = self._path(student_id)
        if not path.exists():
            return StudentProgress(student_id=student_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return StudentProgress(**data)

    def save(self, progress: StudentProgress) -> None:
        self._path(progress.student_id).write_text(
            json.dumps(asdict(progress), indent=2),
            encoding="utf-8",
        )

    def record_attempt(
        self,
        student_id: str,
        guide_number: int,
        topic: str,
        score_percent: float,
        missed_topics: List[str],
        mastered_topics: List[str],
        saved_path: str,
    ) -> StudentProgress:
        progress = self.load(student_id)
        progress.completed_guides = max(progress.completed_guides, guide_number)

        for topic_name in missed_topics:
            clean = topic_name.strip()
            if clean:
                progress.weak_topics[clean] = progress.weak_topics.get(clean, 0) + 1

        for topic_name in mastered_topics:
            clean = topic_name.strip()
            if clean:
                progress.strengths[clean] = progress.strengths.get(clean, 0) + 1

        progress.attempts.append(
            asdict(
                GuideAttempt(
                    guide_number=guide_number,
                    topic=topic,
                    score_percent=score_percent,
                    missed_topics=missed_topics,
                    saved_path=saved_path,
                )
            )
        )
        progress.attempts = progress.attempts[-20:]
        self.save(progress)
        return progress

    def top_weak_topics(self, student_id: str, limit: int = 5) -> List[str]:
        progress = self.load(student_id)
        return [
            topic for topic, _count in sorted(
                progress.weak_topics.items(), key=lambda item: item[1], reverse=True
            )[:limit]
        ]
