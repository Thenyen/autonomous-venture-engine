"""
App Builder
===========

Generiert und deployt Micro-SaaS-Anwendungen.
Liest qualifizierte Leads aus dem Memory-Store und erstellt
daraus requirements.md + Landing Page (index.html).
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Projekt-Root (2 Ebenen über agents/coder/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class BuildStatus(Enum):
    """Status eines Build-Auftrags."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPLOYED = "deployed"


@dataclass
class BuildSpec:
    """Spezifikation für einen App-Build."""
    idea_id: str
    app_name: str
    description: str
    tech_stack: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    target_audience: str = ""
    pricing_model: str = ""


@dataclass
class BuildResult:
    """Ergebnis eines Build-Vorgangs."""
    spec: BuildSpec
    status: BuildStatus = BuildStatus.PENDING
    output_path: Optional[str] = None
    deployment_url: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)


class BuildError(Exception):
    """Wird geworfen, wenn ein Build-Vorgang fehlschlägt."""
    pass


class AppBuilder:
    """
    Micro-SaaS App Builder.

    Generiert Anwendungen basierend auf validierten Spezifikationen.
    Unterstützt verschiedene App-Typen: Landing Pages, Web-Apps, APIs.
    """

    def __init__(self):
        self.builds: list[BuildResult] = []

    # ------------------------------------------------------------------
    # MVP-Spec-Generierung aus Lead
    # ------------------------------------------------------------------
    def generate_mvp_spec(self, lead_path: Path) -> BuildResult:
        """
        Liest einen qualifizierten Lead und generiert daraus:
        1. Eine BuildSpec aus den Lead-Daten
        2. requirements.md im Projekt-Root
        3. index.html (Tailwind-Landing-Page) in /builds/[venture_name]/

        Args:
            lead_path: Pfad zur JSON-Datei des qualifizierten Leads.

        Returns:
            BuildResult mit output_path zum Build-Verzeichnis.

        Raises:
            BuildError: Wenn der Lead nicht gelesen werden kann.
        """
        # --- 1. Lead einlesen ---
        lead_data = self._read_lead(lead_path)
        content = lead_data.get("content", lead_data)

        niche_name = content.get("niche_name", "Unknown Venture")
        description = content.get("notes", content.get("description", ""))
        target_audience = content.get("target_audience", "")
        pricing = content.get("pricing_suggestion", "")
        score = content.get("validation_score", 0)
        competitors = content.get("competitors", [])
        market_size = content.get("market_size_estimate", "")
        diff_potential = content.get("differentiation_potential", 0)

        logger.info("Lead geladen: '%s' (Score: %s)", niche_name, score)

        # --- 2. BuildSpec erstellen ---
        slug = self._slugify(niche_name)
        spec = BuildSpec(
            idea_id=content.get("idea_id", "unknown"),
            app_name=niche_name,
            description=description,
            tech_stack=["HTML5", "Tailwind CSS", "JavaScript"],
            features=self._derive_features(description),
            target_audience=target_audience,
            pricing_model=pricing,
        )

        result = self.create_build(spec)
        result.status = BuildStatus.IN_PROGRESS

        # --- 3. Build-Verzeichnis anlegen ---
        build_dir = PROJECT_ROOT / "builds" / slug
        build_dir.mkdir(parents=True, exist_ok=True)
        result.output_path = str(build_dir)
        result.logs.append(f"Build-Verzeichnis erstellt: {build_dir}")

        # --- 4. requirements.md generieren ---
        req_path = self._write_requirements(
            build_dir, niche_name, description, target_audience,
            pricing, score, competitors, market_size, diff_potential, spec.features,
        )
        result.logs.append(f"requirements.md erstellt: {req_path}")

        # --- 5. index.html generieren ---
        html_path = self._write_landing_page(
            build_dir, niche_name, description, target_audience,
            pricing, spec.features,
        )
        result.logs.append(f"index.html erstellt: {html_path}")

        result.status = BuildStatus.COMPLETED
        logger.info("MVP-Spec komplett: %s", build_dir)
        return result

    # ------------------------------------------------------------------
    # Bestehende Methoden
    # ------------------------------------------------------------------
    def create_build(self, spec: BuildSpec) -> BuildResult:
        """Erstellt einen neuen Build-Auftrag."""
        result = BuildResult(spec=spec)
        self.builds.append(result)
        return result

    def generate_landing_page(self, spec: BuildSpec) -> BuildResult:
        """Generiert eine Landing Page für ein Micro-SaaS-Produkt."""
        result = self.create_build(spec)
        result.status = BuildStatus.IN_PROGRESS
        result.logs.append(f"Landing Page generation started for: {spec.app_name}")
        return result

    def generate_mvp(self, spec: BuildSpec) -> BuildResult:
        """Generiert ein MVP für ein Micro-SaaS-Produkt."""
        result = self.create_build(spec)
        result.status = BuildStatus.IN_PROGRESS
        result.logs.append(f"MVP generation started for: {spec.app_name}")
        return result

    # ------------------------------------------------------------------
    # Private Hilfsmethoden
    # ------------------------------------------------------------------
    def _read_lead(self, lead_path: Path) -> dict:
        """Liest und validiert die Lead-JSON-Datei."""
        lead_path = Path(lead_path)
        if not lead_path.exists():
            raise BuildError(f"Lead-Datei nicht gefunden: {lead_path}")
        try:
            data = json.loads(lead_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise BuildError(f"Lead-Datei konnte nicht gelesen werden: {exc}") from exc

        logger.debug("Lead-JSON geladen: %s", lead_path)
        return data

    @staticmethod
    def _slugify(name: str) -> str:
        """Konvertiert einen Namen in einen Ordner-sicheren Slug."""
        slug = name.lower().strip()
        slug = re.sub(r"[äöüß]", lambda m: {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}[m.group()], slug)
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    @staticmethod
    def _derive_features(description: str) -> list[str]:
        """Leitet Feature-Liste aus der Beschreibung ab."""
        keywords = {
            "automatisch": "Automatisierte Workflows",
            "zusammenfassung": "Intelligente Zusammenfassungen",
            "community": "Community-Funktionen",
            "paywall": "Integriertes Bezahlsystem",
            "no-code": "No-Code Builder",
            "notification": "Smart Notifications",
            "action": "Action-Item Tracking",
            "changelog": "Release Management",
            "voting": "Feature-Voting",
            "feedback": "Feedback-Sammlung",
            "kategorisierung": "Auto-Kategorisierung",
            "priorisierung": "Intelligente Priorisierung",
            "rechnung": "Rechnungsmanagement",
            "mahn": "Automatisches Mahnwesen",
        }
        desc_lower = description.lower()
        features = [feat for kw, feat in keywords.items() if kw in desc_lower]
        if not features:
            features = ["Kern-Funktionalität", "Benutzer-Dashboard", "API-Zugang"]
        return features

    def _write_requirements(
        self, build_dir, name, desc, audience, pricing, score,
        competitors, market_size, diff_potential, features,
    ) -> Path:
        """Schreibt die requirements.md."""
        comp_list = "\n".join(f"- {c.get('name', c)}" for c in competitors) if competitors else "- Keine bekannt"
        feat_list = "\n".join(f"- {f}" for f in features)

        md = f"""# {name} – Requirements

## Übersicht
{desc}

## Validierung
| Metrik | Wert |
|--------|------|
| Validation Score | {score} |
| Marktgröße | {market_size} |
| Differenzierungspotenzial | {diff_potential} |

## Zielgruppe
{audience}

## Preismodell
{pricing}

## Wettbewerber
{comp_list}

## Features (MVP)
{feat_list}

## Tech-Stack
- HTML5 / CSS (Tailwind CSS)
- JavaScript (Vanilla)
- Statisches Hosting (MVP-Phase)

## Nächste Schritte
1. Landing Page veröffentlichen
2. Waitlist-Signups sammeln
3. MVP-Kernfunktionalität entwickeln
4. Beta-Launch mit Early Adopters
"""
        path = build_dir / "requirements.md"
        path.write_text(md, encoding="utf-8")
        return path

    def _write_landing_page(self, build_dir, name, desc, audience, pricing, features) -> Path:
        """Generiert eine moderne Tailwind-CSS Landing Page."""
        feat_cards = "\n".join(self._feature_card_html(f, i) for i, f in enumerate(features))

        html = f"""<!DOCTYPE html>
<html lang="de" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{desc[:155]}">
    <title>{name} – Die smarte Lösung für {audience.split(',')[0].strip()}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: {{ 50:'#f0f9ff',100:'#e0f2fe',200:'#bae6fd',300:'#7dd3fc',400:'#38bdf8',500:'#0ea5e9',600:'#0284c7',700:'#0369a1',800:'#075985',900:'#0c4a6e',950:'#082f49' }},
                        accent: {{ 50:'#fdf4ff',100:'#fae8ff',200:'#f5d0fe',300:'#f0abfc',400:'#e879f9',500:'#d946ef',600:'#c026d3',700:'#a21caf',800:'#86198f',900:'#701a75',950:'#4a044e' }},
                    }},
                    fontFamily: {{ sans: ['Inter', 'system-ui', 'sans-serif'] }},
                }}
            }}
        }}
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        .gradient-bg {{ background: linear-gradient(135deg, #0c4a6e 0%, #1e1b4b 50%, #4a044e 100%); }}
        .glass {{ background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); }}
        .glow {{ box-shadow: 0 0 40px rgba(14,165,233,0.15), 0 0 80px rgba(217,70,239,0.1); }}
        .float {{ animation: float 6s ease-in-out infinite; }}
        @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-20px); }} }}
        .fade-in {{ animation: fadeIn 0.8s ease-out forwards; opacity: 0; }}
        @keyframes fadeIn {{ to {{ opacity: 1; }} }}
        .slide-up {{ animation: slideUp 0.8s ease-out forwards; opacity: 0; transform: translateY(30px); }}
        @keyframes slideUp {{ to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body class="gradient-bg text-white font-sans antialiased">

    <!-- Nav -->
    <nav class="fixed top-0 w-full z-50 glass">
        <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center text-sm font-bold">✦</div>
                <span class="text-lg font-bold">{name}</span>
            </div>
            <div class="hidden md:flex items-center gap-8 text-sm text-white/70">
                <a href="#features" class="hover:text-white transition">Features</a>
                <a href="#pricing" class="hover:text-white transition">Pricing</a>
                <a href="#cta" class="hover:text-white transition">Kontakt</a>
            </div>
            <a href="#cta" class="px-5 py-2 rounded-full bg-gradient-to-r from-primary-500 to-accent-500 text-sm font-semibold hover:shadow-lg hover:shadow-primary-500/25 transition-all duration-300 hover:scale-105">
                Jetzt starten
            </a>
        </div>
    </nav>

    <!-- Hero -->
    <header class="min-h-screen flex items-center justify-center px-6 pt-20">
        <div class="max-w-4xl mx-auto text-center">
            <div class="fade-in inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm text-primary-300 mb-8">
                <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                Jetzt verfügbar – Für {audience.split(',')[0].strip()}
            </div>
            <h1 class="slide-up text-5xl md:text-7xl font-black leading-tight mb-6" style="animation-delay: 0.2s">
                <span class="bg-gradient-to-r from-white via-primary-200 to-accent-300 bg-clip-text text-transparent">
                    {name}
                </span>
            </h1>
            <p class="slide-up text-lg md:text-xl text-white/60 max-w-2xl mx-auto mb-10 leading-relaxed" style="animation-delay: 0.4s">
                {desc}
            </p>
            <div class="slide-up flex flex-col sm:flex-row items-center justify-center gap-4" style="animation-delay: 0.6s">
                <a href="#cta" class="px-8 py-4 rounded-2xl bg-gradient-to-r from-primary-500 to-accent-500 font-semibold text-lg hover:shadow-xl hover:shadow-primary-500/30 transition-all duration-300 hover:scale-105">
                    Kostenlos testen →
                </a>
                <a href="#features" class="px-8 py-4 rounded-2xl glass font-semibold hover:bg-white/10 transition-all duration-300">
                    Features entdecken
                </a>
            </div>
            <div class="mt-16 float">
                <div class="glass glow rounded-2xl p-8 max-w-lg mx-auto">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-3 h-3 rounded-full bg-red-400"></div>
                        <div class="w-3 h-3 rounded-full bg-yellow-400"></div>
                        <div class="w-3 h-3 rounded-full bg-green-400"></div>
                        <span class="text-white/30 text-xs ml-2">{name.lower().replace(' ', '-')}.app</span>
                    </div>
                    <div class="space-y-3">
                        <div class="h-4 bg-white/10 rounded w-3/4"></div>
                        <div class="h-4 bg-white/10 rounded w-1/2"></div>
                        <div class="h-8 bg-gradient-to-r from-primary-500/30 to-accent-500/30 rounded-lg w-full mt-4"></div>
                        <div class="grid grid-cols-3 gap-2 mt-2">
                            <div class="h-16 bg-white/5 rounded-lg"></div>
                            <div class="h-16 bg-white/5 rounded-lg"></div>
                            <div class="h-16 bg-white/5 rounded-lg"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Features -->
    <section id="features" class="py-24 px-6">
        <div class="max-w-6xl mx-auto">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-5xl font-bold mb-4">Alles, was du brauchst</h2>
                <p class="text-white/50 text-lg max-w-xl mx-auto">Entwickelt für {audience}</p>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
{feat_cards}
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="py-24 px-6">
        <div class="max-w-4xl mx-auto text-center">
            <h2 class="text-3xl md:text-5xl font-bold mb-4">Einfaches Pricing</h2>
            <p class="text-white/50 text-lg mb-12">Transparent, fair, ohne versteckte Kosten.</p>
            <div class="glass glow rounded-3xl p-10 max-w-md mx-auto">
                <div class="text-accent-400 text-sm font-semibold uppercase tracking-widest mb-2">Pro Plan</div>
                <div class="text-5xl font-black mb-2">{pricing.split('/')[0] if '/' in pricing else pricing}</div>
                <div class="text-white/40 mb-8">{'/'.join(pricing.split('/')[1:]) if '/' in pricing else 'pro Monat'}</div>
                <ul class="text-left space-y-3 mb-8">
                    {"".join(f'<li class="flex items-center gap-3 text-white/80"><span class="text-green-400">✓</span>{f}</li>' for f in features)}
                    <li class="flex items-center gap-3 text-white/80"><span class="text-green-400">✓</span>Priority Support</li>
                </ul>
                <a href="#cta" class="block w-full py-4 rounded-2xl bg-gradient-to-r from-primary-500 to-accent-500 font-semibold text-center hover:shadow-xl hover:shadow-primary-500/30 transition-all duration-300 hover:scale-105">
                    Jetzt starten
                </a>
            </div>
        </div>
    </section>

    <!-- CTA -->
    <section id="cta" class="py-24 px-6">
        <div class="max-w-3xl mx-auto text-center">
            <h2 class="text-3xl md:text-5xl font-bold mb-6">Bereit loszulegen?</h2>
            <p class="text-white/50 text-lg mb-10">Trage dich in die Waitlist ein und gehöre zu den Ersten.</p>
            <form id="waitlist-form" class="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto" onsubmit="event.preventDefault(); document.getElementById('success-msg').classList.remove('hidden'); this.classList.add('hidden');">
                <input id="waitlist-email" type="email" placeholder="deine@email.de" required
                    class="flex-1 px-6 py-4 rounded-2xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-400/20 transition">
                <button type="submit" class="px-8 py-4 rounded-2xl bg-gradient-to-r from-primary-500 to-accent-500 font-semibold whitespace-nowrap hover:shadow-xl hover:shadow-primary-500/30 transition-all duration-300 hover:scale-105">
                    Eintragen →
                </button>
            </form>
            <div id="success-msg" class="hidden mt-6 p-4 rounded-2xl glass text-green-400 font-semibold">
                🎉 Du bist auf der Waitlist! Wir melden uns bald.
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-white/5 py-8 px-6">
        <div class="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-white/30">
            <span>© 2026 {name}. Autonomous Venture Engine.</span>
            <div class="flex gap-6">
                <a href="#" class="hover:text-white/60 transition">Impressum</a>
                <a href="#" class="hover:text-white/60 transition">Datenschutz</a>
            </div>
        </div>
    </footer>

</body>
</html>"""
        path = build_dir / "index.html"
        path.write_text(html, encoding="utf-8")
        return path

    @staticmethod
    def _feature_card_html(feature: str, index: int) -> str:
        """Erzeugt eine Feature-Card als HTML-String."""
        icons = ["⚡", "🔒", "📊", "🚀", "🎯", "💎", "🔗", "✨"]
        icon = icons[index % len(icons)]
        delay = index * 0.1
        return f"""                <div class="glass rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-primary-500/10" style="animation: fadeIn 0.6s ease-out {delay}s forwards; opacity: 0;">
                    <div class="text-3xl mb-4">{icon}</div>
                    <h3 class="text-lg font-semibold mb-2">{feature}</h3>
                    <p class="text-white/40 text-sm">Optimiert für maximale Produktivität und nahtlose Integration in deinen Workflow.</p>
                </div>"""
