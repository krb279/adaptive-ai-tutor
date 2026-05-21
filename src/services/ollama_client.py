from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class OllamaResult:
    text: str
    used_ollama: bool
    model: str
    error: str | None = None


class OllamaClient:
    """Small local Ollama client using Python standard library only."""

    def __init__(self, model: str | None = None, host: str | None = None, timeout: int = 15) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.enabled = os.getenv("USE_OLLAMA", "1").lower() not in {"0", "false", "no", "off"}
        self.timeout = timeout

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, system: str | None = None, temperature: float = 0.35) -> OllamaResult:
        if not self.enabled:
            return OllamaResult("", False, self.model, "Ollama disabled with USE_OLLAMA=0")

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                return OllamaResult(
                    text=str(data.get("response", "")).strip(),
                    used_ollama=True,
                    model=self.model,
                )
        except urllib.error.HTTPError as exc:
            return OllamaResult("", False, self.model, f"HTTP error from Ollama: {exc.code}")
        except urllib.error.URLError as exc:
            return OllamaResult("", False, self.model, f"Could not connect to Ollama: {exc.reason}")
        except Exception as exc:
            return OllamaResult("", False, self.model, f"Ollama error: {exc}")


def format_history(history: List[Dict[str, Any]], limit: int = 4) -> str:
    recent = history[-limit:]
    if not recent:
        return "No previous tutoring history yet."
    lines = []
    for item in recent:
        lines.append(
            f"- Action: {item.get('action')} | Student asked: {item.get('message')} | Tutor replied: {str(item.get('response'))[:220]}"
        )
    return "\n".join(lines)
