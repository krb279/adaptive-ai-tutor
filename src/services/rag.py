from __future__ import annotations

from pathlib import Path
from typing import List


class SimpleRAG:
    """Small placeholder for local notes/PDF retrieval.

    Current version reads .txt and .md files from data/notes and returns simple
    keyword matches. Later, replace this with embeddings, PDF parsing, or vector DB.
    """

    def __init__(self, notes_dir: str | Path = "data/notes") -> None:
        self.notes_dir = Path(notes_dir)
        self.notes_dir.mkdir(parents=True, exist_ok=True)

    def search(self, query: str, limit: int = 3) -> List[str]:
        terms = [term.lower() for term in query.split() if len(term) > 2]
        matches: List[str] = []
        for path in list(self.notes_dir.glob("*.txt")) + list(self.notes_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            score = sum(1 for term in terms if term in text.lower())
            if score > 0:
                matches.append(f"Source: {path.name}\n{text[:800]}")
        return matches[:limit]
