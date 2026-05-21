from src.services.study_guide_generator import StudyGuideManager

manager = StudyGuideManager(guides_dir="data/test_study_guides")
guide, used_ollama = manager.generate_guide("test_student", "General Astronomy", question_count=10)
print("Generated:", guide.title)
print("Questions:", len(guide.questions))
print("Used Ollama:", used_ollama)
answers = {q.id: "test answer" for q in guide.questions}
result = manager.grade_answers(guide, answers)
print("Score:", result["score_percent"])
print("Missed:", result["missed_topics"])
