from __future__ import annotations

from typing import Dict, List

from src.plugins.base import SubjectPlugin
from src.plugins.astronomy.plugin import AstronomyPlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, SubjectPlugin] = {}

    def register(self, plugin: SubjectPlugin) -> None:
        self._plugins[plugin.subject] = plugin

    def get(self, subject: str) -> SubjectPlugin | None:
        return self._plugins.get(subject.lower())

    def all(self) -> List[SubjectPlugin]:
        return list(self._plugins.values())

    def subjects(self) -> List[str]:
        return sorted(self._plugins.keys())


def build_default_registry() -> PluginRegistry:
    registry = PluginRegistry()
    registry.register(AstronomyPlugin())
    return registry
