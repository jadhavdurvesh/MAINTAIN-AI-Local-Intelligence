from dataclasses import dataclass
import importlib.util

@dataclass
class ModelStatus:
    name: str
    kind: str
    available: bool
    detail: str

class Registry:
    def __init__(self):
        self.items = []

    def initialize(self):
        self.items = [
            ModelStatus("TimeRadar", "zero_shot_anomaly", bool(importlib.util.find_spec("torch") and importlib.util.find_spec("transformers")), "Optional TimeRadar adapter"),
            ModelStatus("Chronos-2", "forecast", bool(importlib.util.find_spec("torch") and importlib.util.find_spec("chronos")), "Optional Chronos-2 adapter"),
            ModelStatus("Timer", "forecast", bool(importlib.util.find_spec("torch") and importlib.util.find_spec("transformers")), "Optional Timer adapter"),
            ModelStatus("Random Forest baseline", "baseline", bool(importlib.util.find_spec("sklearn")), "Lightweight local baseline"),
            ModelStatus("Online anomaly", "online", True, "Signal statistics adapter"),
        ]

    def status(self):
        return [x.__dict__ for x in self.items]

registry = Registry()
