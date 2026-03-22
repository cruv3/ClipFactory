from fastapi import FastAPI
import sys
import os

print("="*50)
print("[*] Starte API und setze Python-Pfade...")

# BRECHSTANGE V2: Jetzt mit dem korrekten 'packages' Ordner!
LTX_DIR = "/opt/LTX-2"

# Falls Lightricks den Code im 'packages' Unterordner hat (laut deinem Snippet)
sys.path.insert(0, f"{LTX_DIR}/packages/ltx-pipelines/src")
sys.path.insert(0, f"{LTX_DIR}/packages/ltx-core/src")

# Sicherheitshalber, falls sie es doch direkt im Root haben
sys.path.insert(0, f"{LTX_DIR}/ltx-pipelines/src")
sys.path.insert(0, f"{LTX_DIR}/ltx-core/src")
sys.path.insert(0, LTX_DIR)

# Jetzt testen wir den Import
try:
    from ltx_pipelines.ti2vid_two_stages import TI2VidTwoStagesPipeline
    print("[+] BINGO: ltx_pipelines wurde gefunden und geladen!")
    IMPORT_STATUS = "Erfolgreich"
except Exception as e:
    print(f"[-] FEHLER beim Import: {e}")
    IMPORT_STATUS = f"Fehler: {e}"

print("="*50)

app = FastAPI(title="LTX-Video Test")

@app.get("/health")
async def health_check():
    return {
        "status": "online", 
        "import_status": IMPORT_STATUS
    }