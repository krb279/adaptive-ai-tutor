from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, scrolledtext, simpledialog, ttk
from typing import Dict

from src.services.ollama_client import OllamaClient
from src.services.progress_tracker import ProgressTracker
from src.services.study_guide_generator import StudyGuide, StudyGuideManager


class AstronomyTutorGUI(tk.Tk):
    """Professional Tkinter desktop interface for the adaptive Astronomy tutor.

    This GUI does not replace the CLI. It uses the same StudyGuideManager,
    ProgressTracker, and OllamaClient that the command-line app already uses.
    """

    BG = "#eef3f8"
    NAVY = "#0b132b"
    NAVY_2 = "#16213e"
    BLUE = "#2563eb"
    BLUE_DARK = "#1d4ed8"
    CYAN = "#38bdf8"
    CARD = "#ffffff"
    TEXT = "#111827"
    MUTED = "#64748b"
    BORDER = "#d9e2ec"
    SUCCESS = "#16a34a"
    WARNING = "#f97316"

    def __init__(self) -> None:
        super().__init__()
        self.title("Adaptive AI Astronomy Tutor")
        self.geometry("1220x820")
        self.minsize(1040, 720)
        self.configure(bg=self.BG)

        self.ollama = OllamaClient(timeout=60)
        # Second Ollama role: evaluator/reviewer model.
        # Set OLLAMA_EVALUATOR_MODEL to a different pulled model, for example:
        # export OLLAMA_EVALUATOR_MODEL=mistral
        evaluator_model = os.getenv("OLLAMA_EVALUATOR_MODEL", "mistral")
        self.evaluator_ollama = OllamaClient(model=evaluator_model, timeout=60)
        self.tracker = ProgressTracker()
        self.manager = StudyGuideManager(ollama=self.ollama, tracker=self.tracker)

        self.current_guide: StudyGuide | None = None
        self.answer_boxes: Dict[int, tk.Text] = {}
        self.last_grade_result = None
        self.last_missed_items: list[Dict] = []

        self.student_id_var = tk.StringVar(value="default")
        self.level_var = tk.StringVar(value="college")
        self.topic_var = tk.StringVar(value="General Astronomy")
        self.status_var = tk.StringVar(value="Welcome screen ready")

        self._configure_styles()
        self._build_welcome_screen()

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _desktop_dir(self) -> Path:
        desktop = Path.home() / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)
        return desktop

    def _desktop_project_dir(self) -> Path:
        return self._desktop_dir() / "Adaptive_AI_Astronomy_Tutor"

    def _desktop_data_dir(self) -> Path:
        return self._desktop_dir() / "Adaptive_AI_Tutor_Data"

    def _build_welcome_screen(self) -> None:
        """Show a first screen before the main tutor interface."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.welcome_frame = tk.Frame(self, bg=self.NAVY)
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")
        self.welcome_frame.columnconfigure(0, weight=1)
        self.welcome_frame.rowconfigure(0, weight=1)

        card = tk.Frame(self.welcome_frame, bg=self.CARD, padx=36, pady=32)
        card.grid(row=0, column=0)

        tk.Label(card, text="Adaptive AI Astronomy Tutor", bg=self.CARD, fg=self.NAVY, font=self._font(0.032, 24, 36, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(
            card,
            text="Welcome. Press Start to prepare the desktop folder, check Ollama, pull the tutor/reviewer models if Ollama is installed, and open the tutoring interface.",
            bg=self.CARD, fg=self.TEXT, wraplength=650, justify=tk.LEFT, font=self._font(0.013, 11, 15),
        ).grid(row=1, column=0, sticky="w", pady=(12, 18))

        self.welcome_status = scrolledtext.ScrolledText(
            card, width=78, height=11, wrap=tk.WORD, bg="#f8fafc", fg=self.TEXT,
            relief=tk.SOLID, bd=1, padx=10, pady=10, font=self._font(0.0115, 9, 12),
        )
        self.welcome_status.grid(row=2, column=0, sticky="ew")
        self.welcome_status.insert(tk.END, "Ready to start.\n\nThis setup only needs internet if Ollama needs to download local AI models.\nIf Ollama is not installed, the app will open the official Ollama download page. Study guides require Ollama generation.\n")
        self.welcome_status.configure(state=tk.DISABLED)

        buttons = tk.Frame(card, bg=self.CARD)
        buttons.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        buttons.columnconfigure(0, weight=1)
        self.start_button = ttk.Button(buttons, text="Start Tutor + Check Setup", style="Primary.TButton", command=self.start_from_welcome)
        self.start_button.grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Open Ollama Download Page", style="Secondary.TButton", command=lambda: webbrowser.open("https://ollama.com/download")).grid(row=0, column=1, sticky="e", padx=(10, 0))

    def _welcome_log(self, text: str) -> None:
        self.welcome_status.configure(state=tk.NORMAL)
        self.welcome_status.insert(tk.END, text + "\n")
        self.welcome_status.see(tk.END)
        self.welcome_status.configure(state=tk.DISABLED)
        self.update_idletasks()

    def start_from_welcome(self) -> None:
        self.start_button.configure(state=tk.DISABLED)
        self.configure(cursor="watch")
        self._welcome_log("Starting setup checks...")
        threading.Thread(target=self._welcome_setup_worker, daemon=True).start()

    def _copy_project_to_desktop_if_needed(self) -> str:
        root = self._project_root()
        desktop_project = self._desktop_project_dir()
        try:
            if desktop_project.exists() and root.resolve() == desktop_project.resolve():
                return f"Project already running from Desktop: {desktop_project}"
            if not desktop_project.exists():
                ignore = shutil.ignore_patterns(".venv", "__pycache__", "*.pyc", ".DS_Store")
                shutil.copytree(root, desktop_project, ignore=ignore)
                return f"Created desktop project folder: {desktop_project}"
            return f"Desktop project folder already exists: {desktop_project}"
        except Exception as exc:
            return f"Desktop project copy skipped: {exc}"

    def _ensure_desktop_data_folder(self) -> str:
        data_dir = self._desktop_data_dir()
        try:
            (data_dir / "progress").mkdir(parents=True, exist_ok=True)
            (data_dir / "attempts").mkdir(parents=True, exist_ok=True)
            return f"Desktop data folder ready: {data_dir}"
        except Exception as exc:
            return f"Could not create desktop data folder: {exc}"

    def _pull_ollama_model(self, model: str) -> str:
        try:
            result = subprocess.run(["ollama", "pull", model], capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                return f"Ollama model ready: {model}"
            return f"Could not pull {model}: {(result.stderr or result.stdout).strip()[:300]}"
        except subprocess.TimeoutExpired:
            return f"Model download timed out for {model}. You can run: ollama pull {model}"
        except Exception as exc:
            return f"Could not pull {model}: {exc}"

    def _welcome_setup_worker(self) -> None:
        steps = [f"Python ready: {sys.version.split()[0]}", self._ensure_desktop_data_folder(), self._copy_project_to_desktop_if_needed()]
        if shutil.which("ollama"):
            steps.append("Ollama found. Checking local models...")
            for model in [self.ollama.model, self.evaluator_ollama.model]:
                steps.append(self._pull_ollama_model(model))
        else:
            steps.append("Ollama was not found on this computer.")
            steps.append("Opening the official Ollama download page. Install it for full AI tutor/reviewer mode.")
            try:
                webbrowser.open("https://ollama.com/download")
            except Exception:
                pass
        for line in steps:
            self.after(0, lambda message=line: self._welcome_log(message))
        self.after(0, self._finish_welcome_setup)

    def _finish_welcome_setup(self) -> None:
        self.configure(cursor="")
        self.welcome_frame.destroy()
        self.status_var.set(self._ollama_status_text())
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self._build_layout()
        self.refresh_progress()

    def _font_size(self, percent: float, minimum: int, maximum: int) -> int:
        """Calculate font size from screen height so the GUI scales better."""
        screen_height = max(self.winfo_screenheight(), 720)
        return max(minimum, min(maximum, int(screen_height * percent)))

    def _font(self, percent: float, minimum: int, maximum: int, weight: str | None = None) -> tuple:
        size = self._font_size(percent, minimum, maximum)
        return ("Arial", size, weight) if weight else ("Arial", size)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.CARD, relief="flat")
        style.configure("Sidebar.TFrame", background=self.NAVY)
        style.configure("Header.TFrame", background=self.NAVY)
        style.configure("Question.TLabelframe", background=self.CARD, bordercolor=self.BORDER, relief="solid")
        style.configure("Question.TLabelframe.Label", background=self.CARD, foreground=self.BLUE_DARK, font=self._font(0.012, 10, 13, "bold"))

        style.configure("Title.TLabel", background=self.NAVY, foreground="white", font=self._font(0.026, 20, 30, "bold"))
        style.configure("Subtitle.TLabel", background=self.NAVY, foreground="#cbd5e1", font=self._font(0.012, 10, 14))
        style.configure("Section.TLabel", background=self.CARD, foreground=self.TEXT, font=self._font(0.017, 13, 18, "bold"))
        style.configure("Body.TLabel", background=self.CARD, foreground=self.TEXT, font=self._font(0.0115, 9, 12))
        style.configure("Muted.TLabel", background=self.CARD, foreground=self.MUTED, font=self._font(0.0115, 9, 12))
        style.configure("Status.TLabel", background=self.NAVY, foreground=self.CYAN, font=self._font(0.0115, 9, 12, "bold"))
        style.configure("SidebarTitle.TLabel", background=self.NAVY, foreground="white", font=self._font(0.018, 14, 20, "bold"))
        style.configure("Sidebar.TLabel", background=self.NAVY, foreground="#e2e8f0", font=self._font(0.0115, 9, 12))
        style.configure("SidebarMuted.TLabel", background=self.NAVY, foreground="#94a3b8", font=self._font(0.0105, 8, 11))

        style.configure("TEntry", fieldbackground="white", bordercolor=self.BORDER, relief="solid", padding=6)
        style.configure("Primary.TButton", background=self.BLUE, foreground="white", font=self._font(0.0115, 9, 12, "bold"), padding=(14, 9), borderwidth=0)
        style.map("Primary.TButton", background=[("active", self.BLUE_DARK)])
        style.configure("Secondary.TButton", background="#e2e8f0", foreground=self.TEXT, font=self._font(0.0115, 9, 12, "bold"), padding=(12, 8), borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#cbd5e1")])
        style.configure("Accent.TButton", background=self.SUCCESS, foreground="white", font=self._font(0.0115, 9, 12, "bold"), padding=(12, 8), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#15803d")])

    def _ollama_status_text(self) -> str:
        tutor_status = "CONNECTED" if self.ollama.is_available() else "LOCAL FALLBACK READY"
        evaluator_status = "CONNECTED" if getattr(self, "evaluator_ollama", None) and self.evaluator_ollama.is_available() else "OPTIONAL"
        evaluator_model = getattr(getattr(self, "evaluator_ollama", None), "model", "mistral")
        return f"Tutor Model: {self.ollama.model} ({tutor_status})   •   Reviewer Model: {evaluator_model} ({evaluator_status})"

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()
        self._build_main_area()

    def _build_header(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(22, 18))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="✦ Adaptive AI Astronomy Tutor", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="College-level practice guides that adapt after every attempt using local progress memory + Ollama.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").grid(row=0, column=1, sticky="e", padx=(16, 0))

    def _build_main_area(self) -> None:
        shell = ttk.Frame(self, padding=16)
        shell.grid(row=1, column=0, sticky="nsew")
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", padding=(18, 18))
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        sidebar.columnconfigure(0, minsize=260)

        ttk.Label(sidebar, text="Student Setup", style="SidebarTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(sidebar, text="Set the learner profile, then generate the next adaptive guide.", style="SidebarMuted.TLabel", wraplength=230).grid(row=1, column=0, sticky="w", pady=(4, 18))

        self._sidebar_field(sidebar, "Student ID", self.student_id_var, 2)
        self._sidebar_field(sidebar, "Course Level", self.level_var, 4)
        self._sidebar_field(sidebar, "Main Topic", self.topic_var, 6)

        ttk.Button(sidebar, text="Generate Next Study Guide", style="Primary.TButton", command=self.generate_guide).grid(row=8, column=0, sticky="ew", pady=(18, 8))
        ttk.Button(sidebar, text="Refresh Progress", style="Secondary.TButton", command=self.refresh_progress).grid(row=9, column=0, sticky="ew")

        ttk.Separator(sidebar).grid(row=10, column=0, sticky="ew", pady=18)
        ttk.Label(sidebar, text="How it works", style="SidebarTitle.TLabel").grid(row=11, column=0, sticky="w")
        ttk.Label(
            sidebar,
            text="1. Generate a 10-question guide\n2. Answer each question\n3. Grade the attempt\n4. Weak topics shape the next guide\n5. Repeat until all 10 are complete",
            style="Sidebar.TLabel",
            justify=tk.LEFT,
        ).grid(row=12, column=0, sticky="w", pady=(8, 0))

        ttk.Label(sidebar, text="Tip: use a new Student ID to reset the adaptive path.", style="SidebarMuted.TLabel", wraplength=230).grid(row=13, column=0, sticky="w", pady=(24, 0))

        main = ttk.PanedWindow(shell, orient=tk.HORIZONTAL)
        main.grid(row=0, column=1, sticky="nsew")

        left = ttk.Frame(main, style="Card.TFrame", padding=16)
        right = ttk.Frame(main, style="Card.TFrame", padding=16)
        main.add(left, weight=5)
        main.add(right, weight=2)

        self._build_workspace(left)
        self._build_feedback_panel(right)

    def _sidebar_field(self, parent: ttk.Frame, label: str, var: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label, style="Sidebar.TLabel").grid(row=row, column=0, sticky="w", pady=(0, 4))
        entry = ttk.Entry(parent, textvariable=var, width=28)
        entry.grid(row=row + 1, column=0, sticky="ew", pady=(0, 10))

    def _build_workspace(self, left: ttk.Frame) -> None:
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Study Guide Workspace", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(left, text="Answer in complete sentences. Calculation questions can include formulas and final units.", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 12))

        canvas_holder = ttk.Frame(left, style="Card.TFrame")
        canvas_holder.grid(row=2, column=0, sticky="nsew")
        canvas_holder.rowconfigure(0, weight=1)
        canvas_holder.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_holder, highlightthickness=0, bg=self.CARD)
        scrollbar = ttk.Scrollbar(canvas_holder, orient="vertical", command=self.canvas.yview)
        self.questions_frame = ttk.Frame(self.canvas, style="Card.TFrame")
        self.questions_frame.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.questions_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.bind("<Configure>", self._resize_canvas_window)

        actions = ttk.Frame(left, style="Card.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="Grade Full Study Guide", style="Accent.TButton", command=self.grade_answers).pack(side=tk.LEFT)
        ttk.Button(actions, text="Show Answer Key", style="Secondary.TButton", command=self.show_answer_key).pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="Clear Workspace", style="Secondary.TButton", command=self.clear_workspace).pack(side=tk.LEFT)

    def _build_feedback_panel(self, right: ttk.Frame) -> None:
        right.rowconfigure(3, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Progress + Feedback", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(right, text="Your weak topics are saved locally and used to personalize the next guide.", style="Muted.TLabel", wraplength=330).grid(row=1, column=0, sticky="w", pady=(3, 10))

        self.progress_label = ttk.Label(right, text="", style="Body.TLabel", justify=tk.LEFT)
        self.progress_label.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self.feedback_box = scrolledtext.ScrolledText(
            right,
            wrap=tk.WORD,
            height=28,
            bg="#f8fafc",
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief=tk.FLAT,
            bd=1,
            padx=10,
            pady=10,
            font=self._font(0.0115, 9, 12),
        )
        self.feedback_box.grid(row=3, column=0, sticky="nsew")
        self.feedback_box.insert(tk.END, "Welcome. Click 'Generate Next Study Guide' to begin your adaptive Astronomy path.\n")
        self.feedback_box.configure(state=tk.DISABLED)

    def _resize_canvas_window(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _safe_student_id(self) -> str:
        return self.student_id_var.get().strip() or "default"

    def _append_feedback(self, text: str, replace: bool = False) -> None:
        self.feedback_box.configure(state=tk.NORMAL)
        if replace:
            self.feedback_box.delete("1.0", tk.END)
        self.feedback_box.insert(tk.END, text + "\n")
        self.feedback_box.see(tk.END)
        self.feedback_box.configure(state=tk.DISABLED)

    def _set_busy(self, busy: bool) -> None:
        self.configure(cursor="watch" if busy else "")
        self.update_idletasks()

    def generate_guide(self) -> None:
        student_id = self._safe_student_id()
        progress = self.tracker.load(student_id)
        if progress.completed_guides >= 10:
            messagebox.showinfo("All Guides Complete", "This student already completed all 10 adaptive study guides. Use a new Student ID to start again.")
            return

        topic = self.topic_var.get().strip() or "General Astronomy"
        self._append_feedback(f"Generating next guide for {student_id} on {topic}...", replace=True)
        self._set_busy(True)
        threading.Thread(target=self._generate_guide_worker, args=(student_id, topic), daemon=True).start()

    def _generate_guide_worker(self, student_id: str, topic: str) -> None:
        try:
            guide, used_ollama = self.manager.generate_guide(student_id=student_id, main_topic=topic, question_count=10)
            self.after(0, lambda: self._display_guide(guide, used_ollama))
        except Exception as exc:
            self.after(0, lambda: self._show_error("Guide Generation Error", exc))

    def _display_guide(self, guide: StudyGuide, used_ollama: bool) -> None:
        self._set_busy(False)
        self.current_guide = guide
        self.last_grade_result = None
        self.last_missed_items = []
        self.answer_boxes.clear()
        for child in self.questions_frame.winfo_children():
            child.destroy()

        title_frame = ttk.Frame(self.questions_frame, style="Card.TFrame")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        title_frame.columnconfigure(0, weight=1)
        tk.Label(title_frame, text=f"{guide.title}", bg=self.CARD, fg=self.TEXT, font=self._font(0.019, 15, 22, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(title_frame, text=f"Guide {guide.guide_number}/10  •  Topic: {guide.main_topic}", bg=self.CARD, fg=self.MUTED, font=self._font(0.0115, 9, 12)).grid(row=1, column=0, sticky="w", pady=(3, 0))
        focus = ", ".join(guide.adaptive_focus) if guide.adaptive_focus else "Balanced diagnostic guide"
        tk.Label(title_frame, text=f"Adaptive focus: {focus}", bg="#eff6ff", fg=self.BLUE_DARK, font=self._font(0.0115, 9, 12, "bold"), padx=10, pady=6).grid(row=2, column=0, sticky="w", pady=(8, 0))

        row = 1
        for question in guide.questions:
            box = ttk.LabelFrame(self.questions_frame, text=f"Question {question.id}: {question.type} | {question.topic}", style="Question.TLabelframe", padding=12)
            box.grid(row=row, column=0, sticky="ew", pady=(0, 12), padx=(0, 8))
            box.columnconfigure(0, weight=1)
            tk.Label(box, text=question.question, wraplength=780, justify=tk.LEFT, bg=self.CARD, fg=self.TEXT, font=self._font(0.0115, 9, 12)).grid(row=0, column=0, sticky="w")
            answer_box = tk.Text(
                box,
                height=4,
                wrap=tk.WORD,
                bg="#f8fafc",
                fg=self.TEXT,
                insertbackground=self.TEXT,
                relief=tk.SOLID,
                bd=1,
                padx=8,
                pady=8,
                font=self._font(0.0115, 9, 12),
            )
            answer_box.grid(row=1, column=0, sticky="ew", pady=(8, 0))
            self.answer_boxes[question.id] = answer_box
            ttk.Button(
                box,
                text="Check Answer",
                style="Primary.TButton",
                command=lambda q=question: self.check_single_answer(q),
            ).grid(row=2, column=0, sticky="w", pady=(8, 0))
            row += 1

        mode = "Ollama-generated" if used_ollama else "generation unavailable"
        self._append_feedback(f"Loaded {guide.title}.\nGeneration mode: {mode}.\n\nUse 'Check Answer' under a question for instant feedback, or grade the full guide when finished.", replace=True)
        self.refresh_progress()

    def _missed_items(self, result: Dict) -> list[Dict]:
        return [item for item in result.get("graded_questions", []) if float(item.get("score_out_of_10", 0)) < 7]

    def _fallback_reteach(self, item: Dict, confusion: str) -> str:
        return (
            f"Let's slow this down. You missed Question {item['id']} on {item['topic']}.\n\n"
            f"Question: {item['question']}\n\n"
            f"Your answer: {item.get('student_answer') or 'No answer entered'}\n\n"
            f"What confused you: {confusion}\n\n"
            f"Correct idea: {item['answer_key']}\n\n"
            "How to think about it:\n"
            "1. Identify the main astronomy concept being tested.\n"
            "2. Compare your answer to the answer key and look for the missing key words, formula, unit, or cause-and-effect relationship.\n"
            "3. Rewrite the answer in your own words using the correct concept.\n\n"
            f"Original grading feedback: {item['feedback']}"
        )

    def _build_reteach_prompt(self, item: Dict, confusion: str) -> str:
        return f"""
