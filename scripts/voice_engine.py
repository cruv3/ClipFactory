import requests
import os
import whisper
import time
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from config import KOKORO_URL, KOKORO_URL_WEB

class VoiceEngine:
    def __init__(self):
        self.model_verified = self.verify_kokoro()
        self.model = whisper.load_model("base")

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
            response = requests.post(KOKORO_URL, json=payload, timeout=600)
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
        
    def get_word_timestamps(self, audio_path):
        result = self.model.transcribe(audio_path, verbose=False, word_timestamps=True)
        
        word_data = []
        for segment in result['segments']:
            for w in segment['words']:
                word_data.append({
                    "word": w['word'].strip().upper(),
                    "start": w['start'],
                    "end": w['end']
                })
        return word_data
    
    def verify_kokoro(self):
        print(f"[*] Checking Kokoro TTS at {KOKORO_URL_WEB}...")
        try:
            response = requests.get(KOKORO_URL_WEB, timeout=3)
            
            if response.status_code == 200:
                print("[+] Kokoro TTS is ready.")
                return True
            return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"[!] Kokoro TTS not reachable yet at {KOKORO_URL_WEB}...")
            return False
        except Exception as e:
            print(f"[!] Unexpected TTS Check Error: {e}")
            return False

# --- TEST RUN ---
if __name__ == "__main__":
    import dataclasses

    engine = VoiceEngine()

    while not engine.model_verified:
        time.sleep(10)
        engine.model_verified = engine.verify_kokoro()
        
    # Genau ~250 Wörter: Perfekt für einen Stress-Test von Kokoro & Whisper!
    test_text = """
    I recently moved into a new apartment with a guy I found online, let's call him Mark. At first, everything was completely normal. 
    We split the rent, kept the place clean, and occasionally played video games on the weekends. But then, the weird things started happening. 
    It began with the food. I'd buy a carton of milk, and the next day it would be exactly half empty, but the cap was glued shut. 
    Literally superglued. I thought it was a bizarre prank. Then, I started noticing my shoes were being moved. 
    I always leave them pointing towards the door, but I'd wake up and they'd be facing the window. When I confronted Mark, he just laughed and said I was being paranoid. 
    Last week, it escalated to a terrifying level. I woke up at 3 AM because I heard a faint scratching sound coming from the living room. 
    I crept out of bed, peeked around the corner, and saw Mark sitting in the pitch dark. He wasn't watching TV or on his phone. 
    He was just staring blankly at the blank wall, running a butter knife up and down the drywall, creating this agonizing scraping noise. 
    I flicked the light switch, and he instantly snapped his head towards me, smiled this incredibly wide, unnatural smile, and whispered, 
    'They are almost through.' I locked myself in my room and haven't slept since. My lease isn't up for another six months. What am I supposed to do?
    """
    
    # Saubere MockStrategy mit allen Properties, die auch die echte Engine liefert
    @dataclasses.dataclass
    class MockStrategy:
        voice: str
        hook_style: str
        folder_name: str
        search_query: str
        reason: str
        caption: str
        description: str
        tags: str
        output_dir: str
        
    test_strategy = MockStrategy(
        voice="am_onyx",
        hook_style="Creepy",
        folder_name="creepy_stories",
        search_query="dark forest drone 4k no commentary",
        reason="A creepy story needs a deep voice and unsettling background.",
        caption="My roommate is doing WHAT at 3 AM?! 😳🔪",
        description="This roommate story will give you nightmares...",
        tags="#storytime #scary #creepy #reddit #roommate",
        output_dir="data/test_run_001"
    )
    
    path = engine.generate_audio(test_text, strategy=test_strategy)
    
    if path:
        print(f"🎉 Voice Test successful! File at: {path}")
        timestamps = engine.get_word_timestamps(path)
        if timestamps:
            print(f"✅ Timestamps successfully extracted. First word: {timestamps[0]} | Last word: {timestamps[-1]}")