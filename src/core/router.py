from __future__ import annotations

from src.core.types import TutorRequest
from src.plugins.base import SubjectPlugin
from src.plugins.registry import PluginRegistry


class Router:
    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry

    def route(self, request: TutorRequest) -> SubjectPlugin:
        if request.subject:
            plugin = self.registry.get(request.subject.lower())
            if plugin:
                return plugin

        for plugin in self.registry.all():
            if plugin.can_handle(request):
                return plugin

        default_plugin = self.registry.get("astronomy")
        if default_plugin is None:
            raise RuntimeError("No Astronomy plugin registered.")
        return default_plugin
