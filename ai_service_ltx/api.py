from fastapi import FastAPI, HTTPException
import os
import torch

from ltx_pipelines.inference.pipeline import LTXVideoPipeline
from torchvision.io import write_video

from request_model import VideoRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: LTX-Video 2.3")

DATA_DIR = "/app/data/ai_generated"
os.makedirs(DATA_DIR, exist_ok=True)

def render_scenes(prompts: list, folder_name: str):
    print("[*] Initialisiere LTX-2.3 (Lightricks/LTX-2.3)...")
    
    pipe = LTXVideoPipeline.from_pretrained(
        "Lightricks/LTX-2.3", 
        torch_dtype=torch.bfloat16
    ).to("cuda")
    
    try:
        pipe.enable_model_cpu_offload() 
    except AttributeError:
        print("[!] enable_model_cpu_offload nicht nativ unterstützt, lade direkt in VRAM.")
    
    # VAE Tiling (WICHTIG für hohe Auflösungen)
    try:
        pipe.vae.enable_tiling()
    except AttributeError:
        print("[!] VAE Tiling in nativer LTX-Pipeline nicht separat aufrufbar.")

    video_paths = []
    
    try:
        for i, prompt in enumerate(prompts):
            print(f"[*] Rendering Scene {i+1}/{len(prompts)}...")
    
            
            output = pipe(
                prompt=prompt, 
                num_frames=121, 
                num_inference_steps=30, # 30 bis 40 ist optimal
                guidance_scale=3.5,
                height=704,
                width=480 
            )
            
            video_tensor = output.video if hasattr(output, 'video') else output.frames[0]
            
            file_name = f"{folder_name}_scene_{i}.mp4"
            path = os.path.join(DATA_DIR, file_name)
            
            write_video(path, video_tensor, fps=24)
            print(f"[*] Szene {i+1} gespeichert unter {path}")
            
            # Relativen Pfad für die Factory speichern
            video_paths.append(f"ai_generated/{file_name}")

        # --- VRAM BEREINIGUNG ---
        del pipe
        cleanup()
        # ------------------------
        
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
    return {"status": "online", "service": "LTX-Video 2.3", "gpu": "RTX 3090"}

@app.post("/generate_video")
async def api_generate_video(req: VideoRequest):
    try:
        paths = render_scenes(req.scenes, req.folder_name)
        
        if not paths:
            raise HTTPException(status_code=500, detail="Video rendering returned empty.")
            
        return {"status": "success", "video_paths": paths}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))