from fastapi import FastAPI
import sys
import os

print("="*50)
print("[*] Starte API und setze Python-Pfade...")

# BRECHSTANGE: Wir hämmern alle möglichen Pfade des geklonten Repos in Pythons Hirn
LTX_DIR = "/opt/LTX-2"
sys.path.insert(0, LTX_DIR)
sys.path.insert(0, f"{LTX_DIR}/ltx-pipelines")
sys.path.insert(0, f"{LTX_DIR}/ltx-pipelines/src") # Falls der Code im src-Ordner liegt
sys.path.insert(0, f"{LTX_DIR}/ltx-core")
sys.path.insert(0, f"{LTX_DIR}/ltx-core/src")

# Jetzt testen wir den Import
try:
    from ltx_pipelines.ti2vid_two_stages import TI2VidTwoStagesPipeline
    print("[+] ERFOLG: ltx_pipelines wurde gefunden und geladen!")
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