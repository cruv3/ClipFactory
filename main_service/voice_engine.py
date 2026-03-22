import requests
import os
import whisper
import time
import warnings
import re
import shutil

warnings.filterwarnings("ignore", category=UserWarning)

import config
from ai_service_provider import AIServiceProvider

class VoiceEngine:
    def __init__(self):
        # Whisper laden wir lokal, da es CPU-freundlich ist und Word-Timestamps braucht
        print("[*] Loading Whisper model (base)...")
        self.model = whisper.load_model("base")

    def generate_audio(self, text, strategy):
        """
        Spricht den Text via Kokoro Microservice und speichert ihn lokal ab.
        """
        # 1. Health Check via Provider
        if not AIServiceProvider.ensure_service_ready("VOICE", config.API_VOICE_HEALTH):
            print("[!] VOICE Service is not ready. Aborting.")
            return None
        
        # 2. Vorbereitung
        os.makedirs(strategy.output_dir, exist_ok=True)
        safe_text = self._sanitize_text(text)
        local_filename = "narrator.wav"
        full_local_path = os.path.join(strategy.output_dir, local_filename)
        
        # 3. Payload für dein neues FastAPI VoiceRequest Model
        payload = {
            "script_text": safe_text,
            "folder_name": strategy.folder_name,
            "voice_name": strategy.voice, # z.B. "af_bella" oder "am_adam"
            "speed": min(2.0, max(0.5, strategy.voice_speed))
        }
        
        print(f"[*] Sending TTS Request to Kokoro Service (Voice: {strategy.voice})...")
        
        try:
            # Request an den Microservice
            response = requests.post(config.API_GENERATE_VOICE, json=payload, timeout=300)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "success":
                server_rel_path = data.get("rel_path") # z.B. "ai_generated/creepy_stories_voice.wav"
                source_path = os.path.join(config.DATA_DIR, os.path.basename(server_rel_path))
                
                if os.path.exists(source_path):
                    shutil.copy(source_path, full_local_path)
                    print(f"[+] Audio successfully localized: {full_local_path}")
                else:
                    print(f"[!] Warning: Audio file created on server but not found at {source_path}")
                    return None

                return full_local_path
            
        except Exception as e:
            print(f"[!] TTS Engine Error: {e}")
            return None
        finally:
            # Optional: Cleanup Trigger für den Voice Service, falls du VRAM sparen willst
            # AIServiceProvider.trigger_cleanup("VOICE", config.API_VOICE_CLEANUP)
            pass

    def get_word_timestamps(self, audio_path):
        """Erstellt präzise Word-Timestamps mit Whisper."""
        print(f"[*] Analyzing timestamps for {audio_path}...")
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
        """Bereinigt Text für bessere TTS-Aussprache."""
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