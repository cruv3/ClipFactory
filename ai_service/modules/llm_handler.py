import torch
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from .vram_manager import cleanup

def generate_script(prompt, model_id):
    """
    Generiert das Skript. 
    model_id: Kann beim Aufruf geändert werden (z.B. gemma-2-2b für 1660ti).
    """
    print(f"[*] Vorbereitung für Modell: {model_id}")
    cache_dir = "/models"
    hf_token = os.getenv("HF_TOKEN")
    
    try:
        # Tokenizer & Modell laden
        tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir, token=hf_token)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            load_in_4bit=True,
            cache_dir=cache_dir,
            token=hf_token,
            low_cpu_mem_usage=True
        )

        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        print("[*] Generiere Skript...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7
            )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)

        del inputs
        return result

    except Exception as e:
        print(f"[!] Fehler im LLM-Modul: {e}")
        return None