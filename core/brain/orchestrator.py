"""
Orchestrator
============

Koordiniert den Ablauf der Venture-Pipeline.
Weist Aufgaben an Researcher und Coder zu und überwacht den Fortschritt.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


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
    lead_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class DiscoveryError(Exception):
    """Wird geworfen, wenn die Discovery-Phase fehlschlägt."""
    pass


class Orchestrator:
    """
    Zentrale Steuerungsklasse.

    Verantwortlich für:
    - Pipeline-Management
    - Agentenkoordination
    - Entscheidungslogik
    """

    # Go/No-Go-Schwellenwert
    DEFAULT_THRESHOLD = 0.6

    def __init__(self):
        self.ventures: list[Venture] = []
        self.active_venture: Optional[Venture] = None

    # ------------------------------------------------------------------
    # Phase 1: Discovery
    # ------------------------------------------------------------------
    def run_discovery_phase(self, threshold: float | None = None) -> Path:
        """
        Führt die autonome Discovery-Phase durch.

        Ablauf:
            1. MemoryStore instanziieren
            2. MarketAnalyzer mit MemoryStore erstellen
            3. fetch_trending_niches() aufrufen
            4. Top-Lead identifizieren (höchster Score)
            5. Go/No-Go-Entscheidung treffen
            6. Bei Go: Venture erstellen, in Pipeline aufnehmen, Pfad zurückgeben
            7. Bei No-Go: DiscoveryError werfen

        Args:
            threshold: Score-Schwellenwert für Go-Entscheidung.
                       Standard: 0.6

        Returns:
            Path zum Top-Lead im Memory-Store (für den Coder-Agent).

        Raises:
            DiscoveryError: Wenn keine Leads gefunden wurden oder
                            kein Lead den Schwellenwert erreicht.
        """
        threshold = threshold if threshold is not None else self.DEFAULT_THRESHOLD

        logger.info("=" * 60)
        logger.info("DISCOVERY PHASE gestartet (Threshold: %.2f)", threshold)
        logger.info("=" * 60)

        # --- 1. MemoryStore instanziieren ---
        from shared.memory.store import MemoryStore
        memory = MemoryStore()
        logger.info("MemoryStore initialisiert: %s", memory.base_dir)

        # --- 2. MarketAnalyzer instanziieren ---
        from agents.researcher.analyzer import MarketAnalyzer
        researcher = MarketAnalyzer(memory_store=memory)
        logger.info("MarketAnalyzer instanziiert (mit MemoryStore).")

        # --- 3. Trending-Nischen abrufen ---
        try:
            reports = researcher.fetch_trending_niches(
                auto_score=True,
                persist=True,
            )
        except Exception as exc:
            logger.error("Discovery fehlgeschlagen: %s", exc)
            raise DiscoveryError(
                f"Trending-Nischen konnten nicht abgerufen werden: {exc}"
            ) from exc

        if not reports:
            logger.warning("Keine Leads aus der Discovery-Phase.")
            raise DiscoveryError("Keine Leads gefunden – Pipeline gestoppt.")

        # --- 4. Top-Lead identifizieren ---
        # Reports sind bereits nach Score sortiert (absteigend)
        top_lead = reports[0]

        logger.info(
            "Top-Lead identifiziert: '%s' (Score: %.4f)",
            top_lead.niche_name,
            top_lead.validation_score or 0.0,
        )

        # --- 5. Go/No-Go-Entscheidung ---
        top_score = top_lead.validation_score or 0.0

        if top_score < threshold:
            logger.warning(
                "NO-GO: '%s' (Score: %.4f) liegt unter Threshold (%.2f). "
                "Keine Nische qualifiziert sich.",
                top_lead.niche_name,
                top_score,
                threshold,
            )
            raise DiscoveryError(
                f"Kein Lead erreicht den Schwellenwert ({threshold}). "
                f"Bester Lead: '{top_lead.niche_name}' mit Score {top_score:.4f}"
            )

        # --- 6. Venture erstellen und in Pipeline aufnehmen ---
        lead_path = memory.base_dir / "leads" / f"{top_lead.idea_id}.json"

        venture = Venture(
            id=top_lead.idea_id,
            name=top_lead.niche_name,
            description=top_lead.notes,
            stage=PipelineStage.IDEATION,
            score=top_score,
            lead_path=str(lead_path),
            metadata={
                "market_size": top_lead.market_size_estimate,
                "competitors": top_lead.competitor_count,
                "differentiation": top_lead.differentiation_potential,
                "target_audience": top_lead.target_audience,
                "pricing": top_lead.pricing_suggestion,
                "source": top_lead.source,
            },
        )

        self.add_venture(venture)

        # Durch Pipeline-Phasen bewegen: IDEATION → RESEARCH → VALIDATION → DECISION → DEVELOPMENT
        for _ in range(4):
            self.advance_stage(venture)

        self.active_venture = venture

        # --- 7. Qualifikations-Log ---
        logger.info("-" * 60)
        logger.info(
            "🚀 Venture '%s' qualifiziert für Phase 2 (Building) | Score: %.4f",
            venture.name,
            venture.score,
        )
        logger.info("   Lead-Pfad: %s", lead_path)
        logger.info("   Pipeline-Stage: %s", venture.stage.value)
        logger.info("   Zielgruppe: %s", venture.metadata.get("target_audience", ""))
        logger.info("   Preismodell: %s", venture.metadata.get("pricing", ""))
        logger.info("-" * 60)

        return lead_path

    # ------------------------------------------------------------------
    # Pipeline-Management
    # ------------------------------------------------------------------
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
