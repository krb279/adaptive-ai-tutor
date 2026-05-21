# Local Agentic AI Astronomy Tutor

A local AI-powered Astronomy tutor that generates adaptive study guides, checks student answers, tracks weak topics, and uses that progress to personalize the next guide. The project is built with Python, Tkinter, Ollama, and local JSON storage.

## Main idea

This project follows an adaptive learning loop:

```text
Generate guide → student answers → grade answers → save weak topics → next guide adapts
```

The app is designed to **generate**, not rely on a pre-written question bank. Study guides and practice questions are created dynamically through Ollama. If Ollama is not running, the app tells the user to start Ollama instead of loading pre-defined study guide questions.

## Features

- AI-generated college-level Astronomy study guides
- 10-guide adaptive learning path
- Student progress tracking through local JSON files
- Weak-topic tracking for personalized future guides
- Answer keys, explanations, and rubric keywords generated with each guide
- Desktop GUI version built with Tkinter
- CLI version for terminal use
- Regular tutor mode for explaining, hinting, practice, and grading
- Optional two-model flow where one Ollama model teaches and a second model reviews feedback
- Local-first design with no cloud database required

## Technologies used

- Python
- Tkinter
- Ollama
- JSON file storage
- Local AI model integration

## Project structure

```text
src/
  ui/
    app.py                         # CLI interface
    tk_app.py                      # Tkinter GUI interface
  core/
    orchestrator.py                # Main tutor control flow
    router.py                      # Routes Astronomy requests
    types.py                       # Shared request/response structures
  plugins/
    base.py                        # Subject plugin interface
    registry.py                    # Plugin registry
    astronomy/
      plugin.py                    # Astronomy tutoring plugin
  services/
    ollama_client.py               # Local Ollama API client
    progress_tracker.py            # Local adaptive progress memory
    study_guide_generator.py       # Adaptive study guide generator
    rag.py                         # Placeholder for future notes/PDF retrieval
    assessment.py                  # Shared assessment helpers
```

## Setup

### macOS / Linux

```bash
chmod +x setup_mac_linux.sh run_gui.sh
./setup_mac_linux.sh
./run_gui.sh
```

### Windows

Double-click:

```text
setup_windows.bat
```

Then double-click:

```text
run_gui_windows.bat
```

## Ollama setup

Install Ollama, then run:

```bash
ollama pull llama3.1
ollama serve
```

In a second Terminal or Command Prompt window, run the app.

Default model:

```text
llama3.1
```

Optional evaluator model:

```bash
ollama pull mistral
```

## Run the app manually

CLI version:

```bash
python3 -m src.ui.app
```

GUI version:

```bash
python3 -m src.ui.tk_app
```

On Windows, you may need to use:

```bash
python -m src.ui.tk_app
```

## How the adaptive guide feature works

1. The student enters a Student ID.
2. The student selects a main Astronomy topic.
3. Ollama generates a new study guide using the topic and the student's previous weak areas.
4. The student answers each question.
5. The app grades the answers using the generated answer key and rubric keywords.
6. Missed topics are saved locally.
7. The next guide uses those missed topics as adaptive focus areas.

## Where local data is stored

Generated study guides:

```text
data/study_guides/<student_id>/study_guide_01.json
```

Graded attempts:

```text
data/study_guides/<student_id>/study_guide_01_attempt.json
```

Progress memory:

```text
data/progress/<student_id>.json
```

These files are generated when the app runs and are intentionally ignored by Git.

## Important design choice: Generate, don't pre-define

Earlier versions included local fallback study guide questions. Those have been removed so the project better matches the requirement to generate content dynamically. Now, if Ollama is unavailable or returns invalid JSON, the app shows an error message and asks the user to start Ollama instead of silently using pre-written questions.

This makes the project clearer academically because the study guide content comes from the AI generation process, not from a hard-coded question bank.

## Professor explanation

This is an agentic tutoring system because it does more than answer one question at a time. It generates a study guide, evaluates student answers, records weak topics, and adapts the next guide based on the student's performance. Ollama acts as the local AI engine, while JSON files store the student's learning history locally.

## Author

Kedrick Bryant
