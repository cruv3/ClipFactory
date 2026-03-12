import json
import requests
import os

from utils import StoryStrategy
from utils import generate_story_id
from config import (
    OLLAMA_GENERATE_URL, DATA_DIR, VIDEO_CHUNKS_DIR
)
from ollama_provider import OllamaProvider

class StoryAnalyzer(OllamaProvider):
    def __init__(self):
        self.available_voices = [
            "am_adam", "am_michael", "am_onyx", "am_echo", 
            "af_bella", "af_heart", "af_nicole", "af_sky", "af_nova",
            "bm_george", "bm_lewis", "bm_daniel", "bf_emma", "bf_alice", 
            "bf_v0isabella"
        ]
    
    def analyzer(self, story_text):

        available_folders = []
        if os.path.exists(VIDEO_CHUNKS_DIR):
            available_folders = [f for f in os.listdir(VIDEO_CHUNKS_DIR) if os.path.isdir(os.path.join(VIDEO_CHUNKS_DIR, f))]

        safe_themes = ["minecraft_parkour", "gta5_stunts", "satisfying_slime", "nature_drone_4k"]

        prompt = f"""
        Analyze this story and decide the visual and vocal strategy.
        
        STORY: "{story_text}"

        TASK:
        1. Select a Voice: Choose from {self.available_voices}.
        
        2. Background Strategy (CRITICAL):
           We need high-retention background footage. 
           Existing folders: {available_folders}
           
           RULES:
           - Use an EXISTING folder if it fits even remotely.
           - If you create a NEW folder, it MUST be a generic gameplay or nature category.
           - NEVER include story-specific keywords (like 'daughter', 'struggle', 'behavior') in the 'folder_name' or 'search_query'.
           - The 'search_query' MUST be for YouTube and should focus on: 'gameplay no commentary', 'parkour 4k', or 'cinematic nature'.
           - PREFERRED THEMES: Minecraft Parkour, GTA 5 Mega Ramp, CS:GO Surfing, Satisfying Kinetic Sand, Nature Drone.
           - These are the safe_themes: {safe_themes}

        Return ONLY a JSON object:
        {{
            "voice": "selected_voice",
            "folder_name": "generic_category_name",
            "search_query": "generic youtube search query (e.g. 'minecraft parkour no commentary 4k')",
            "reason": "short explanation",
            "hook_style": "Shocking/Emotional/etc",
            "caption": "Viral hook caption",
            "description": "SEO description",
            "tags": "#tags"
        }}
        """

        print("[*] Llama 3 is deciding the visual and vocal style...")
        
        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(OLLAMA_GENERATE_URL, json=payload)
            response.raise_for_status() # Throws an error if Ollama is unreachable
            
            data = response.json()
            raw_content = data.get("response", "").strip()

            try:
                parsed_json = json.loads(raw_content)
            except json.JSONDecodeError:
                start = raw_content.find('{')
                end = raw_content.rfind('}') + 1
                parsed_json = json.loads(raw_content[start:end])

            category = parsed_json.get("folder_name", "stories")
            unique_id = f"{category}_{generate_story_id()}"
            final_path = os.path.join(DATA_DIR, category, unique_id)

            strategy = StoryStrategy(
                voice=parsed_json.get("voice", "am_onyx"),
                hook_style=parsed_json.get("hook_style", "Shocking"),
                folder_name=parsed_json.get("folder_name", "stories"),
                output_dir=final_path,
                search_query=parsed_json.get("search_query", "minecraft parkour no copyright"),
                reason=parsed_json.get("reason", ""),
                caption=parsed_json.get("caption", "You won't believe this... #storytime"),
                description=parsed_json.get("description", "A crazy story that will leave you speechless. #reddit #shorts"),
                tags=parsed_json.get("tags", "#reddit #storytime #fyp")
            )

            print("\n" + "="*40)
            print("🚀 GENERATED STORY STRATEGY:")
            print("="*40)
            for key, value in strategy.__dict__.items():
                print(f"{key.upper():<15}: {value}")
            print("="*40 + "\n")

            return strategy
            
        except requests.exceptions.ConnectionError:
            print("[!] ERROR: Could not connect to Ollama.")
            print(f"[!] Is Ollama running in the background? (Check {OLLAMA_GENERATE_URL} in your browser)")
            return None
        except Exception as e:
            print(f"[!] An error occurred: {e}")
            return None

# --- TEST RUN ---
if __name__ == "__main__":
    # Falls StoryStrategy in utils.py definiert ist, stelle sicher, dass sie importiert ist
    # from scripts.utils import StoryStrategy 

    analyzer_tool = StoryAnalyzer()

    # Szenario: Eine gruselige Geschichte
    test_story = """
    I was walking through the woods at 3 AM when I realized 
    the trees were whispering my name. I turned around, 
    but there was nothing but a tall, dark figure with no face.
    """
    
    print("[*] Starting test analysis...")
    analysis = analyzer_tool.analyzer(test_story)

    if analysis:
        print("\n" + "="*30)
        print("🚀 TEST SUCCESSFUL")
        print("="*30)
        # Zugriff über die Dataclass-Attribute
        print(f"Voice:         {analysis.voice}")
        print(f"Hook Style:    {analysis.hook_style}")
        print(f"Folder:       {analysis.folder_name}")
        print(f"YT Query:     {analysis.search_query}")
        print(f"Reasoning:    {analysis.reason}")
        print("="*30 + "\n")
    else:
        print("\n--- TEST FAILED (No Strategy Object) ---")