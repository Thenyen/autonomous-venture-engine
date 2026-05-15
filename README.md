# 🚀 Autonomous Venture Engine

> Ein autonomes System zur Validierung und Umsetzung von Micro-SaaS-Ideen.

## Architektur

```
autonomous-venture-engine/
├── manifest.json              # Agenten-Rollen & Kompetenzen
├── core/
│   └── brain/                 # Strategische Entscheidungslogik
│       ├── __init__.py
│       └── orchestrator.py    # Pipeline-Management & Orchestrierung
├── agents/
│   ├── researcher/            # Marktanalyse-Agent
│   │   ├── __init__.py
│   │   └── analyzer.py        # Marktbewertung & Scoring
│   └── coder/                 # App-Erstellungs-Agent
│       ├── __init__.py
│       └── builder.py         # MVP- & Landing-Page-Generierung
└── shared/
    └── memory/                # Wissensaustausch zwischen Agenten
        ├── __init__.py
        ├── store.py           # Persistenter JSON-basierter Memory Store
        └── data/              # Gespeicherte Einträge (ideas, decisions, learnings)
```

## Agenten

| Agent | Rolle | Pfad |
|-------|-------|------|
| **Brain** | Zentrale Steuerung, Priorisierung, Go/No-Go-Entscheidungen | `core/brain/` |
| **Researcher** | Marktanalyse, Wettbewerbsbewertung, Validierung | `agents/researcher/` |
| **Coder** | App-Generierung, MVP-Erstellung, Deployment | `agents/coder/` |

## Pipeline

```
Ideation → Research → Validation → Decision → Development → Launch → Monitoring
```

## Status

🟡 **Phase 0** – Grundstruktur initialisiert. Bereit für den nächsten Schritt.