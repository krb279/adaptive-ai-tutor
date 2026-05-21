from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.services.ollama_client import OllamaClient
from src.services.progress_tracker import ProgressTracker


ASTRONOMY_STUDY_GUIDE_SYSTEM = """
You are a college-level Astronomy professor and tutor.
Create rigorous but readable undergraduate astronomy study guides.
Return valid JSON only when asked for JSON.
Questions should include a balanced mix of conceptual, short-answer, and calculation questions.
Keep everything focused on Astronomy: celestial motion, light, spectra, stars, galaxies, cosmology, telescopes, planets, exoplanets, and the Solar System.
""".strip()


@dataclass
class StudyQuestion:
    id: int
    type: str
    topic: str
    difficulty: str
    question: str
    answer: str
    explanation: str
    rubric_keywords: List[str] = field(default_factory=list)


@dataclass
class StudyGuide:
    guide_number: int
    title: str
    student_id: str
    main_topic: str
    adaptive_focus: List[str]
    questions: List[StudyQuestion]


class StudyGuideManager:
    """Generates, saves, grades, and adapts 10 Astronomy study guides.

    Primary app feature:
    1. Generate a college-level guide with an answer key.
    2. Student answers the guide.
    3. The guide is graded.
    4. Mistakes are saved locally.
    5. The next guide focuses more on those mistakes.
    """

    def __init__(
        self,
        guides_dir: str | Path = "data/study_guides",
        ollama: OllamaClient | None = None,
        tracker: ProgressTracker | None = None,
    ) -> None:
        self.guides_dir = Path(guides_dir)
        self.guides_dir.mkdir(parents=True, exist_ok=True)
        self.ollama = ollama or OllamaClient(timeout=60)
        self.tracker = tracker or ProgressTracker()

    def _student_dir(self, student_id: str) -> Path:
        safe_id = student_id.replace("/", "_").replace("\\", "_").strip() or "default"
        path = self.guides_dir / safe_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _guide_path(self, student_id: str, guide_number: int) -> Path:
        return self._student_dir(student_id) / f"study_guide_{guide_number:02d}.json"

    def _attempt_path(self, student_id: str, guide_number: int) -> Path:
        return self._student_dir(student_id) / f"study_guide_{guide_number:02d}_attempt.json"

    def next_guide_number(self, student_id: str) -> int:
        progress = self.tracker.load(student_id)
        return min(progress.completed_guides + 1, 10)

    def generate_guide(self, student_id: str, main_topic: str = "General Astronomy", question_count: int = 10) -> Tuple[StudyGuide, bool]:
        guide_number = self.next_guide_number(student_id)
        weak_topics = self.tracker.top_weak_topics(student_id, limit=5)

        prompt = f"""
Generate Study Guide {guide_number} of 10 for a college-level Astronomy tutor app.
Student ID: {student_id}
Main topic requested: {main_topic}
Number of questions: {question_count}
Adaptive focus based on prior mistakes: {weak_topics or ['none yet; create a balanced diagnostic guide']}

Rules:
- Return valid JSON only. No markdown.
- Use exactly this schema:
{{
  "title": "string",
  "main_topic": "string",
  "adaptive_focus": ["string"],
  "questions": [
    {{
      "id": 1,
      "type": "multiple choice | short answer | calculation | explanation",
      "topic": "specific astronomy topic",
      "difficulty": "college intro | college intermediate",
      "question": "student-facing question",
      "answer": "answer key answer",
      "explanation": "why the answer is correct",
      "rubric_keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ]
}}
- Include a mix of conceptual questions and calculation questions.
- At least 4 questions should target the adaptive focus topics when weak topics exist.
- Include formulas and units where relevant.
""".strip()

        result = self.ollama.generate(prompt=prompt, system=ASTRONOMY_STUDY_GUIDE_SYSTEM, temperature=0.45)
        if not (result.used_ollama and result.text):
            raise RuntimeError(
                "Ollama is required to generate a new study guide. "
                "Start Ollama, pull the model, and try again. "
                f"Details: {result.error or 'No response returned from Ollama.'}"
            )

        try:
            guide = self._parse_guide_json(result.text, student_id, guide_number, main_topic, weak_topics)
        except Exception as exc:
            raise RuntimeError(
                "Ollama responded, but the response was not valid study-guide JSON. "
                "Try generating again, or use a stronger local model. "
                f"Details: {exc}"
            ) from exc

        self.save_guide(guide)
        return guide, True

    def _parse_guide_json(
        self,
        raw_text: str,
        student_id: str,
        guide_number: int,
        main_topic: str,
        weak_topics: List[str],
    ) -> StudyGuide:
        json_text = self._extract_json(raw_text)
        data = json.loads(json_text)
        questions = []
        for idx, item in enumerate(data.get("questions", []), start=1):
            questions.append(
                StudyQuestion(
                    id=int(item.get("id", idx)),
                    type=str(item.get("type", "short answer")),
                    topic=str(item.get("topic", main_topic)),
                    difficulty=str(item.get("difficulty", "college intro")),
                    question=str(item.get("question", "")),
                    answer=str(item.get("answer", "")),
                    explanation=str(item.get("explanation", "")),
                    rubric_keywords=[str(x) for x in item.get("rubric_keywords", [])],
                )
            )
        if not questions:
            raise ValueError("Ollama returned no questions")
        return StudyGuide(
            guide_number=guide_number,
            title=str(data.get("title", f"Astronomy Adaptive Study Guide {guide_number}")),
            student_id=student_id,
            main_topic=str(data.get("main_topic", main_topic)),
            adaptive_focus=[str(x) for x in data.get("adaptive_focus", weak_topics)],
            questions=questions[:10],
        )

    def _extract_json(self, text: str) -> str:
        clean = text.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?", "", clean).strip()
            clean = re.sub(r"```$", "", clean).strip()
        first = clean.find("{")
        last = clean.rfind("}")
        if first == -1 or last == -1:
            raise ValueError("No JSON object found")
        return clean[first:last + 1]

    def save_guide(self, guide: StudyGuide) -> Path:
        path = self._guide_path(guide.student_id, guide.guide_number)
        data = asdict(guide)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def load_guide(self, student_id: str, guide_number: int) -> StudyGuide:
        path = self._guide_path(student_id, guide_number)
        data = json.loads(path.read_text(encoding="utf-8"))
        questions = [StudyQuestion(**q) for q in data["questions"]]
        return StudyGuide(
            guide_number=data["guide_number"],
            title=data["title"],
            student_id=data["student_id"],
            main_topic=data["main_topic"],
            adaptive_focus=data.get("adaptive_focus", []),
            questions=questions,
        )

    def render_student_copy(self, guide: StudyGuide) -> str:
        lines = [f"{guide.title}", f"Guide {guide.guide_number}/10", f"Topic: {guide.main_topic}"]
        if guide.adaptive_focus:
            lines.append(f"Adaptive focus: {', '.join(guide.adaptive_focus)}")
        lines.append("\nAnswer each question. The app will grade your answers and use missed topics to build the next guide.\n")
        for q in guide.questions:
            lines.append(f"{q.id}. [{q.type} | {q.topic}] {q.question}")
        return "\n".join(lines)

    def render_answer_key(self, guide: StudyGuide) -> str:
        lines = [f"ANSWER KEY: {guide.title}"]
        for q in guide.questions:
            lines.append(f"\n{q.id}. Topic: {q.topic}")
            lines.append(f"Answer: {q.answer}")
            lines.append(f"Explanation: {q.explanation}")
            if q.rubric_keywords:
                lines.append(f"Rubric keywords: {', '.join(q.rubric_keywords)}")
        return "\n".join(lines)

    def grade_answers(self, guide: StudyGuide, answers: Dict[int, str]) -> Dict[str, Any]:
        graded_questions = []
        total = 0.0
        missed_topics: List[str] = []
        mastered_topics: List[str] = []

        for q in guide.questions:
            student_answer = answers.get(q.id, "").strip()
            score, feedback = self._grade_one(q, student_answer)
            total += score
            if score < 7:
                missed_topics.append(q.topic)
            else:
                mastered_topics.append(q.topic)
            graded_questions.append(
                {
                    "id": q.id,
                    "topic": q.topic,
                    "question": q.question,
                    "student_answer": student_answer,
                    "score_out_of_10": score,
                    "feedback": feedback,
                    "answer_key": q.answer,
                }
            )

        score_percent = round((total / (len(guide.questions) * 10)) * 100, 1) if guide.questions else 0.0
        result = {
            "guide_number": guide.guide_number,
            "title": guide.title,
            "score_percent": score_percent,
            "missed_topics": sorted(set(missed_topics)),
            "mastered_topics": sorted(set(mastered_topics)),
            "graded_questions": graded_questions,
            "next_step": self._next_step(sorted(set(missed_topics))),
        }

        attempt_path = self._attempt_path(guide.student_id, guide.guide_number)
        attempt_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        progress = self.tracker.record_attempt(
            student_id=guide.student_id,
            guide_number=guide.guide_number,
            topic=guide.main_topic,
            score_percent=score_percent,
            missed_topics=result["missed_topics"],
            mastered_topics=result["mastered_topics"],
            saved_path=str(attempt_path),
        )
        result["progress"] = asdict(progress)
        result["attempt_path"] = str(attempt_path)
        return result

    def _grade_one(self, question: StudyQuestion, student_answer: str) -> Tuple[float, str]:
        if not student_answer:
            return 0.0, "No answer entered. Review the topic and try this again."

        keywords = [kw.lower() for kw in question.rubric_keywords if kw.strip()]
        answer_lower = student_answer.lower()
        matched = [kw for kw in keywords if kw in answer_lower]

        if keywords:
            ratio = len(matched) / len(keywords)
            if ratio >= 0.75:
                return 9.0, "Strong answer. You included most of the important astronomy vocabulary or calculation pieces."
            if ratio >= 0.45:
                return 7.0, "Partially correct. Add more key terms, units, formulas, or explanation from the answer key."
            if ratio >= 0.2:
                return 5.0, "You are on the right track, but the answer is missing several required ideas."
            return 3.0, "This answer does not yet show the main concept. Compare it carefully with the answer key."

        # Backup grading if Ollama did not provide rubric keywords.
        expected_words = set(re.findall(r"[a-zA-Z]{4,}", question.answer.lower()))
        student_words = set(re.findall(r"[a-zA-Z]{4,}", answer_lower))
        overlap = len(expected_words & student_words)
        if overlap >= 5:
            return 8.0, "Mostly correct based on overlap with the answer key."
        if overlap >= 2:
            return 6.0, "Some correct ideas are present, but the answer needs more detail."
        return 4.0, "Needs work. Review the answer key and retry similar questions."

    def _next_step(self, missed_topics: List[str]) -> str:
        if not missed_topics:
            return "Great job. The next study guide can increase difficulty and introduce more synthesis questions."
        return "Next guide should focus on: " + ", ".join(missed_topics[:5])
