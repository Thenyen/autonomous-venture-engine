"""
Market Analyzer
===============

Führt Marktanalysen durch und bewertet Micro-SaaS-Nischen.
Bezieht Trending-Nischen aus externen Quellen (simuliert/API/Scraper)
und bewertet sie nach dem 40/30/30-Scoring-Modell.
"""

import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scoring-Gewichte (aus manifest.json: 40/30/30-Modell)
# ---------------------------------------------------------------------------
WEIGHT_DIFFERENTIATION = 0.40  # Differenzierungspotenzial
WEIGHT_MARKET_SIZE = 0.30      # Marktgröße
WEIGHT_COMPETITION = 0.30      # Wettbewerbsintensität (invertiert)

# Maximal angenommene Wettbewerber für die Normierung
MAX_COMPETITORS_BASELINE = 20


# ---------------------------------------------------------------------------
# Datenmodelle
# ---------------------------------------------------------------------------
@dataclass
class TrendingNiche:
    """Eine vom Researcher entdeckte Trending-Nische (Rohdaten)."""
    name: str
    description: str
    source: str  # z.B. "simulated_api", "product_hunt", "reddit_scraper"
    estimated_market_size: str = ""          # z.B. "$5M-$20M ARR"
    market_size_score: float = 0.0           # normiert 0.0 - 1.0
    estimated_competitors: int = 0
    competitor_names: list[str] = field(default_factory=list)
    differentiation_potential: float = 0.0   # 0.0 - 1.0
    target_audience: str = ""
    pricing_suggestion: str = ""
    tags: list[str] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class MarketReport:
    """Ergebnis einer Marktanalyse."""
    idea_id: str
    niche_name: str = ""
    market_size_estimate: Optional[str] = None
    market_size_score: float = 0.0           # normiert 0.0 - 1.0
    competitor_count: int = 0
    competitors: list[dict] = field(default_factory=list)
    target_audience: str = ""
    differentiation_potential: Optional[float] = None  # 0.0 - 1.0
    pricing_suggestion: Optional[str] = None
    validation_score: Optional[float] = None  # 0.0 - 1.0
    source: str = ""
    notes: str = ""
    scored_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Simulierte Datenquelle
# ---------------------------------------------------------------------------
class SimulatedTrendAPI:
    """
    Simulierte externe API für Trending-Nischen.

    Liefert realistische Micro-SaaS-Nischen als Testdaten.
    Wird später durch echte API-Calls / Web-Scraper ersetzt.
    """

    @staticmethod
    def fetch() -> list[TrendingNiche]:
        """Gibt eine Liste simulierter Trending-Nischen zurück."""
        return [
            TrendingNiche(
                name="AI Meeting Summarizer",
                description="Automatische Zusammenfassung von Online-Meetings mit Action-Items und Follow-up-Erkennung.",
                source="simulated_api",
                estimated_market_size="$10M-$50M ARR",
                market_size_score=0.75,
                estimated_competitors=8,
                competitor_names=["Otter.ai", "Fireflies.ai", "Fathom"],
                differentiation_potential=0.55,
                target_audience="Remote-Teams, Consultants, Projektmanager",
                pricing_suggestion="$12-$25/User/Monat",
                tags=["ai", "productivity", "meetings", "saas"],
            ),
            TrendingNiche(
                name="Micro-SaaS Invoice Tracker für Freelancer",
                description="Minimalistische Rechnungsverfolgung speziell für Solo-Freelancer mit automatischer Mahnfunktion.",
                source="simulated_api",
                estimated_market_size="$5M-$15M ARR",
                market_size_score=0.50,
                estimated_competitors=15,
                competitor_names=["FreshBooks", "Wave", "Zoho Invoice", "Bonsai"],
                differentiation_potential=0.35,
                target_audience="Freelancer, Solo-Unternehmer",
                pricing_suggestion="$5-$9/Monat",
                tags=["fintech", "freelancer", "invoicing", "micro-saas"],
            ),
            TrendingNiche(
                name="Niche Community Platform Builder",
                description="No-Code-Tool zum Aufbau themenspezifischer Micro-Communities mit eingebautem Paywall.",
                source="simulated_api",
                estimated_market_size="$20M-$80M ARR",
                market_size_score=0.85,
                estimated_competitors=5,
                competitor_names=["Circle.so", "Mighty Networks"],
                differentiation_potential=0.70,
                target_audience="Creator, Coaches, Nischen-Experten",
                pricing_suggestion="$19-$49/Monat",
                tags=["community", "no-code", "creator-economy", "saas"],
            ),
            TrendingNiche(
                name="Developer Changelog as a Service",
                description="Gehosteter Changelog mit Release-Notes, Feature-Voting und automatischer Notification-Pipeline.",
                source="simulated_api",
                estimated_market_size="$2M-$8M ARR",
                market_size_score=0.35,
                estimated_competitors=3,
                competitor_names=["Beamer", "LaunchNotes"],
                differentiation_potential=0.80,
                target_audience="SaaS-Startups, Dev-Teams, Open-Source-Projekte",
                pricing_suggestion="$15-$29/Monat",
                tags=["devtools", "changelog", "developer", "micro-saas"],
            ),
            TrendingNiche(
                name="AI-Powered Customer Feedback Triage",
                description="Automatische Kategorisierung und Priorisierung von Kunden-Feedback aus verschiedenen Kanälen.",
                source="simulated_api",
                estimated_market_size="$15M-$40M ARR",
                market_size_score=0.70,
                estimated_competitors=6,
                competitor_names=["Canny", "Productboard", "UserVoice"],
                differentiation_potential=0.65,
                target_audience="Product-Teams, Customer Success, SaaS-Unternehmen",
                pricing_suggestion="$29-$79/Monat",
                tags=["ai", "customer-feedback", "product-management", "saas"],
            ),
        ]