You are an encouraging college Astronomy tutor inside a GUI app.
The student got this question wrong and then explained what confused them.
Teach the concept based directly on their confusion.

Question ID: {item['id']}
Topic: {item['topic']}
Question: {item['question']}
Student answer: {item.get('student_answer') or 'No answer entered'}
Score: {item['score_out_of_10']}/10
Grader feedback: {item['feedback']}
Answer key: {item['answer_key']}
Student confusion: {confusion}

Write the response in this exact structure:
1. Start with a short friendly acknowledgement.
2. Explain the concept in simple language.
3. Show what was missing or incorrect in the student's answer.
4. Give a corrected answer the student could study.
5. End with one quick check-for-understanding question.
Keep it clear and not too long.
""".strip()

    def _build_evaluator_prompt(self, item: Dict, confusion: str, tutor_explanation: str) -> str:
        return f"""
You are the evaluator/reviewer model for an AI tutoring app.
Your job is to improve the tutor model's explanation before the student sees it.

Review goals:
- Keep the explanation accurate for college-level Astronomy.
- Make it clear, beginner-friendly, and directly connected to the student's confusion.
- Do not simply say whether the tutor was good; return the final improved teaching feedback.
- Keep the same structure and make the wording student-facing.

Question ID: {item['id']}
Topic: {item['topic']}
Question: {item['question']}
Student answer: {item.get('student_answer') or 'No answer entered'}
Score: {item['score_out_of_10']}/10
Grader feedback: {item['feedback']}
Answer key: {item['answer_key']}
Student confusion: {confusion}

