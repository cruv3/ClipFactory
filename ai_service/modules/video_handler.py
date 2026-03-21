import os
import torch
from diffusers import LTX2Pipeline
from diffusers.utils import export_to_video

def render_scenes(prompts, folder_name, data_dir):
    print("[*] Lade LTX-2.3 (22B)...")
    pipe = LTX2Pipeline.from_pretrained(
        "Lightricks/ltx-2.3-22b-dev", 
        torch_dtype=torch.bfloat16
    ).to("cuda")
    
    pipe.enable_model_cpu_offload() # Wichtig für 22B auf 24GB VRAM
    pipe.vae.enable_tiling()

    paths = []
    for i, p in enumerate(prompts):
        print(f"[*] Rendering Scene {i+1}...")
        video = pipe(prompt=p, num_frames=121, num_inference_steps=40).frames[0]
        
        path = os.path.join(data_dir, f"{folder_name}_{i}.mp4")
        export_to_video(video, path, fps=24)
        paths.append(path)

    del pipe
    return paths