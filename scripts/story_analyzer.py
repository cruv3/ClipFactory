import json
import requests
import os

from utils import StoryStrategy
from utils import generate_story_id
# WICHTIG: Fallback-Modelle in config.py definieren!
from config import (
    OLLAMA_GENERATE_URL, DATA_DIR, 
    OLLAMA_MODEL, OLLAMA_MODEL_BACKUP 
)
from ollama_provider import OllamaProvider

class StoryAnalyzer(OllamaProvider):
    def __init__(self, ai_temp=0.7, ai_top_p=0.9):
        super().__init__()
        self.available_voices = [
            "am_adam", "am_michael", "am_onyx", "am_echo", 
            "af_bella", "af_heart", "af_nicole", "af_sky", "af_nova",
            "bm_george", "bm_lewis", "bm_daniel", "bf_emma", "bf_alice", 
            "bf_v0isabella"
        ]
        self.ai_temp = ai_temp
        self.ai_top_p = ai_top_p 
    
    def analyzer(self, story_text):      
        prompt = f"""
        Analyze this story and decide the visual and vocal strategy for a VIRAL TikTok/Shorts video.
        
        STORY: "{story_text}"

        TASK:
        1. Select a Voice: Choose from {self.available_voices}. Pick a voice that matches the tone (e.g., deep for scary, energetic for funny/drama).
        
        2. Background Strategy (CRITICAL FOR RETENTION):
           We are making viral "Reddit-style" stories. We DO NOT want cinematic or realistic backgrounds (like restaurants or cafes). They are too boring.
           We ONLY use highly stimulating "Brainrot" or visually satisfying footage to keep viewer retention at 100%.
           
           CHOOSE ONE OF THESE HIGH-RETENTION CATEGORIES based on the story's vibe:
           - If Action/Angry/Crazy -> Choose 'gta5_stunts' (Search: "gta 5 mega ramp car jumping no commentary 4k")
           - If Funny/TIFU/Embarrassing -> Choose 'minecraft_parkour' (Search: "minecraft parkour gameplay no commentary")
           - If Drama/Relationship/Casual -> Choose 'satisfying_slime' or 'kinetic_sand' (Search: "satisfying kinetic sand cutting ASMR no commentary")
           - If Scary/Creepy/Mysterious -> Choose 'nature_drone' or 'liminal_spaces' (Search: "creepy liminal space background loop 4k" or "dark forest drone 4k")
           - If Fast-paced/Chaotic -> Choose 'subway_surfers' (Search: "subway surfers gameplay background no copyright")

           RULES:
           - The 'folder_name' MUST be one of the categories mentioned above.
           - The 'search_query' MUST be a generic brainrot/satisfying search term from the examples above. 
           - NEVER search for the actual content of the story.

        Return ONLY a raw JSON object (no markdown, no backticks, no introduction). Follow this exact structure:
        {{
            "voice": "af_bella",
            "folder_name": "gta5_stunts",
            "search_query": "gta 5 mega ramp car jumping no commentary 4k",
            "reason": "The story is an angry breakup, fast-paced GTA stunts will keep the viewer hooked during the drama.",
            "hook_style": "Controversial",
            "caption": "Wait until the end... 🚩",
            "description": "Crazy storytime! #reddit #storytime #fyp",
            "tags": "#redditstories #drama #storytime"
        }}
        """

        # --- DAS FALLBACK SYSTEM ---
        models_to_try = [OLLAMA_MODEL]
        if OLLAMA_MODEL_BACKUP:
            models_to_try.append(OLLAMA_MODEL_BACKUP)

        for current_model in models_to_try:
            print(f"\n[*] 🧠 Ollama deciding strategy using model: '{current_model}'...")
            
            payload = {
                "model": current_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": self.ai_temp,
                    "top_p": self.ai_top_p
                }
            }

            try:
                response = requests.post(OLLAMA_GENERATE_URL, json=payload)
                response.raise_for_status() 
                
                data = response.json()
                raw_content = data.get("response", "").strip()

                try:
                    parsed_json = json.loads(raw_content)
                except json.JSONDecodeError:
                    start = raw_content.find('{')
                    end = raw_content.rfind('}') + 1
                    parsed_json = json.loads(raw_content[start:end])

                category = parsed_json.get("folder_name", "dynamic_stories")
                # Leerzeichen in Ordnernamen durch Unterstriche ersetzen zur Sicherheit
                category = category.replace(" ", "_").lower() 
                
                unique_id = f"{category}_{generate_story_id()}"
                final_path = os.path.join(DATA_DIR, category, unique_id)

                strategy = StoryStrategy(
                    voice=parsed_json.get("voice", "am_onyx"),
                    hook_style=parsed_json.get("hook_style", "Shocking"),
                    folder_name=category,
                    output_dir=final_path,
                    search_query=parsed_json.get("search_query", "satisfying video no copyright 4k"),
                    reason=parsed_json.get("reason", ""),
                    caption=parsed_json.get("caption", "You won't believe this... #storytime"),
                    description=parsed_json.get("description", "A crazy story that will leave you speechless. #reddit #shorts"),
                    tags=parsed_json.get("tags", "#reddit #storytime #fyp")
                )

                print("\n" + "="*40)
                print(f"🚀 GENERATED STRATEGY (via {current_model}):")
                print("="*40)
                for key, value in strategy.__dict__.items():
                    print(f"{key.upper():<15}: {value}")
                print("="*40 + "\n")

                return strategy
                
            except requests.exceptions.HTTPError as err:
                print(f"[!] HTTP Error with model '{current_model}': {err}")
                print("[*] Model likely out of memory or not installed. Switching to backup...")
                continue # Springt zum nächsten Modell
                
            except requests.exceptions.ConnectionError:
                print("[!] ERROR: Could not connect to Ollama.")
                return None
            except Exception as e:
                print(f"[!] An error occurred with '{current_model}': {e}")
                continue # Springt zum nächsten Modell

        print("[!] ERROR: All models failed to generate a strategy.")
        return None

# --- TEST RUN ---
if __name__ == "__main__":
    analyzer_tool = StoryAnalyzer()

    # Szenario: Eine wütende Restaurant/Tinder-Story
    test_story = """
    I went on a Tinder date and the guy ordered an $80 steak. When the bill came, 
    he went to the bathroom and literally climbed out the window. I had to pay $120 
    for the whole meal.
    """
    
    print("[*] Starting test analysis...")
    analyzer_tool.analyzer(test_story)