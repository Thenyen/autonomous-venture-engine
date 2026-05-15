"""
Memory Store
============

Persistenter Wissenspeicher für den Austausch zwischen Agenten.
Speichert Ideen, Entscheidungen und Learnings als JSON-Dateien.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional
from pathlib import Path


MEMORY_DIR = Path(__file__).parent / "data"


@dataclass
class MemoryEntry:
    """Ein einzelner Eintrag im Memory Store."""
    id: str
    category: str  # "ideas" | "decisions" | "learnings" | "leads"
    content: dict = field(default_factory=dict)
    agent_source: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: list[str] = field(default_factory=list)


class MemoryStore:
    """
    Zentraler Wissenspeicher.

    Kategorien:
    - ideas: Pool aller generierten und bewerteten Micro-SaaS-Ideen
    - decisions: Protokoll aller Go/No-Go-Entscheidungen mit Begründungen
    - learnings: Gesammelte Erkenntnisse und Lessons Learned
    - leads: Vom Researcher identifizierte und bewertete Nischen-Leads

    Daten werden als JSON-Dateien unter shared/memory/data/ gespeichert.
    """

    CATEGORIES = ("ideas", "decisions", "learnings", "leads")

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or MEMORY_DIR
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Erstellt die Verzeichnisstruktur für alle Kategorien."""
        for category in self.CATEGORIES:
            (self.base_dir / category).mkdir(parents=True, exist_ok=True)

    def save(self, entry: MemoryEntry) -> Path:
        """Speichert einen Memory-Eintrag als JSON-Datei."""
        if entry.category not in self.CATEGORIES:
            raise ValueError(f"Unbekannte Kategorie: {entry.category}. Erlaubt: {self.CATEGORIES}")

        filepath = self.base_dir / entry.category / f"{entry.id}.json"
        filepath.write_text(json.dumps(asdict(entry), indent=2, ensure_ascii=False), encoding="utf-8")
        return filepath

    def load(self, category: str, entry_id: str) -> Optional[MemoryEntry]:
        """Lädt einen Memory-Eintrag anhand von Kategorie und ID."""
        filepath = self.base_dir / category / f"{entry_id}.json"
        if not filepath.exists():
            return None

        data = json.loads(filepath.read_text(encoding="utf-8"))
        return MemoryEntry(**data)

    def list_entries(self, category: str) -> list[MemoryEntry]:
        """Listet alle Einträge einer Kategorie."""
        category_dir = self.base_dir / category
        if not category_dir.exists():
            return []

        entries = []
        for filepath in sorted(category_dir.glob("*.json")):
            data = json.loads(filepath.read_text(encoding="utf-8"))
            entries.append(MemoryEntry(**data))
        return entries

    def search(self, query: str, category: Optional[str] = None) -> list[MemoryEntry]:
        """
        Durchsucht den Memory Store nach einem Suchbegriff.

        TODO: Volltextsuche und semantische Suche integrieren.
        """
        results = []
        categories = [category] if category else self.CATEGORIES

        for cat in categories:
            for entry in self.list_entries(cat):
                content_str = json.dumps(entry.content, ensure_ascii=False).lower()
                if query.lower() in content_str or query.lower() in " ".join(entry.tags).lower():
                    results.append(entry)

        return results
