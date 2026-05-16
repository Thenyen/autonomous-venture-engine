from agents.researcher.analyzer import MarketAnalyzer
from shared.memory.store import MemoryStore

def main():
    print("🚀 Starte Autonomous Venture Researcher...")
    
    # Initialisiere Memory und Researcher
    memory = MemoryStore()
    researcher = MarketAnalyzer(memory_store=memory)
    
    # Führe die Analyse aus
    reports = researcher.fetch_trending_niches()
    
    print(f"\n✅ Analyse abgeschlossen. {len(reports)} Leads gefunden.")
    print("-" * 30)
    
    for i, r in enumerate(reports[:3], 1):
        print(f"{i}. {r.niche_name} | Score: {r.validation_score}")
        print(f"   Zielgruppe: {r.target_audience}")
        print(f"   Potential: {r.notes[:60]}...")
        print("-" * 30)

if __name__ == "__main__":
    main()