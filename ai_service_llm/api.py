from fastapi import FastAPI, HTTPException
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

from request_model import ScriptRequest
from vram_manager import cleanup

app = FastAPI(title="Microservice: LLM (Gemma)")

def generate_text(prompt: str, model_id: str) -> str:
    cache_dir = "/models"
    hf_token = os.getenv("HF_TOKEN")
    
    print(f"[*] Lade Modell: {model_id} in 4-Bit...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token, cache_dir=cache_dir)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            dtype=torch.bfloat16,
            device_map="auto",
            load_in_4bit=True,
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
                pad_token_id=tokenizer.eos_token_id
            )
            
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
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