Tutor model draft explanation:
{tutor_explanation}

Return only the final improved feedback that should appear in the GUI.
""".strip()

    def _save_reteach_feedback(self, result: Dict, item: Dict, confusion: str, explanation: str, reviewer_used: bool = False) -> None:
        attempt_path = result.get("attempt_path")
        if not attempt_path:
            return
        try:
            import json
            from pathlib import Path
            path = Path(attempt_path)
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else result
            data.setdefault("reteach_feedback", []).append({
                "question_id": item["id"],
                "topic": item["topic"],
                "student_confusion": confusion,
                "ollama_explanation": explanation,
                "reviewer_model_used": reviewer_used,
            })
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass


    def check_single_answer(self, question) -> None:
        """Check one answer. Correct answers show a quick message; wrong answers ask what confused the student before any AI teaching feedback appears."""
        if self.current_guide is None:
            messagebox.showwarning("No Guide", "Generate a study guide first.")
            return

        answer_widget = self.answer_boxes.get(question.id)
        student_answer = answer_widget.get("1.0", tk.END).strip() if answer_widget else ""
        score, feedback = self.manager._grade_one(question, student_answer)
        item = {
            "id": question.id,
            "topic": question.topic,
            "question": question.question,
            "student_answer": student_answer,
            "score_out_of_10": score,
            "feedback": feedback,
            "answer_key": question.answer,
        }

        if score >= 7:
            messagebox.showinfo("Correct Answer", f"You got Question {question.id} right!\n\nScore: {score}/10\n{feedback}")
            self._append_feedback(
                f"\nQuestion {question.id} checked: CORRECT ({score}/10)\n{feedback}",
                replace=False,
            )
            return

        confusion = simpledialog.askstring(
            "What confused you?",
            f"Question {question.id} needs more work.\n\nWhat confused you about this question?",
            parent=self,
        )
        if not confusion:
            messagebox.showinfo(
                "No Feedback Created",
                "Personalized teaching feedback will only appear after you explain what confused you.",
            )
            return

        self._set_busy(True)
        threading.Thread(target=self._reteach_worker, args=(item, confusion), daemon=True).start()

    def ask_for_confusion_feedback(self) -> None:
        if not self.last_grade_result:
            messagebox.showwarning("No Graded Attempt", "Grade your answers first.")
            return

        missed = self._missed_items(self.last_grade_result)
        if not missed:
            messagebox.showinfo("No Missed Questions", "Personalized teaching feedback is only shown when a checked or graded answer is wrong.")
            return

        options = "\n".join(f"{item['id']}. {item['topic']} — {item['score_out_of_10']}/10" for item in missed)
        question_id_text = simpledialog.askstring(
            "Choose a missed question",
            "Which missed question do you want help with?\n\n" + options + "\n\nEnter the question number:",
            parent=self,
        )
        if not question_id_text:
            return
        try:
            question_id = int(question_id_text.strip())
        except ValueError:
            messagebox.showerror("Invalid Question", "Please enter the question number, like 1 or 2.")
            return

        item = next((x for x in missed if int(x["id"]) == question_id), None)
        if item is None:
            messagebox.showerror("Question Not Found", "That question was not one of the missed questions.")
            return

        confusion = simpledialog.askstring(
            "What confused you?",
            "Tell the tutor what confused you about this question.\n\nExample: I do not understand which formula to use.",
            parent=self,
        )
        if not confusion:
            return

        self._set_busy(True)
        threading.Thread(target=self._reteach_worker, args=(item, confusion), daemon=True).start()

    def _reteach_worker(self, item: Dict, confusion: str) -> None:
        prompt = self._build_reteach_prompt(item, confusion)
        tutor_result = self.ollama.generate(prompt=prompt, system="You are a patient Astronomy tutor.", temperature=0.25)
        tutor_explanation = tutor_result.text if tutor_result.used_ollama and tutor_result.text else self._fallback_reteach(item, confusion)

        reviewer_used = False
        final_explanation = tutor_explanation
        reviewer_prompt = self._build_evaluator_prompt(item, confusion, tutor_explanation)
        reviewer_result = self.evaluator_ollama.generate(
            prompt=reviewer_prompt,
            system="You are a careful Astronomy teaching-feedback reviewer.",
            temperature=0.15,
        )
        if reviewer_result.used_ollama and reviewer_result.text:
            final_explanation = reviewer_result.text
            reviewer_used = True

        self.after(0, lambda: self._display_reteach_feedback(item, confusion, final_explanation, tutor_result.used_ollama, reviewer_used))

    def _display_reteach_feedback(self, item: Dict, confusion: str, explanation: str, used_ollama: bool, reviewer_used: bool = False) -> None:
        self._set_busy(False)
        if used_ollama and reviewer_used:
            source = f"Ollama tutor model + evaluator/reviewer model ({self.evaluator_ollama.model})"
        elif used_ollama:
            source = "Ollama tutor model explanation; reviewer unavailable, so tutor draft was shown"
        else:
            source = "Local fallback explanation"
        self._append_feedback(
            "\n" + "=" * 50 +
            f"\nRETEACHING FEEDBACK — Question {item['id']} ({item['topic']})\n" +
            f"Source: {source}\n\n" +
            explanation +
            "\n" + "=" * 50
        )
        if self.last_grade_result:
            self._save_reteach_feedback(self.last_grade_result, item, confusion, explanation, reviewer_used)

    def grade_answers(self) -> None:
        if self.current_guide is None:
            messagebox.showwarning("No Guide", "Generate a study guide first.")
            return

        answers: Dict[int, str] = {}
        for question_id, widget in self.answer_boxes.items():
            answers[question_id] = widget.get("1.0", tk.END).strip()

        result = self.manager.grade_answers(self.current_guide, answers)
        self.last_grade_result = result
        self.last_missed_items = self._missed_items(result)

        completed_guides = int(result.get("progress", {}).get("completed_guides", 0))
        answer_key_unlocked = completed_guides >= 10

        lines = [
            f"RESULTS FOR {self.current_guide.title}",
            f"Score: {result['score_percent']}%",
            f"Missed topics: {', '.join(result['missed_topics']) if result['missed_topics'] else 'None'}",
            f"Next step: {result['next_step']}",
            "",
            "Question Feedback:",
        ]
        for item in result["graded_questions"]:
            lines.extend([
                "",
                f"{item['id']}. {item['topic']} - {item['score_out_of_10']}/10",
                f"Feedback: {item['feedback']}",
            ])
            if answer_key_unlocked:
                lines.append(f"Answer key: {item['answer_key']}")
            else:
                lines.append("Answer key: Locked until all 10 study guides are completed.")

        if self.last_missed_items:
            lines.extend([
                "",
                "Some questions were missed.",
                "Use the 'Check Answer' button under a missed question and explain what confused you. Ollama will reteach it here in the GUI.",
            ])
        else:
            lines.extend([
                "",
                "All checked concepts look strong. Personalized AI feedback only appears when a checked answer is wrong.",
            ])

        if answer_key_unlocked:
            lines.extend([
                "",
                "Answer key access is unlocked because all 10 study guides are complete.",
            ])
        else:
            lines.extend([
                "",
                f"Answer key access is locked. Completed guides: {completed_guides}/10.",
            ])

        lines.extend([
            "",
            "Saved locally:",
            f"- {result['attempt_path']}",
            "- data/progress/" + self._safe_student_id() + ".json",
        ])
        self._append_feedback("\n".join(lines), replace=True)
        self.refresh_progress()
        messagebox.showinfo("Grading Complete", f"Score: {result['score_percent']}%\nThe next guide will adapt to missed topics.")

    def show_answer_key(self) -> None:
        student_id = self._safe_student_id()
        progress = self.tracker.load(student_id)
        if progress.completed_guides < 10:
            messagebox.showwarning(
                "Answer Key Locked",
                f"The answer key unlocks after all 10 study guides are completed.\n\nCurrent progress: {progress.completed_guides}/10",
            )
            self._append_feedback(
                f"Answer key locked. Complete all 10 study guides first. Current progress: {progress.completed_guides}/10.",
                replace=False,
            )
            return

        if self.current_guide is None:
            messagebox.showwarning("No Guide", "Generate or load a study guide first.")
            return
        self._append_feedback(self.manager.render_answer_key(self.current_guide), replace=True)

    def clear_workspace(self) -> None:
        self.current_guide = None
        self.last_grade_result = None
        self.last_missed_items = []
        self.answer_boxes.clear()
        for child in self.questions_frame.winfo_children():
            child.destroy()
        self._append_feedback("Workspace cleared. Generate a new guide to continue.", replace=True)

    def refresh_progress(self) -> None:
        student_id = self._safe_student_id()
        progress = self.tracker.load(student_id)
        weak = sorted(progress.weak_topics.items(), key=lambda item: item[1], reverse=True)
        strengths = sorted(progress.strengths.items(), key=lambda item: item[1], reverse=True)[:5]

        weak_text = "None yet" if not weak else "\n".join(f"• {topic}: missed {count} time(s)" for topic, count in weak[:8])
        strengths_text = "None yet" if not strengths else "\n".join(f"• {topic}: strong {count} time(s)" for topic, count in strengths)
        self.progress_label.configure(
            text=(
                f"Student: {student_id}\n"
                f"Completed guides: {progress.completed_guides}/10\n\n"
                f"Weak topics:\n{weak_text}\n\n"
                f"Strengths:\n{strengths_text}"
            )
        )
        self.status_var.set(self._ollama_status_text())

    def _show_error(self, title: str, exc: Exception) -> None:
        self._set_busy(False)
        messagebox.showerror(title, str(exc))
        self._append_feedback(f"{title}: {exc}")


def main() -> None:
    app = AstronomyTutorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
