from __future__ import annotations

from src.core.types import TutorAction, TutorRequest, TutorResponse
from src.plugins.base import SubjectPlugin
from src.services.assessment import contains_any
from src.services.ollama_client import OllamaClient, format_history


ASTRONOMY_SYSTEM_PROMPT = """
You are a college-level Astronomy tutor for undergraduate students.
Teach only Astronomy and closely related physics when needed.
Use a supportive Socratic tutoring style: explain clearly, ask one check-for-understanding question, and avoid doing every step for the student unless grading.
Use correct vocabulary and equations when helpful, such as Kepler's laws, inverse-square law, Wien's law, Stefan-Boltzmann law, Doppler/redshift, parallax, luminosity, magnitude, and Hubble's law.
When generating practice, provide the problem, learning objective, and expected answer or rubric.
When grading, give a score out of 10, what is correct, what is missing, and one next step.
Keep answers focused and readable for a college class.
""".strip()


class AstronomyPlugin(SubjectPlugin):
    subject = "astronomy"
    keywords = [
        "astronomy", "planet", "star", "galaxy", "moon", "sun", "orbit",
        "gravity", "telescope", "redshift", "light-year", "nebula", "kepler",
        "hr diagram", "h-r diagram", "black hole", "supernova", "cosmos",
        "parallax", "parsec", "luminosity", "magnitude", "spectroscopy", "exoplanet",
        "hubble", "cosmology", "stellar", "radiation", "wavelength", "doppler",
    ]

    def __init__(self, ollama: OllamaClient | None = None) -> None:
        self.ollama = ollama or OllamaClient()

    def _llm_response(self, request: TutorRequest, task_instruction: str, temperature: float = 0.35) -> TutorResponse | None:
        context = request.context
        level = context.level if context else "college"
        history = format_history(context.history if context else [])
        prompt = f"""
Student level: {level}
Recent student history:
{history}

Tutoring task: {task_instruction}
Student topic/question: {request.message}
Student answer, if grading: {request.answer or 'N/A'}

Respond as the Astronomy tutor. Do not mention that you are using Ollama.
""".strip()
        result = self.ollama.generate(prompt=prompt, system=ASTRONOMY_SYSTEM_PROMPT, temperature=temperature)
        if result.used_ollama and result.text:
            return TutorResponse(
                message=result.text,
                subject=self.subject,
                action=request.action,
                confidence=0.9,
                metadata={"used_ollama": True, "ollama_model": result.model},
            )
        return None

    def explain(self, request: TutorRequest) -> TutorResponse:
        llm = self._llm_response(
            request,
            "Explain the concept at a college level. Include key vocabulary, one useful equation or relationship if relevant, an example, and one check-for-understanding question.",
        )
        if llm:
            return llm

        text = request.message.lower()
        if "redshift" in text:
            message = (
                "Redshift is the increase in wavelength of light from an astronomical object. At a college level, "
                "you should connect it to the Doppler effect and cosmic expansion. If a galaxy's spectral lines are "
                "shifted toward longer wavelengths, astronomers infer it is moving away from us. A common relation is "
                "z = (observed wavelength - rest wavelength) / rest wavelength. Check yourself: if wavelength increases, "
                "does frequency increase or decrease?"
            )
        elif "kepler" in text or "orbit" in text:
            message = (
                "Kepler's laws describe orbital motion: planets move in ellipses, sweep out equal areas in equal times, "
                "and follow P^2 = a^3 when P is in years and a is in astronomical units for objects orbiting the Sun. "
                "The college-level connection is that Newton's gravity explains why these patterns occur. Check yourself: "
                "where in an elliptical orbit does a planet move fastest?"
            )
        elif "parallax" in text:
            message = (
                "Stellar parallax is the apparent shift of a nearby star against distant background stars as Earth orbits "
                "the Sun. The distance relation is d = 1/p, where d is in parsecs and p is the parallax angle in arcseconds. "
                "This is a geometric distance method and forms the base of the cosmic distance ladder."
            )
        elif "hr" in text or "h-r" in text or "star" in text:
            message = (
                "The H-R diagram plots stellar luminosity against surface temperature. It reveals major stellar groups: "
                "main sequence stars, giants, supergiants, and white dwarfs. College-level use includes estimating stellar "
                "evolution stage from temperature and luminosity."
            )
        else:
            message = (
                "Astronomy studies planets, stars, galaxies, and the universe using evidence from light, gravity, and motion. "
                "A college-level answer should connect observations to physical laws, such as spectroscopy for composition, "
                "parallax for distance, and gravity for orbital motion."
            )
        return TutorResponse(message=message, subject=self.subject, action=TutorAction.EXPLAIN, metadata={"used_ollama": False})

    def hint(self, request: TutorRequest) -> TutorResponse:
        llm = self._llm_response(
            request,
            "Give a helpful hint without fully solving the problem. Ask one guiding question that moves the student forward.",
            temperature=0.25,
        )
        if llm:
            return llm

        text = request.message.lower()
        if "redshift" in text:
            message = "Hint: start with wavelength. Compare the observed wavelength to the rest wavelength using z = Δλ / λ_rest."
        elif "orbit" in text or "kepler" in text:
            message = "Hint: identify whether the problem is asking about orbit shape, orbital speed, or period-distance relation."
        elif "parallax" in text:
            message = "Hint: for parallax, use d = 1/p. Make sure p is measured in arcseconds, not degrees."
        else:
            message = "Hint: identify the observation first: light, motion, brightness, color, distance, or gravity."
        return TutorResponse(message=message, subject=self.subject, action=TutorAction.HINT, metadata={"used_ollama": False})

    def generate_practice(self, request: TutorRequest) -> TutorResponse:
        llm = self._llm_response(
            request,
            "Generate one college-level Astronomy practice question on the requested topic. Include learning objective, problem, and a hidden-style expected answer/rubric clearly labeled for the tutor.",
            temperature=0.55,
        )
        if llm:
            return llm

        message = (
            "Ollama is required to generate a new practice question. "
            "Start Ollama and try again. This project does not use a pre-written practice question bank."
        )
        return TutorResponse(
            message=message,
            subject=self.subject,
            action=TutorAction.PRACTICE,
            confidence=0.0,
            metadata={"used_ollama": False, "generation_required": True},
        )

    def grade(self, request: TutorRequest) -> TutorResponse:
        llm = self._llm_response(
            request,
            "Grade the student's answer to this Astronomy question. Give a score out of 10, identify correct ideas, missing ideas, and one next step.",
            temperature=0.2,
        )
        if llm:
            return llm

        answer = request.answer or request.message
        text = request.message.lower()
        if "redshift" in text:
            expected = ["0.05", "moving away", "longer wavelength", "redshift"]
        elif "parallax" in text:
            expected = ["5", "parsec", "d = 1/p"]
        elif "kepler" in text or "orbit" in text:
            expected = ["8", "years", "p^2", "a^3"]
        elif "hr" in text or "h-r" in text:
            expected = ["brightness", "temperature", "luminosity"]
        else:
            expected = ["star", "planet", "galaxy", "light", "gravity", "orbit", "universe"]

        if contains_any(answer, expected):
            message = "Score: 8/10. Correct or mostly correct. Your answer includes at least one key astronomy idea. To improve, add the relevant equation, units, or observational evidence."
            confidence = 0.8
        else:
            message = (
                "Score: 4/10. Not quite yet. Your answer is missing the main astronomy vocabulary or calculation. "
                f"Key terms I was looking for include: {', '.join(expected[:3])}."
            )
            confidence = 0.55
        return TutorResponse(message=message, subject=self.subject, action=TutorAction.GRADE, confidence=confidence, metadata={"used_ollama": False})
