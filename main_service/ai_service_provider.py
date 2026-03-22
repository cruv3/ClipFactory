import requests
import time
import config

class AIServiceProvider:
    """
    Zentrale Verwaltung für alle externen AI-Microservices.
    Merkt sich für jeden Service einzeln, ob er online ist.
    """
    
    # Status-Speicher für jeden einzelnen Service
    _service_status = {
        "LLM": False,
        "VOICE": False,
        "VIDEO": False
    }

    @classmethod
    def ensure_service_ready(cls, service_name: str, health_url: str) -> bool:
        """
        Prüft, ob der angegebene Service erreichbar ist. 
        Wartet geduldig, falls er gerade hochfährt.
        """
        if not config.USE_RTX_XX90:
            print(f"[*] Fallback Mode active. Skipping remote check for {service_name}.")
            return False

        # Wenn wir schon wissen, dass er online ist, direkt True zurückgeben
        if cls._service_status.get(service_name):
            return True

        print(f"[*] Checking {service_name} Service at {health_url}...")
        
        # Bis zu 2 Minuten warten (12 * 10s)
        max_attempts = 12
        for attempt in range(max_attempts):
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"[+] {service_name} Service is READY. (GPU: {data.get('gpu', 'Unknown')})")
                    cls._service_status[service_name] = True
                    return True
            except requests.exceptions.RequestException:
                print(f"[*] {service_name} Attempt {attempt + 1}/{max_attempts}: Booting up...")
                time.sleep(10)
        
        print(f"[!] ERROR: {service_name} Service failed to respond in time.")
        return False

    @classmethod
    def trigger_cleanup(cls, service_name: str, cleanup_url: str):
        """
        Schickt einen Cleanup-Befehl an den spezifischen Service, 
        um dessen VRAM sofort freizugeben.
        """
        if not config.USE_RTX_XX90:
            return
            
        try:
            response = requests.post(cleanup_url, timeout=10)
            if response.status_code == 200:
                print(f"[*] {service_name} VRAM Cleanup successful.")
            else:
                print(f"[-] {service_name} VRAM Cleanup returned status {response.status_code}.")
        except Exception as e:
            print(f"[-] Failed to trigger {service_name} VRAM cleanup: {e}")