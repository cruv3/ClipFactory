import requests
import os
import whisper
import time
import warnings
import re

warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import config

class VoiceEngine:
    def __init__(self):
        self.model = whisper.load_model("base")

    def generate_audio(self, text, strategy):
        os.makedirs(strategy.output_dir, exist_ok=True)
        safe_text = self._sanitize_text(text)
        filename = "narrator.wav"
        full_output_path = os.path.join(strategy.output_dir, filename)
        
        clamped_speed = min(2.0, max(1.0, strategy.voice_speed))
        print(f"[*] Sending text to Kokoro (Voice: {strategy.voice}, Speed: {clamped_speed})...")
        payload = {
            "model": "kokoro",
            "input": safe_text,
            "voice": strategy.voice,
            "response_format": "wav",
            "speed": clamped_speed,
        }
        
        try:
            response = requests.post(config.API_GENERATE_VOICE, json=payload, timeout=600)
            response.raise_for_status()
            
            with open(full_output_path, "wb") as audio_file:
                audio_file.write(response.content)
                
            print(f"[+] Audio saved: {full_output_path}")
            return full_output_path
            
        except requests.exceptions.ConnectionError:
            print(f"[!] ERROR: Kokoro unreachable at {config.API_GENERATE_VOICE}")
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
        
    @staticmethod
    def _sanitize_text(text):
        """
        Wandelt komplett großgeschriebene Wörter (ab 3 Buchstaben) in normale 
        Schreibweise um, damit die TTS sie als Wort und nicht als Buchstabensalat liest.
        Beispiel: "BROKENHEARTED" -> "Brokenhearted"
        """
        def replace_caps(match):
            return match.group(0).capitalize() 
        return re.sub(r'\b[A-Z]{3,}\b', replace_caps, text)

# --- TEST RUN ---
if __name__ == "__main__":
    import dataclasses

    engine = VoiceEngine()
        
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
        voice_speed: float
        
    test_strategy = MockStrategy(
        voice="am_onyx",
        voice_speed=1.25,
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