from fastapi import FastAPI, HTTPException
import os
import torch
import torchvision.io as io

# NATIVE IMPORTS AUS DEM LTX-2 REPO (Laut deiner Doku)
from ltx_pipelines import TI2VidOneStagePipeline
# Falls Quantization importiert werden muss (oft in utils):
from ltx_pipelines.utils.quantization import QuantizationPolicy 

from request_model import VideoRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: LTX-2.3")

# INTERNER PFAD (gemappt auf dein Host-System)
DATA_DIR = "/app/data/ai_generated"
os.makedirs(DATA_DIR, exist_ok=True)

# WICHTIG: Die Pfade zu den Modellen. 
# Wenn die Pipeline HuggingFace-IDs frisst, super. Ansonsten musst du die 
# .safetensors später in deinen /models Ordner laden.
MODEL_ID = "Lightricks/LTX-2.3" 

def render_scenes(prompts: list, folder_name: str):
    print("[*] Initialisiere LTX-2.3 (Native Pipeline)...")
    
    # 1. Native Pipeline laden + FP8 Optimierung für die RTX 3090!
    # Wie in der Doku beschrieben, nutzen wir fp8_cast, um VRAM zu sparen.
    print("[*] Lade Modell mit FP8 Quantisierung...")
    pipe = TI2VidOneStagePipeline(
        model_name_or_path=MODEL_ID,
        quantization=QuantizationPolicy.fp8_cast(), # Lebensretter für 24GB GPUs!
        device="cuda"
    )
    
    # Optional: Offload, falls die Pipeline das nativ unterstützt
    try:
        pipe.enable_model_cpu_offload()
    except AttributeError:
        pass

    video_paths = []
    
    try:
        for i, prompt in enumerate(prompts):
            print(f"[*] Rendering Scene {i+1}/{len(prompts)}...")
            
            # 2. Rendern mit der One-Stage Pipeline
            # 121 Frames, 480x704 (durch 32 teilbar)
            output = pipe(
                prompt=prompt, 
                num_frames=121, 
                num_inference_steps=30, # Laut Doku mit Gradient Estimation auf 20-30 reduzierbar
                guidance_scale=3.5,
                height=704,
                width=480 
            )
            
            # Output extrahieren (kann ein Tensor oder ein Objekt sein)
            video_tensor = output.video if hasattr(output, 'video') else output
            
            # Speichern mit torchvision
            file_name = f"{folder_name}_scene_{i}.mp4"
            path = os.path.join(DATA_DIR, file_name)
            
            # Torchvision write_video erwartet [T, H, W, C] und Werte 0-255
            io.write_video(path, video_tensor, fps=24)
            print(f"[*] Szene {i+1} gespeichert unter {path}")
            
            video_paths.append(f"ai_generated/{file_name}")

        # VRAM aufräumen
        del pipe
        cleanup()
        
        return video_paths

    except Exception as e:
        print(f"[!] Fehler beim Rendern der Szene {i+1}: {e}")
        try:
            del pipe
        except:
            pass
        cleanup()
        raise e

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "LTX-2.3 (Native)", "gpu": "RTX 3090"}

@app.post("/generate_video")
async def api_generate_video(req: VideoRequest):
    try:
        paths = render_scenes(req.scenes, req.folder_name)
        if not paths:
            raise HTTPException(status_code=500, detail="Video rendering returned empty.")
        return {"status": "success", "video_paths": paths}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))