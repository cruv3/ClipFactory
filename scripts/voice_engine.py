import requests
import os
import whisper

from config import KOKORO_URL

class VoiceEngine:
    def __init__(self):
        self.model_verified = self._verify_kokoro()

    def generate_audio(self, text, strategy, speed=1.0):
        os.makedirs(strategy.output_dir, exist_ok=True)
        
        filename = "narrator.wav"
        full_output_path = os.path.join(strategy.output_dir, filename)
        
        print(f"[*] Sending text to Kokoro (Voice: {strategy.voice}, Speed: {speed})...")
        
        payload = {
            "model": "kokoro",
            "input": text,
            "voice": strategy.voice,
            "response_format": "wav",
            "speed": speed 
        }
        
        try:
            response = requests.post(KOKORO_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            with open(full_output_path, "wb") as audio_file:
                audio_file.write(response.content)
                
            print(f"[+] Audio saved: {full_output_path}")
            return full_output_path
            
        except requests.exceptions.ConnectionError:
            print(f"[!] ERROR: Kokoro unreachable at {KOKORO_URL}")
            return None
        except Exception as e:
            print(f"[!] TTS Error: {e}")
            return None
        
    def get_word_timestamps(audio_path):
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, verbose=False, word_timestamps=True)
        
        word_data = []
        for segment in result['segments']:
            for w in segment['words']:
                word_data.append({
                    "word": w['word'].strip().upper(),
                    "start": w['start'],
                    "end": w['end']
                })
        return word_data
    
    def _verify_kokoro(self):
        print(f"[*] Checking Kokoro TTS at {KOKORO_URL}...")
        try:
            # Wir säubern die URL für den Root-Check
            base_url = KOKORO_URL.replace("/v1/audio/speech", "")
            response = requests.get(base_url, timeout=3)
            
            if response.status_code == 200:
                print("[+] Kokoro TTS is ready.")
                return True
            return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"[!] Kokoro TTS not reachable yet at {KOKORO_URL}...")
            return False
        except Exception as e:
            print(f"[!] Unexpected TTS Check Error: {e}")
            return False

# --- TEST RUN ---
if __name__ == "__main__":
    engine = VoiceEngine()
    test_text = "The shadows in my room don't match the furniture anymore. One of them just stood up."
    
    # Test mit einer fiktiven Story-ID
    path = engine.generate_audio(test_text, story_id="test_run_001", voice="am_onyx")
    
    if path:
        print(f"🎉 Voice Test successful! File at: {path}")