import logging
from core.brain.orchestrator import Orchestrator
from agents.coder.builder import AppBuilder

# Logging konfigurieren, damit wir sehen, was passiert
logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_venture_engine():
    print("\n" + "="*50)
    print("🚀 AUTONOMOUS VENTURE ENGINE v1.0")
    print("="*50 + "\n")

    # 1. Orchestrator (CEO) initialisieren
    brain = Orchestrator()

    # 2. Discovery Phase (Marktanalyse & Qualifizierung)
    try:
        lead_path = brain.run_discovery_phase(threshold=0.6)
    except Exception as e:
        print(f"❌ Discovery abgebrochen: {e}")
        return

    # 3. Build Phase (MVP-Generierung durch den Coder)
    print("\n🔨 Starte Build Phase...")
    coder = AppBuilder()
    build_result = coder.generate_mvp_spec(lead_path)

    if build_result.status.value == "completed":
        print(f"\n✅ ERFOLG: MVP für '{build_result.spec.app_name}' erstellt!")
        print(f"📂 Ort: {build_result.output_path}")
        print(f"🌐 Öffne die index.html in deinem Browser, um die Landing Page zu sehen.")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    run_venture_engine()