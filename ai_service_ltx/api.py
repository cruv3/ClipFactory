from fastapi import FastAPI, HTTPException
import os
import torch
from diffusers import LTXVideoPipeline
from diffusers.utils import export_to_video

from request_model import VideoRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: LTX-Video")

# INTERNER PFAD (gemappt auf dein Host-System)
DATA_DIR = "/app/data/ai_generated"
os.makedirs(DATA_DIR, exist_ok=True)

def render_scenes(prompts: list, folder_name: str):
    print("[*] Initialisiere LTX-2.3 (Lightricks/LTX-Video)...")
    
    # 1. Pipeline laden (bfloat16 ist Pflicht für RTX 3090)
    pipe = LTXVideoPipeline.from_pretrained(
        "Lightricks/LTX-Video", 
        torch_dtype=torch.bfloat16
    ).to("cuda")
    
    # 2. VRAM Optimierungen (Ohne das hier crasht deine 24GB Karte!)
    pipe.enable_model_cpu_offload() 
    pipe.vae.enable_tiling()

    video_paths = []
    
    try:
        for i, prompt in enumerate(prompts):
            print(f"[*] Rendering Scene {i+1}/{len(prompts)}...")
            
            # LTX Rendern (121 Frames = ca. 5 Sekunden bei 24fps)
            # Hochkant-Auflösung (480x704) spart massiv VRAM gegenüber Full HD
            output = pipe(
                prompt=prompt, 
                num_frames=121, 
                num_inference_steps=30, # 30 bis 40 ist der Sweetspot für LTX
                guidance_scale=3.5,
                height=704,
                width=480 
            ).frames[0]
            
            # Speichern
            file_name = f"{folder_name}_scene_{i}.mp4"
            path = os.path.join(DATA_DIR, file_name)
            export_to_video(output, path, fps=24)
            
            # Relativen Pfad für die Factory speichern
            video_paths.append(f"ai_generated/{file_name}")

        # --- VRAM BEREINIGUNG ---
        del pipe
        # ------------------------
        
        return video_paths

    except Exception as e:
        print(f"[!] Fehler beim Rendern der Szene {i+1}: {e}")
        del pipe
        cleanup()
        raise e


@app.get("/health")
async def health_check():
    return {"status": "online", "service": "LTX-Video", "gpu": "RTX 3090"}

@app.post("/generate_video")
async def api_generate_video(req: VideoRequest):
    try:
        paths = render_scenes(req.scenes, req.folder_name)
        
        if not paths:
            raise HTTPException(status_code=500, detail="Video rendering returned empty.")
            
        return {"status": "success", "video_paths": paths}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))