import torch
import gc

def cleanup():
    """Löscht alle Reste aus dem VRAM."""
    gc.collect()
    torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.ipc_collect()
    print("[*] VRAM gesäubert.")