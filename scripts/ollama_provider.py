import requests
from config import OLLAMA_MODEL, OLLAMA_TAGS_URL, OLLAMA_PULL_URL

class OllamaProvider:
    """Basis-Klasse für alle Komponenten, die Ollama benötigen."""
    _model_verified = False

    def __init__(self):
            if not OllamaProvider._model_verified:
                if not self._ensure_model_is_available():
                    raise ConnectionError("Ollama is not reachable!")
                OllamaProvider._model_verified = True

    def _ensure_model_is_available(self):
        print(f"[*] Checking if Ollama model '{OLLAMA_MODEL}' is installed...")
        try:
            response = requests.get(OLLAMA_TAGS_URL, timeout=10)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                if OLLAMA_MODEL in models or f"{OLLAMA_MODEL}:latest" in models:
                    print(f"[+] Model '{OLLAMA_MODEL}' is ready.")
                    return True
            
            print(f"[!] Model '{OLLAMA_MODEL}' not found. Pulling from Ollama...")
            pull_payload = {"name": OLLAMA_MODEL, "stream": False}
            pull_resp = requests.post(OLLAMA_PULL_URL, json=pull_payload, timeout=1200)
            if pull_resp.status_code == 200:
                print(f"[+] Successfully pulled model '{OLLAMA_MODEL}'.")
                return True
            else:
                print(f"[!] Failed to pull model: {pull_resp.text}")
                return False
        except Exception as e:
            print(f"[!] Connection to Ollama failed: {e}")
            return False