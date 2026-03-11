import requests
import re
import os

from config import OLLAMA_GENERATE_URL, STRATEGY_LOG, OLLAMA_MODEL
from ollama_provider import OllamaProvider

class ScriptRewriter(OllamaProvider):
    def __init__(self):
        super().__init__()       

    def rewrite(self, raw_text, hook_style="Shocking"):
        print(f"\n[*] 🧠 Ollama is rewriting the script (Hook Style: {hook_style})...")
        
        past_rules = self._read_past_strategy()
        strategy_injection = ""
        if past_rules:
            strategy_injection = f"""
            PAST PERFORMANCE DATA:
            The following rules are based on our recent videos that got the most views:
            {past_rules}
            
            INSTRUCTION: Strongly consider applying these rules to maximize engagement. However, if you feel these rules completely ruin the context, tone, or narrative of the specific story provided below, use your best creative judgment to deviate.
            """
        
        prompt = f"""
        You are a master viral storyteller. Your task is to transform the premise into a FULL, highly cinematic narrative script for a 60-90 second video.
        
        WORD COUNT TARGET: 220 - 260 words. (CRITICAL: Do not write less than 200 words).

        NARRATIVE ARCHITECTURE (Mandatory):
        1. THE HOOK (0-5s): A devastating, controversial, or terrifying first sentence (Style: {hook_style}).
        2. THE SETTING (5-30s): Establish the scene. Add intense sensory details. What does it smell like? How cold is the room? Make the listener feel they are THERE.
        3. THE ESCALATION (30-60s): Something goes wrong. Introduce a twist or a realization. Increase the pacing with shorter sentences.
        4. THE FINAL BLOW (60-90s): A shocking conclusion or a haunting cliffhanger. This MUST feel like a complete story arc.

        STRICT STYLE RULES:
        - Output ONLY the spoken script.
        - NO intros like "Here is your script" or "Sure, I can help".
        - NO conversational filler.
        - Start immediately with the hook.
        - Use "I" (first-person perspective).
        - Use punchy, dramatic sentences.
        - ZERO filler, ZERO intros. Start with the hook immediately.
        - Invent names, locations, or specific dialogue if needed to reach the word count and make it immersive.
        
        {strategy_injection}

        Original premise:
        {raw_text}
        
        SPOKEN SCRIPT ONLY (Start immediately with the hook):
        """
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(OLLAMA_GENERATE_URL, json=payload)
            response.raise_for_status()
            
            data = response.json()
            script = data.get("response", "").strip()
            
            # Entfernt alle Arten von Klammern (Regieanweisungen)
            script = re.sub(r'\(.*?\)', '', script)
            script = re.sub(r'\[.*?\]', '', script)
            script = re.sub(r'\*.*?\*', '', script) # Entfernt auch *flüstert* etc.
            
            # Bereinigt doppelte Leerzeichen, die durch Regex entstehen können
            script = " ".join(script.split())

            print("[+] Script generated successfully!\n")
            return script
            
        except requests.exceptions.ConnectionError:
            print("[!] ERROR: Could not connect to Ollama.")
            return None
        except Exception as e:
            print(f"[!] An error occurred: {e}")
            return None

    def _read_past_strategy(self):
        if os.path.exists(STRATEGY_LOG):
            with open(STRATEGY_LOG, "r", encoding="utf-8") as f:
                rules = f.read().strip()
                if rules:
                    return rules
        return None
    
# --- TEST RUN ---
if __name__ == "__main__":
    rewriter = ScriptRewriter()
    
    test_story = "My mirror reflection blinked today, but I didn't. Now it's smiling, even though I'm crying."
    
    finished_script = rewriter.rewrite(test_story, "Shocking")
    
    if finished_script:
        print("=== GENERATED SCRIPT ===")
        print(finished_script)
        print(f"\n(Word count: {len(finished_script.split())})")
        print("===============================")