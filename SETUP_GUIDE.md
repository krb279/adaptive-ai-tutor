# Setup Guide for Another Computer

This project is designed so another person, like your professor, can unzip it and run it with a simple setup path.

## What must be installed first

The computer needs:

1. **Python 3.10 or newer**
2. **Ollama** for the strongest local AI features

Ollama download page: https://ollama.com/download

The app can still open without Ollama, but the full tutor + evaluator/reviewer AI feedback works best when Ollama and the models are installed.

---

## Easiest way to run

### macOS / Linux

Open Terminal inside the project folder and run:

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

---

## New welcome screen

When the GUI opens, it now starts on a **Welcome screen**.

Press:

```text
Start Tutor + Check Setup
```

That button will:

- create an easy-to-find desktop project folder named `Adaptive_AI_Astronomy_Tutor`
- create a desktop data folder named `Adaptive_AI_Tutor_Data`
- check whether Ollama is installed
- pull the required Ollama models if Ollama is installed
- open the official Ollama download page if Ollama is missing
- then open the main tutoring interface

Important: Python packages and Ollama may still require the normal operating-system permissions. The app can check and guide the setup, but it cannot silently install system software on every computer without permission.

---

## Ollama model commands

The setup scripts and welcome screen try to pull these automatically if Ollama is installed:

```bash
ollama pull llama3.1
ollama pull mistral
```

The project uses:

- `llama3.1` as the tutor model
- `mistral` as the evaluator/reviewer model

If Ollama is installed but not running, start it with:

```bash
ollama serve
```

On many computers, Ollama also starts automatically after installation.

---

## Manual run commands

GUI version:

```bash
python3 -m src.ui.tk_app
```

Command-line version:

```bash
python3 -m src.ui.app
```

---

## Important note

Study guide generation requires Ollama. With Ollama installed and the two models pulled, the app uses the stronger tutor model and evaluator/reviewer model workflow.
