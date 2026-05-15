"""
Orchestrator
============

Koordiniert den Ablauf der Venture-Pipeline.
Weist Aufgaben an Researcher und Coder zu und überwacht den Fortschritt.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


class PipelineStage(Enum):
    """Phasen der Venture-Pipeline."""
    IDEATION = "ideation"
    RESEARCH = "research"
    VALIDATION = "validation"
    DECISION = "decision"
    DEVELOPMENT = "development"
    LAUNCH = "launch"
    MONITORING = "monitoring"


@dataclass
class Venture:
    """Repräsentiert eine Micro-SaaS-Idee im Pipeline-Durchlauf."""
    id: str
    name: str
    description: str
    stage: PipelineStage = PipelineStage.IDEATION
    score: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class Orchestrator:
    """
    Zentrale Steuerungsklasse.

    Verantwortlich für:
    - Pipeline-Management
    - Agentenkoordination
    - Entscheidungslogik
    """

    def __init__(self):
        self.ventures: list[Venture] = []
        self.active_venture: Optional[Venture] = None

    def add_venture(self, venture: Venture) -> None:
        """Fügt eine neue Venture-Idee zur Pipeline hinzu."""
        self.ventures.append(venture)

    def prioritize(self) -> list[Venture]:
        """Sortiert Ventures nach Score (absteigend)."""
        return sorted(
            self.ventures,
            key=lambda v: v.score or 0,
            reverse=True,
        )

    def advance_stage(self, venture: Venture) -> Venture:
        """Bewegt ein Venture in die nächste Pipeline-Phase."""
        stages = list(PipelineStage)
        current_index = stages.index(venture.stage)
        if current_index < len(stages) - 1:
            venture.stage = stages[current_index + 1]
            venture.updated_at = datetime.utcnow().isoformat()
        return venture

    def decide(self, venture: Venture, threshold: float = 0.6) -> bool:
        """
        Go/No-Go-Entscheidung basierend auf dem Validierungs-Score.

        Returns:
            True = Go, False = No-Go
        """
        if venture.score is None:
            return False
        return venture.score >= threshold
