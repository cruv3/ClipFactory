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
            
            INSTRUCTION: Strongly consider applying these rules to maximize engagement.
            """
        
        # --- DER NEUE, LIMITIERENDE PROMPT ---
        prompt = f"""
        You are a master viral TikTok storyteller. Your task is to rewrite the premise into a PUNCHY, highly engaging script for a SHORT-FORM video (maximum 50-60 seconds).
        
        CRITICAL LENGTH LIMITS: 
        - The script MUST be exactly between 130 and 160 words. DO NOT exceed 160 words under any circumstances!
        - Keep sentences short, punchy, and easy to speak. No long, complex paragraphs.
        - Cut the fluff. Get straight to the point.

        NARRATIVE ARCHITECTURE:
        1. THE HOOK (First 3 seconds): A devastating, terrifying, or highly controversial first sentence (Style: {strategy.hook_style}).
        2. THE ESCALATION: Build tension immediately. Give 1-2 sensory details (like a sound or a cold sweat), but do not over-explain.
        3. THE FINAL BLOW (Cliffhanger): End abruptly with a shocking revelation or a thought-provoking question that makes the viewer want to re-watch or comment.

        STRICT STYLE RULES:
        - Output ONLY the spoken script. No titles, no formatting, no emojis.
        - NO conversational AI intros (e.g., "Here is your script").
        - Start immediately with the hook.
        - Use "I" (first-person perspective).

        STRATEGY CONTEXT:
        {strategy}
        
        {past_rules_injection}

        Original premise to rewrite and condense:
        {raw_text}
        
        SPOKEN SCRIPT ONLY (130-160 words MAX. Start directly with the hook!):
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
            
            # KI-Gequatsche am Anfang killen
            ai_chatter_pattern = r'^(?:sure[,! ]|certainly[,! ]|of course[,! ]|here is |here\'s ).{0,100}?(?:script|story|rewrite|rewritten|narrative).*?[:\n]+'
            script = re.sub(ai_chatter_pattern, '', script, flags=re.IGNORECASE).strip()
            
            # Regieanweisungen und Sonderzeichen entfernen
            script = re.sub(r'\(.*?\)', '', script)
            script = re.sub(r'\[.*?\]', '', script)
            script = re.sub(r'\*.*?\*', '', script) 
            script = script.replace(' -', '.')  
            script = script.replace('"', '')  
            script = script.replace(':', ',') 
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