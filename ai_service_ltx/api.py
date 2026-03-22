from fastapi import FastAPI, HTTPException
import os
import torch
from huggingface_hub import hf_hub_download
import torchvision.io as io

# SAUBERER IMPORT (Da wir es via Pip installiert haben!)
from ltx_pipelines.ti2vid_two_stages import TI2VidTwoStagesPipeline
from ltx_core.tiling import TilingConfig

from request_model import VideoRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: LTX-2.3 (100% Local)")

DATA_DIR = "/app/data/ai_generated"
os.makedirs(DATA_DIR, exist_ok=True)

# Modell-Dateien
REPO_ID = "Lightricks/LTX-2.3"
CKPT_FILE = "ltx-2.3-22b-dev.safetensors"
LORA_FILE = "ltx-2.3-22b-distilled-lora-384.safetensors"
UPSAMPLER_FILE = "ltx-2.3-spatial-upscaler-x2-1.0.safetensors"

pipeline = None

def init_pipeline():
    global pipeline
    if pipeline is not None:
        return

    print("[*] Lade LTX-2 Modelle herunter...")
    ckpt_path = hf_hub_download(repo_id=REPO_ID, filename=CKPT_FILE)
    lora_path = hf_hub_download(repo_id=REPO_ID, filename=LORA_FILE)
    upsampler_path = hf_hub_download(repo_id=REPO_ID, filename=UPSAMPLER_FILE)

    print("[*] Initialisiere lokale Pipeline (INKLUSIVE Text-Encoder)...")
    # Indem wir gemma_root=None weglassen, zwingen wir die Pipeline, 
    # den Text-Encoder lokal zu laden!
    pipeline = TI2VidTwoStagesPipeline(
        checkpoint_path=ckpt_path,
        distilled_lora_path=lora_path,
        distilled_lora_strength=1.0,
        spatial_upsampler_path=upsampler_path,
        loras=[],
        fp8transformer=True, # Extrem wichtig, damit die RTX 3090 das überlebt!
        local_files_only=False
    )
    print("[+] Startup komplett! System läuft zu 100% lokal.")

# Modell beim Start laden
init_pipeline()

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "LTX-2.3 Local", "gpu": "RTX 3090"}

@app.post("/generate_video")
async def api_generate_video(req: VideoRequest):
    try:
        video_paths = []
        for i, prompt in enumerate(req.scenes):
            print(f"[*] Rendere Szene {i+1} komplett lokal auf RTX 3090...")
            
            output_path = os.path.join(DATA_DIR, f"{req.folder_name}_scene_{i}.mp4")
            
            # Da der Cloud-Text-Encoder weg ist, übergeben wir einfach nur den Prompt!
            pipeline(
                prompt=prompt,
                negative_prompt="shaky, low quality, worst quality, deformed, distorted, static",
                output_path=output_path,
                seed=42 + i,
                height=480,
                width=704,
                num_frames=121,
                frame_rate=24.0,
                num_inference_steps=25,
                cfg_guidance_scale=3.0,
                images=[],
                tiling_config=TilingConfig.default(),
            )
            
            print(f"[*] Szene {i+1} fertig!")
            video_paths.append(f"ai_generated/{req.folder_name}_scene_{i}.mp4")
            
            cleanup()

        return {"status": "success", "video_paths": video_paths}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))