import requests
import re
import os

from config import OLLAMA_GENERATE_URL, STRATEGY_LOG, OLLAMA_MODEL
from ollama_provider import OllamaProvider

class ScriptRewriter(OllamaProvider):
    def __init__(self):
        super().__init__()       

    def rewrite(self, raw_text, strategy):
        print(f"\n[*] 🧠 Ollama is rewriting the script (Hook Style: {strategy.hook_style})...")
        
        past_rules = self._read_past_strategy()
        past_rules_injection = ""
        if past_rules:
            past_rules_injection = f"""
            PAST PERFORMANCE DATA:
            The following rules are based on our recent videos that got the most views:
            {past_rules}
            
            INSTRUCTION: Strongly consider applying these rules to maximize engagement. However, if you feel these rules completely ruin the context, tone, or narrative of the specific story provided below, use your best creative judgment to deviate.
            """
        
        prompt = f"""
        You are a master viral storyteller. Your task is to transform the short premise into a FULL, highly cinematic narrative script for a 60-90 second video.
        
        LENGTH CRITERIA (CRITICAL): 
        - The script MUST be at least 250 words long.
        - You MUST write a minimum of 15 to 20 sentences.
        - Do not rush the narrative. Expand on every single detail to stretch the duration.

        NARRATIVE ARCHITECTURE (Mandatory pacing):
        1. THE HOOK: A devastating or terrifying first sentence (Style: {strategy.hook_style}).
        2. THE SCENE BUILDING: Do not skip this! Spend at least 4 sentences describing the room, the lighting, the temperature, and the smell. Make it highly immersive.
        3. THE SLOW ESCALATION: Stretch the suspense. Describe the physical reactions of the narrator (heartbeat, breathing, sweating) and their internal monologue before the main event happens.
        4. THE FINAL BLOW: A shocking conclusion or haunting cliffhanger.

        STRICT STYLE RULES:
        - Output ONLY the spoken script. No titles, no formatting.
        - NO intros like "Here is your script" or "Sure".
        - Start immediately with the hook.
        - Use "I" (first-person perspective).
        - Invent heavy sensory details, specific objects in the room, or internal thoughts to ensure the script is extremely long and detailed.

        STRATEGY CONTEXT:
        {strategy}
        
        {past_rules_injection}

        Original short premise to expand upon:
        {raw_text}
        
        SPOKEN SCRIPT ONLY (Start immediately with the hook. Remember: Expand details heavily to reach the length!):
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
            
            # --- NEU: KI-Gequatsche am Anfang killen ---
            # Sucht nach Sätzen wie "Here is your script:", "Sure!", "Certainly, here is the rewritten story\n\n"
            # am GANZ ANFANG des Textes und löscht sie.
            ai_chatter_pattern = r'^(?:sure[,! ]|certainly[,! ]|of course[,! ]|here is |here\'s ).{0,100}?(?:script|story|rewrite|rewritten|narrative).*?[:\n]+'
            script = re.sub(ai_chatter_pattern, '', script, flags=re.IGNORECASE).strip()
            # -------------------------------------------
            
            # Entfernt alle Arten von Klammern (Regieanweisungen)
            script = re.sub(r'\(.*?\)', '', script)
            script = re.sub(r'\[.*?\]', '', script)
            script = re.sub(r'\*.*?\*', '', script) # Entfernt auch *flüstert* etc.
            script = script.replace(' -', '.')  # Killt alle "
            script = script.replace('"', '')  # Killt alle "
            script = script.replace(':', ',') # Macht aus Doppelpunkten ein Komma (für eine saubere Sprechpause)
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
    import dataclasses

    @dataclasses.dataclass
    class MockStrategy:
        voice: str
        folder_name: str
        search_query: str
        reason: str
        hook_style: str
        caption: str
        description: str
        tags: str
        output_dir: str = "data/test_output"

    strategy = MockStrategy(
        voice="af_sky",
        folder_name="minecraft",
        search_query="minecraft parkour no copyright gameplay",
        reason="High energy parkour fits the shocking narrative twist.",
        hook_style="Shocking",
        caption="My reflection blinked... but I didn't. 😳",
        description="A terrifying discovery in the bathroom mirror leads to a dark realization.",
        tags="#horror #minecraft #storytime #creepy"
    )

    rewriter = ScriptRewriter()
    
    test_story = "Here is a written script, My mirror reflection blinked today, Certainly but I didn't. Now it's smiling, even though I'm crying."
    
    finished_script = rewriter.rewrite(test_story, strategy)
    
    if finished_script:
        print("=== GENERATED SCRIPT ===")
        print(finished_script)
        print(f"\n(Word count: {len(finished_script.split())})")
        print("===============================")