import requests
import time
from config import VIDEO_AI_URL, USE_RTX_XX90

class AIServiceProvider:
    """
    Basis-Klasse für alle Komponenten, die den High-End AI Service 
    (RTX 3090 Master API) benötigen.
    """
    service_verified = False

    def __init__(self):
        # Wir prüfen den Service nur, wenn die 3090 auch aktiv sein soll
        if USE_RTX_XX90 and not AIServiceProvider.service_verified:
            if not self._ensure_service_is_reachable():
                print("[!] Warning: AI Master Service (RTX 3090) is not reachable!")
                print("[*] Switching to local fallback mode (1660 Ti style).")
                AIServiceProvider.service_verified = True 
            else:
                AIServiceProvider.service_verified = True

    def _ensure_service_is_reachable(self):
        """
        Prüft den /health Endpunkt deines neuen AI-Services.
        """
        health_url = f"{VIDEO_AI_URL}/health"
        print(f"[*] Checking AI Master Service at {health_url}...")
        
        # Wir geben dem Service 3 Versuche (falls er gerade noch Modelle lädt)
        for attempt in range(3):
            try:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f"[+] AI Master Service is READY. GPU: {data.get('gpu', 'Unknown')}")
                    return True
            except Exception:
                print(f"[*] Attempt {attempt + 1}/3: Service still starting up...")
                time.sleep(5)
        
        return False

    def trigger_vram_cleanup(self):
        """Erlaubt es jeder Unterklasse, den VRAM der 3090 manuell zu putzen."""
        try:
            requests.post(f"{VIDEO_AI_URL}/cleanup", timeout=10)
            print("[*] VRAM Cleanup triggered via Provider.")
        except:
            pass