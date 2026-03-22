from fastapi import FastAPI, HTTPException
import sys
import os
from pathlib import Path
import torch
from huggingface_hub import hf_hub_download, snapshot_download

# =================================================================
# 1. DYNAMISCHER PFAD-HACK (Findet den Code immer!)
# =================================================================
LTX_DIR = Path("/opt/LTX-2")
if (LTX_DIR / "packages").exists():
    sys.path.insert(0, str(LTX_DIR / "packages" / "ltx-pipelines" / "src"))
    sys.path.insert(0, str(LTX_DIR / "packages" / "ltx-core" / "src"))
else:
    sys.path.insert(0, str(LTX_DIR / "ltx-pipelines" / "src"))
    sys.path.insert(0, str(LTX_DIR / "ltx-core" / "src"))

# =================================================================
# 2. NATIVE IMPORTE (Passend zu deinem geposteten Quellcode)
# =================================================================
from ltx_pipelines.ti2vid_two_stages import TI2VidTwoStagesPipeline
from ltx_core.model.video_vae import TilingConfig, get_video_chunks_number
from ltx_core.components.guiders import MultiModalGuiderParams
from ltx_core.loader import LoraPathStrengthAndSDOps
from ltx_core.quantization import QuantizationPolicy
from ltx_pipelines.utils.media_io import encode_video

from request_model import VideoRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: LTX-2.3 (100% Local)")

DATA_DIR = "/app/data/ai_generated"
os.makedirs(DATA_DIR, exist_ok=True)

pipeline = None

def init_pipeline():
    global pipeline
    if pipeline is not None:
        return

    print("[*] Lade LTX-2.3 Modelle herunter (22B Parameter)...")
    REPO_ID = "Lightricks/LTX-2.3"
    ckpt_path = hf_hub_download(repo_id=REPO_ID, filename="ltx-2.3-22b-dev.safetensors")
    lora_path = hf_hub_download(repo_id=REPO_ID, filename="ltx-2.3-22b-distilled-lora-384.safetensors")
    upsampler_path = hf_hub_download(repo_id=REPO_ID, filename="ltx-2.3-spatial-upscaler-x2-1.0.safetensors")

    print("[*] Lade Gemma 3 Text-Encoder herunter...")
    # LTX nutzt das neue Gemma 3 von Google
    gemma_path = snapshot_download(repo_id="google/gemma-3-4b-it")

    print("[*] Initialisiere lokale Pipeline (inklusive Text-Encoder)...")
    pipeline = TI2VidTwoStagesPipeline(
        checkpoint_path=ckpt_path,
        # Lora erwartet laut deinem Code eine Liste mit Objekten:
        distilled_lora=[LoraPathStrengthAndSDOps(path=lora_path, strength=1.0)],
        spatial_upsampler_path=upsampler_path,
        gemma_root=gemma_path,
        loras=[],
        quantization=QuantizationPolicy.fp8_cast() # PFLICHT für die RTX 3090!
    )
    print("[+] Startup komplett! System läuft komplett lokal.")

# Direkt beim Start laden
init_pipeline()

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "LTX-2.3 Local", "gpu": "RTX 3090"}

@app.post("/generate_video")
async def api_generate_video(req: VideoRequest):
    try:
        video_paths = []
        for i, prompt in enumerate(req.scenes):
            print(f"[*] Rendere Szene {i+1} komplett lokal...")
            
            tiling_config = TilingConfig.default()
            num_frames = 121

            # Aufruf exakt wie im __call__ des Quellcodes
            video, audio = pipeline(
                prompt=prompt,
                negative_prompt="shaky, low quality, worst quality, deformed, distorted, static",
                seed=42 + i,
                height=480,
                width=704,
                num_frames=num_frames,
                frame_rate=24.0,
                num_inference_steps=25,
                # Diese Guider-Params erwartet die Pipeline zwingend
                video_guider_params=MultiModalGuiderParams(
                    cfg_scale=3.0, stg_scale=1.0, rescale_scale=0.7, modality_scale=1.0, skip_step=0.0, stg_blocks=[]
                ),
                audio_guider_params=MultiModalGuiderParams(
                    cfg_scale=3.0, stg_scale=1.0, rescale_scale=0.7, modality_scale=1.0, skip_step=0.0, stg_blocks=[]
                ),
                images=[],
                tiling_config=tiling_config,
            )
            
            # Speichern über die native LTX Media-IO Funktion
            output_path = os.path.join(DATA_DIR, f"{req.folder_name}_scene_{i}.mp4")
            chunks = get_video_chunks_number(num_frames, tiling_config)
            
            encode_video(
                video=video,
                fps=24.0,
                audio=audio,
                output_path=output_path,
                video_chunks_number=chunks
            )
            
            print(f"[*] Szene {i+1} fertig!")
            video_paths.append(f"ai_generated/{req.folder_name}_scene_{i}.mp4")
            
            cleanup()

        return {"status": "success", "video_paths": video_paths}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))