# ---------------------------------------------------------------------------
# Error-Typen
# ---------------------------------------------------------------------------
class MemoryPersistenceError(Exception):
    """Wird geworfen, wenn der Memory-Store nicht erreichbar ist."""
    pass


class TrendFetchError(Exception):
    """Wird geworfen, wenn Trending-Nischen nicht abgerufen werden können."""
    pass


# ---------------------------------------------------------------------------
# Market Analyzer
# ---------------------------------------------------------------------------
class MarketAnalyzer:
    """
    Marktanalyse-Engine.

    Analysiert Nischen, bewertet Wettbewerb und generiert
    Validierungs-Scores für Micro-SaaS-Ideen.

    Scoring-Modell (40/30/30):
        - 40% Differenzierungspotenzial
        - 30% Marktgröße
        - 30% Wettbewerbsintensität (invertiert: weniger = besser)
    """

    def __init__(self, memory_store=None):
        """
        Args:
            memory_store: Optional – MemoryStore-Instanz für persistente
                          Speicherung. Wenn None, werden Ergebnisse nur
                          lokal in self.reports gehalten.
        """
        self.reports: list[MarketReport] = []
        self._memory = memory_store
        self._trend_source = SimulatedTrendAPI()

    # ------------------------------------------------------------------
    # Trend-Fetching
    # ------------------------------------------------------------------
    def fetch_trending_niches(
        self,
        auto_score: bool = True,
        persist: bool = True,
    ) -> list[MarketReport]:
        """
        Bezieht Trending-Nischen und erstellt bewertete MarketReports.

        1. Nischen von der Datenquelle abrufen (simulierte API / Scraper)
        2. Jede Nische nach dem 40/30/30-Modell bewerten
        3. MarketReport-Objekte erstellen
        4. Optional im shared/memory unter Kategorie 'leads' speichern

        Args:
            auto_score: Wenn True, wird jede Nische sofort bewertet.
            persist: Wenn True, werden Reports im Memory-Store gespeichert.

        Returns:
            Liste der erstellten MarketReport-Objekte, sortiert nach Score.

        Raises:
            TrendFetchError: Wenn die Datenquelle nicht erreichbar ist.
        """
        # --- 1. Nischen abrufen ---
        try:
            niches = self._trend_source.fetch()
        except Exception as exc:
            logger.error("Fehler beim Abrufen der Trending-Nischen: %s", exc)
            raise TrendFetchError(
                f"Trending-Nischen konnten nicht abgerufen werden: {exc}"
            ) from exc

        if not niches:
            logger.warning("Keine Trending-Nischen gefunden.")
            return []

        logger.info("%d Trending-Nischen abgerufen.", len(niches))

        # --- 2. + 3. Bewerten und Reports erstellen ---
        reports: list[MarketReport] = []

        for niche in niches:
            report = self._niche_to_report(niche)

            if auto_score:
                self.score_idea(report)

            self.reports.append(report)
            reports.append(report)

        # --- 4. Im Memory-Store persistieren ---
        if persist:
            self._persist_leads(reports)

        # Sortiert nach Score zurückgeben (beste zuerst)
        reports.sort(
            key=lambda r: r.validation_score or 0.0,
            reverse=True,
        )

        logger.info(
            "Top-Nische: '%s' (Score: %.2f)",
            reports[0].niche_name,
            reports[0].validation_score or 0.0,
        )

        return reports

    # ------------------------------------------------------------------
    # Scoring (40/30/30-Modell)
    # ------------------------------------------------------------------
    def score_idea(self, report: MarketReport) -> float:
        """
        Berechnet einen Validierungs-Score basierend auf dem Marktbericht.

        Scoring-Faktoren (aus manifest.json):
        - Differenzierungspotenzial (40%)
        - Marktgröße (30%)
        - Wettbewerbsintensität (30%) – invertiert

        Returns:
            Validierungs-Score zwischen 0.0 und 1.0.
        """
        diff_score = report.differentiation_potential or 0.0
        market_score = report.market_size_score or 0.0

        # Weniger Wettbewerber = besser (inverse Skalierung)
        competition_score = max(
            0.0,
            1.0 - (report.competitor_count / MAX_COMPETITORS_BASELINE),
        )

        score = (
            (diff_score * WEIGHT_DIFFERENTIATION)
            + (market_score * WEIGHT_MARKET_SIZE)
            + (competition_score * WEIGHT_COMPETITION)
        )

        report.validation_score = round(score, 4)
        report.scored_at = datetime.utcnow().isoformat()

        logger.debug(
            "Score für '%s': diff=%.2f (×0.4) + market=%.2f (×0.3) + comp=%.2f (×0.3) = %.4f",
            report.niche_name,
            diff_score,
            market_score,
            competition_score,
            report.validation_score,
        )

        return report.validation_score

    # ------------------------------------------------------------------
    # Analyse (bestehende Methode, erweitert)
    # ------------------------------------------------------------------
    def analyze(self, idea_id: str, idea_description: str) -> MarketReport:
        """
        Führt eine Marktanalyse für eine gegebene Idee durch.

        TODO: Integration mit externen Datenquellen und LLM-basierter Analyse.
        """
        report = MarketReport(idea_id=idea_id, notes=idea_description)
        self.reports.append(report)
        return report

    # ------------------------------------------------------------------
    # Private Hilfsmethoden
    # ------------------------------------------------------------------
    def _niche_to_report(self, niche: TrendingNiche) -> MarketReport:
        """Konvertiert eine TrendingNiche in ein MarketReport-Objekt."""
        return MarketReport(
            idea_id=f"lead-{uuid.uuid4().hex[:8]}",
            niche_name=niche.name,
            market_size_estimate=niche.estimated_market_size,
            market_size_score=niche.market_size_score,
            competitor_count=niche.estimated_competitors,
            competitors=[
                {"name": name} for name in niche.competitor_names
            ],
            target_audience=niche.target_audience,
            differentiation_potential=niche.differentiation_potential,
            pricing_suggestion=niche.pricing_suggestion,
            source=niche.source,
            notes=niche.description,
        )

    def _persist_leads(self, reports: list[MarketReport]) -> None:
        """
        Speichert MarketReports im Memory-Store unter Kategorie 'leads'.

        Fängt Fehler graceful ab – ein fehlerhafter Memory-Store soll
        nicht den gesamten Analyse-Vorgang blockieren.
        """
        if self._memory is None:
            logger.warning(
                "Kein Memory-Store konfiguriert – %d Leads werden nicht persistiert.",
                len(reports),
            )
            return

        persisted = 0
        errors = 0

        for report in reports:
            try:
                # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
                from shared.memory.store import MemoryEntry

                entry = MemoryEntry(
                    id=report.idea_id,
                    category="leads",
                    content=asdict(report),
                    agent_source="researcher",
                    tags=_extract_tags(report),
                )

                self._memory.save(entry)
                persisted += 1

                logger.debug(
                    "Lead '%s' (%s) im Memory-Store gespeichert.",
                    report.niche_name,
                    report.idea_id,
                )

            except PermissionError as exc:
                errors += 1
                logger.error(
                    "Zugriffsfehler beim Speichern von Lead '%s': %s",
                    report.idea_id,
                    exc,
                )
            except OSError as exc:
                errors += 1
                logger.error(
                    "I/O-Fehler beim Speichern von Lead '%s': %s",
                    report.idea_id,
                    exc,
                )
            except Exception as exc:
                errors += 1
                logger.error(
                    "Unerwarteter Fehler beim Speichern von Lead '%s': %s",
                    report.idea_id,
                    exc,
                )

        if errors > 0:
            logger.warning(
                "Memory-Persistierung: %d/%d Leads gespeichert, %d Fehler.",
                persisted,
                len(reports),
                errors,
            )
        else:
            logger.info(
                "%d Leads erfolgreich im Memory-Store (Kategorie 'leads') gespeichert.",
                persisted,
            )


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _extract_tags(report: MarketReport) -> list[str]:
    """Extrahiert suchbare Tags aus einem MarketReport."""
    tags = [report.source]
    if report.niche_name:
        # Nischen-Name in Keywords aufteilen
        tags.extend(
            word.lower()
            for word in report.niche_name.replace("-", " ").split()
            if len(word) > 2
        )
    if report.target_audience:
        tags.append(report.target_audience.split(",")[0].strip().lower())
    return tags
