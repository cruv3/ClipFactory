from fastapi import FastAPI, HTTPException
import os
import soundfile as sf
import numpy as np
from kokoro import KPipeline

from request_model import VoiceRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: TTS (Kokoro)")

# INTERNER PFAD (gemappt auf dein Host-System)
DATA_DIR = "/app/data/ai_generated"
os.makedirs(DATA_DIR, exist_ok=True)

def generate_audio(text: str, output_path: str, voice_name: str, speed: float):
    print(f"[*] Kokoro TTS: Initialisiere '{voice_name}' @ {speed}x...")
    
    try:
        # Lang-Code bestimmen (z.B. 'a' für American 'af_bella')
        lang = voice_name[0] 
        pipeline = KPipeline(lang_code=lang, repo_id='hexgrad/Kokoro-82M')

        # Generierung
        generator = pipeline(
            text, 
            voice=voice_name, 
            speed=speed, 
            split_pattern=r'\n+' # Teilt den Text an Zeilenumbrüchen
        )

        all_audio = []
        for _, _, audio in generator:
            all_audio.append(audio)
            
        if not all_audio:
            raise ValueError("Kein Audio generiert.")

        # Audio zusammenfügen und speichern
        final_audio = np.concatenate(all_audio)
        sf.write(output_path, final_audio, 24000)
        
        # --- VRAM & RAM BEREINIGUNG ---
        del pipeline
        del generator
        del all_audio
        del final_audio
        # ------------------------------
        
        return output_path

    except Exception as e:
        print(f"[!] TTS Fehler: {e}")
        cleanup()
        raise e

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "TTS", "gpu": "RTX 3090"}

@app.post("/generate_voice")
async def api_generate_voice(req: VoiceRequest):
    try:
        filename = f"{req.folder_name}_voice.wav"
        output_path = os.path.join(DATA_DIR, filename)
        
        generate_audio(
            text=req.script_text, 
            output_path=output_path, 
            voice_name=req.voice_name, 
            speed=req.speed
        )
        
        return {"status": "success", "rel_path": f"ai_generated/{filename}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))