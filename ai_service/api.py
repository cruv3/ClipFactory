from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os

# Deine Module laden
from modules.llm_handler import generate_script
from modules.tts_handler import generate_voice
from modules.video_handler import render_scenes
from modules.vram_manager import cleanup
from request_model import ScriptRequest, VideoRequest, VoiceRequest

app = FastAPI(title="AI Director API")

# --- DATA CONFIG ---
DATA_DIR = "/app/data/ai_generated"
os.makedirs(DATA_DIR, exist_ok=True)

# --- ENDPUNKTE ---

@app.get("/health")
async def health_check():
    return {"status": "online", "gpu": "RTX 3090", "vram_free": "Ready"}

@app.post("/cleanup")
async def manual_cleanup():
    """Falls du manuell den Speicher leeren willst."""
    cleanup()
    return {"message": "VRAM cleaned"}

@app.post("/generate_script")
async def api_generate_script(req: ScriptRequest):
    try:
        print(f"[*] Request erhalten: Generiere Skript mit {req.model_id}")
        
        script_data = generate_script(
            raw_content=req.prompt, 
            model_id=req.model_id
        )
        
        if script_data is None:
            raise HTTPException(status_code=500, detail="LLM Generation failed")
            
        return {"status": "success", "data": script_data}
        
    except Exception as e:
        print(f"[!] API Error: {e}")
        cleanup()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_voice")
async def api_generate_voice(req: VoiceRequest):
    try:
        # Speicherpfad definieren
        audio_path = os.path.join(DATA_DIR, f"{req.folder_name}_voice.wav")
        
        # Generierung ohne automatischen VRAM-Cleanup danach
        path = generate_voice(
            text=req.script_text, 
            output_path=audio_path, 
            voice_name=req.voice_name, 
            speed=req.speed
        )
        
        if not path:
            raise HTTPException(status_code=500, detail="Voice generation failed")
            
        return {"status": "success", "audio_path": path}
        
    except Exception as e:
        print(f"[!] API Error: {e}")
        cleanup()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_video")
async def api_generate_video(req: VideoRequest):
    try:
        video_paths = render_scenes(req.scenes, req.folder_name, DATA_DIR)
        return {"status": "success", "video_paths": video_paths}
    except Exception as e:
        print(f"[!] API Error: {e}")
        cleanup()
        raise HTTPException(status_code=500, detail=str(e))