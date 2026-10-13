from __future__ import annotations

from importlib import import_module
from contractive_tool.errors import AnalysisError


class StrategyRegistry:
    known = ("putinar", "schmudgen", "handelman")

    def __init__(self, enabled=None):
        self.enabled = tuple(self.known if enabled is None else enabled)
        if set(self.enabled) - set(self.known):
            raise AnalysisError("Unknown strategy ID")
        self.instances = {}
        self.diagnostics = {}

    def get(self, name):
        if name not in self.known:
            raise AnalysisError(f"Unknown strategy '{name}'")
        if name not in self.enabled:
            self.diagnostics[name] = "disabled"
            return None
        if name not in self.instances:
            try:
                module = import_module(f"contractive_tool.positivity.{name}")
                cls = getattr(module, {"putinar": "PutinarStrategy", "schmudgen": "SchmudgenStrategy",
                                       "handelman": "HandelmanStrategy"}[name])
                self.instances[name] = cls()
            except (ImportError, AttributeError) as error:
                self.diagnostics[name] = f"not_available: {type(error).__name__}"
                return None
        return self.instances[name]

    def snapshot(self):
        return [{"id": name, "available": self.get(name) is not None,
                 "reason": self.diagnostics.get(name)} for name in self.known]
