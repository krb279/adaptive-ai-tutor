from __future__ import annotations

from typing import Dict

from src.core.orchestrator import TutorOrchestrator
from src.core.types import TutorAction, TutorRequest, StudentContext
from src.services.ollama_client import OllamaClient
from src.services.progress_tracker import ProgressTracker
from src.services.study_guide_generator import StudyGuideManager


def choose_action(raw: str) -> TutorAction:
    raw = raw.strip().lower()
    aliases = {
        "1": TutorAction.EXPLAIN,
        "2": TutorAction.HINT,
        "3": TutorAction.PRACTICE,
        "4": TutorAction.GRADE,
        "explain": TutorAction.EXPLAIN,
        "hint": TutorAction.HINT,
        "practice": TutorAction.PRACTICE,
        "generate practice": TutorAction.PRACTICE,
        "grade": TutorAction.GRADE,
    }
    return aliases.get(raw, TutorAction.EXPLAIN)


def run_adaptive_study_guide(manager: StudyGuideManager, student_id: str) -> None:
    progress = manager.tracker.load(student_id)
    if progress.completed_guides >= 10:
        print("\nYou already completed all 10 adaptive study guides.")
        print("You can reset by deleting data/progress and data/study_guides, or use a new student ID.")
        return

    default_topic = "General Astronomy"
    topic = input(f"Main topic for this guide [{default_topic}]: ").strip() or default_topic
    try:
        guide, used_ollama = manager.generate_guide(student_id=student_id, main_topic=topic, question_count=10)
    except RuntimeError as exc:
        print("\nStudy guide was not generated.")
        print(exc)
        print("\nStart Ollama, pull the model, and try again:")
        print("  ollama pull llama3.1")
        print("  ollama serve")
        return

    print("\n" + "=" * 70)
    print(manager.render_student_copy(guide))
    print("=" * 70)
    print("\nAnswer the questions below. Your mistakes will train the next study guide.")
    print("Type 'skip' to leave a question blank.\n")

    answers: Dict[int, str] = {}
    for question in guide.questions:
        answer = input(f"Answer {question.id}: ").strip()
        if answer.lower() == "skip":
            answer = ""
        answers[question.id] = answer

    result = manager.grade_answers(guide, answers)

    print("\n" + "=" * 70)
    print(f"RESULTS FOR {guide.title}")
    print(f"Score: {result['score_percent']}%")
    print(f"Missed topics: {', '.join(result['missed_topics']) if result['missed_topics'] else 'None'}")
    print(f"Next step: {result['next_step']}")
    print("\nQuestion Feedback:")
    for item in result["graded_questions"]:
        print(f"\n{item['id']}. {item['topic']} — {item['score_out_of_10']}/10")
        print(f"Feedback: {item['feedback']}")
        print(f"Answer key: {item['answer_key']}")

    print("\nSaved files:")
    print(f"- Study guide: data/study_guides/{student_id}/study_guide_{guide.guide_number:02d}.json")
    print(f"- Graded attempt: {result['attempt_path']}")
    print("- Progress memory: data/progress/" + student_id + ".json")
    print("\nGeneration mode:", "Ollama-generated" if used_ollama else "generation unavailable")
    print("=" * 70)


def view_progress(tracker: ProgressTracker, student_id: str) -> None:
    progress = tracker.load(student_id)
    print("\n--- Student Progress ---")
    print(f"Student: {progress.student_id}")
    print(f"Completed guides: {progress.completed_guides}/10")
    if progress.weak_topics:
        print("Weak topics:")
        for topic, count in sorted(progress.weak_topics.items(), key=lambda x: x[1], reverse=True):
            print(f"- {topic}: missed {count} time(s)")
    else:
        print("Weak topics: none yet")
    if progress.strengths:
        print("Strengths:")
        for topic, count in sorted(progress.strengths.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"- {topic}: strong {count} time(s)")
    print("------------------------")


def run_regular_tutor(tutor: TutorOrchestrator, context: StudentContext) -> None:
    print("\nRegular Astronomy Tutor Mode")
    print("1. Explain | 2. Hint | 3. Generate one practice question | 4. Grade one answer")
    action_raw = input("Selection: ").strip()
    action = choose_action(action_raw)
    message = input("Astronomy question or topic: ").strip()
    answer = None
    if action == TutorAction.GRADE:
        answer = input("Student answer to grade: ").strip()
    request = TutorRequest(
        message=message,
        action=action,
        subject="astronomy",
        answer=answer,
        context=context,
    )
    response = tutor.handle(request)
    print("\n--- Astronomy Tutor Response ---")
    print(response.message)
    print("--------------------------------")


def main() -> None:
    tutor = TutorOrchestrator()
    ollama = OllamaClient(timeout=60)
    tracker = ProgressTracker()
    guide_manager = StudyGuideManager(ollama=ollama, tracker=tracker)

    print("Local Agentic AI Astronomy Tutor")
    print("Primary feature: 10 adaptive study guides with answer keys")
    print("Subject: Astronomy only")
    print(f"Ollama model: {ollama.model}")
    print("Ollama status:", "connected" if ollama.is_available() else "not connected; study guide generation requires Ollama")
    print("Type 'quit' to exit.\n")

    student_id = input("Student name/id [default]: ").strip() or "default"
    level = input("Student level [college]: ").strip() or "college"
    preferences = {"subject": "astronomy", "llm": "ollama", "primary_feature": "adaptive_study_guides"}
    context = StudentContext(student_id=student_id, level=level, preferences=preferences)

    while True:
        print("\nMain Menu:")
        print("1. Start next adaptive study guide")
        print("2. View progress and weak topics")
        print("3. Regular tutor mode: explain / hint / practice / grade")
        print("4. Exit")

        choice = input("Selection: ").strip().lower()
        if choice in {"quit", "exit", "4"}:
            break
        if choice == "1":
            run_adaptive_study_guide(guide_manager, student_id)
        elif choice == "2":
            view_progress(tracker, student_id)
        elif choice == "3":
            run_regular_tutor(tutor, context)
        else:
            print("Please choose 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
