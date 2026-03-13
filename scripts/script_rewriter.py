import requests
import re
import os

from config import OLLAMA_GENERATE_URL, STRATEGY_LOG, OLLAMA_MODEL, OLLAMA_MODEL_BACKUP
from ollama_provider import OllamaProvider

class ScriptRewriter(OllamaProvider):
    def __init__(self, ai_temp = 0.8, ai_top_p = 1.0, ai_num_ctx = 4096):
        super().__init__()    
        self.ai_temp = ai_temp
        self.ai_top_p = ai_top_p 
        self.ai_num_ctx = ai_num_ctx

    def rewrite(self, raw_text, strategy):
        past_rules = self._read_past_strategy()
        past_rules_injection = ""
        if past_rules:
            past_rules_injection = f"""
            PAST PERFORMANCE DATA:
            The following rules are based on our recent videos that got the most views:
            {past_rules}
            
            INSTRUCTION: Strongly consider applying these rules to maximize engagement.
            """

        models_to_try = [OLLAMA_MODEL]
        if OLLAMA_MODEL_BACKUP:
            models_to_try.append(OLLAMA_MODEL_BACKUP)

        for current_model in models_to_try:
            max_retries = 3
            attempt = 0
            info_message = ""

            while attempt < max_retries:
                attempt += 1
                print(f"\n[*] 🧠 Ollama strategy using model: '{current_model}'... [Attempt {attempt}/{max_retries}]...")

                prompt = f"""
                {info_message}
                You are a master viral TikTok storyteller. Your task is to rewrite the premise into a PUNCHY, highly engaging script for a SHORT-FORM video (approx. 70-90 seconds).
                
                CRITICAL LENGTH LIMITS: 
                - The script MUST be roughly between 120 and 180 words.
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
                
                SPOKEN SCRIPT ONLY:
                """
                
                payload = {
                    "model": current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.ai_temp,
                        "top_p": self.ai_top_p,
                        "num_ctx": self.ai_num_ctx
                    }
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

                    # --- LÄNGEN-CHECK ---
                    word_count = len(script.split())
                    
                    if word_count < 100:
                        print(f"[!] Script too short ({word_count} words). Rejecting...")
                        info_message = f"CRITICAL FEEDBACK ON PREVIOUS ATTEMPT: Your last response was ONLY {word_count} words long. This is WAY TOO SHORT! You MUST write at least 130 words to tell a proper story. Expand the narrative!"
                        continue

                    elif word_count > 200:
                        print(f"[!] Script too long ({word_count} words). Rejecting...")
                        info_message = f"CRITICAL FEEDBACK ON PREVIOUS ATTEMPT: Your last response was {word_count} words long. This is TOO LONG! You MUST condense the story and keep it STRICTLY under 160 words, but ensure it still has a proper ending/cliffhanger!"
                        continue

                    else:
                        # Perfekte Länge erreicht!
                        print(f"[+] Script generated successfully with {word_count} words!\n")
                        return script
                    
                except requests.exceptions.HTTPError as err:
                    # HIER PASSIERT DIE MAGIE BEIM OUT-OF-MEMORY FEHLER
                    print(f"[!] HTTP Error with model '{current_model}': {err}")
                    print(f"[*] The model likely crashed (Out of Memory/Not pulled).")
                    break
                except requests.exceptions.ConnectionError:
                    print("[!] ERROR: Could not connect to Ollama. Service might be down.")
                    return None
                except Exception as e:
                    print(f"[!] An error occurred: {e}")
                    continue

            print(f"[-] Model '{current_model}' failed to generate a valid script.")

        # Wenn die while-Schleife nach 3 Versuchen endet, geben wir auf.
        print(f"[!] ERROR: All models exhausted. Could not generate a script.")
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

    # 1. Wir bauen uns eine Fake-Strategie für den Test
    @dataclasses.dataclass
    class MockStrategy:
        hook_style: str
        voice: str
        folder_name: str
        search_query: str
        caption: str
        tags: str

        # Das wird aufgerufen, wenn im Prompt {strategy} steht
        def __str__(self):
            return f"Hook Style: {self.hook_style} | Voice: {self.voice}"

    test_strategy = MockStrategy(
        hook_style="Controversial/Angry",
        voice="af_bella",
        folder_name="satisfying_slime",
        search_query="satisfying kinetic sand 4k",
        caption="Is she the asshole here? 🚩",
        tags="#aita #storytime #drama"
    )

    # 2. Eine typische, rohe Reddit-Story (ca. 75 Wörter)
    # Perfekt, um zu sehen, ob Ollama sie wie gewünscht auf über 100 Wörter streckt!
    raw_reddit_story = """
    My (25F) boyfriend (27M) of 3 years proposed to me yesterday in a fancy restaurant. 
    Instead of a ring box, he slid a printed piece of paper across the table with a QR code on it. 
    When I scanned it, it led to a picture of an NFT of a ring. 
    He said it's the future and actual diamonds are a scam. 
    I got so mad I threw my drink in his face, walked out, and took an Uber home. 
    Now his family is texting me saying I'm ungrateful. Am I?
    """

    # 3. Wir starten den Rewriter 
    # TIPP: Wir übergeben hier direkt ai_temp=0.6, um die Halluzinationen zu killen!
    rewriter = ScriptRewriter(ai_temp=0.6, ai_top_p=0.9)
    
    print("\n[*] Starting ScriptRewriter Test...")
    final_script = rewriter.rewrite(raw_reddit_story, test_strategy)
    
    if final_script:
        print("\n" + "="*60)
        print("✅ FINAL SCRIPT OUTPUT:")
        print("="*60)
        print(final_script)
        print("="*60)
        print(f"📊 Final Word Count: {len(final_script.split())} words")
    else:
        print("\n[❌] Test failed. No script generated after 3 attempts.")