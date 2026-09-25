from dataclasses import dataclass
import importlib.util

from app.models.adapters import timer_status, timeradar_status


@dataclass
class ModelStatus:
    name: str
    kind: str
    available: bool
    detail: str


class Registry:
    def __init__(self):
        self.items: list[ModelStatus] = []

    def initialize(self):
        radar = timeradar_status()
        timer = timer_status()
        self.items = [
            ModelStatus("TimeRadar", "zero_shot_anomaly", radar["available"], f"Checkpoint: {radar['checkpoint']}"),
            ModelStatus("Chronos-2", "forecast", bool(importlib.util.find_spec("torch") and importlib.util.find_spec("chronos")), "Optional Chronos-2 adapter"),
            ModelStatus("Timer", "forecast", timer["available"], f"Model: {timer['model_id']}"),
            ModelStatus("Random Forest baseline", "baseline", bool(importlib.util.find_spec("sklearn")), "Lightweight local baseline"),
            ModelStatus("Online anomaly", "online", True, "Signal statistics adapter"),
        ]

    def status(self):
        return [x.__dict__ for x in self.items]


registry = Registry()
