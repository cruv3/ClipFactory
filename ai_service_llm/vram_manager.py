import torch
import gc

def cleanup():
    """Zwingt die GPU, den Speicher sofort freizugeben."""
    print("[*] 🧹 LLM VRAM Cleanup...")
    gc.collect()
    if torch.cuda.is_available():
        with torch.cuda.device('cuda'):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    print("[+] LLM VRAM ist frei.")