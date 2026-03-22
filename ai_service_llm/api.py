import os
os.environ["BNB_CUDA_VERSION"] = "130"

import re
from fastapi import FastAPI, HTTPException
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from request_model import ScriptRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: LLM (Gemma)")

def generate_text(prompt: str, model_id: str) -> str:
    cache_dir = "/models"
    hf_token = os.getenv("HF_TOKEN")
    
    print(f"[*] Lade Modell: {model_id} in 4-Bit...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16, # Optimiert für RTX 3090
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token, cache_dir=cache_dir)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="auto",
            token=hf_token,
            cache_dir=cache_dir,
            low_cpu_mem_usage=True
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        print(f"[*] Generiere Text (Modell läuft auf {model.device})...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=2048, 
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                pad_token_id=tokenizer.eos_token_id
            )

        full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        json_match = re.search(r"(\{.*?\})", full_text, re.DOTALL)

        if json_match:
            result = json_match.group(1)
            print("[+] Erstes JSON erfolgreich extrahiert.")
        else:
            result = full_text # Fallback
            print("[!] Kein JSON im Output gefunden.")
        
        # --- PRINT ---
        print("\n" + "="*50)
        print("--- LLM RAW OUTPUT ---")
        print(result)
        print("="*50 + "\n")
        # --------------------
        
        # --- DER WICHTIGSTE TEIL: MODELL VERNICHTEN ---
        del inputs
        del outputs
        del model
        del tokenizer
        # ----------------------------------------------
        
        return result

    except Exception as e:
        print(f"[!] Fehler bei der Generierung: {e}")
        cleanup()
        raise e

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "LLM", "gpu": "RTX 3090"}

@app.post("/cleanup")
async def force_cleanup():
    cleanup()
    return {"status": "success", "message": "VRAM cleared"}

@app.post("/generate_script")
async def api_generate_script(req: ScriptRequest):
    try:        
        script = generate_text(req.prompt, req.model_id)
        
        return {"status": "success", "data": script}
        
    except Exception as e:
        cleanup()
        raise HTTPException(status_code=500, detail=str(e))