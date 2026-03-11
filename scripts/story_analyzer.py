import json
import requests
import os

from utils import StoryStrategy
from utils import generate_story_id
from config import (
    OLLAMA_GENERATE_URL, DATA_DIR
)
from ollama_provider import OllamaProvider

class StoryAnalyzer(OllamaProvider):
    def __init__(self):
        self.available_voices = [
            "am_adam", "am_michael", "am_onyx", "am_echo", 
            "af_bella", "af_heart", "af_nicole", "af_sky", "af_nova",
            "bm_george", "bm_lewis", "bm_daniel", "bf_emma", "bf_alice", "bf_isabella"
        ]
    
    def analyzer(self, story_text):
        prompt = f"""
        Analyze this story and decide:
        1. Which voice fits best? (Choices: {self.available_voices})
        2. What background gameplay would fit? (e.g., Minecraft, GTA, League of Legends, etc.)
        3. Which hook style fits best to make this story viral? (e.g., Shocking, Mysterious, Emotional, etc.)
        4. Create a viral CAPTION, a DESCRIPTION, and relevant HASHTAGS.
        
        STORY: "{story_text}"

        Return ONLY a JSON object:
        {{
            "voice": "selected_voice",
            "folder_name": "category",
            "search_query": "youtube search query",
            "reason": "why this fits",
            "hook_style": "style",
            "caption": "Viral hook caption",
            "description": "SEO description",
            "tags": "#hashtag1 #hashtag2 #hashtag3"
        }}

        Example for a horror story:
        {{
            "voice": "am_onyx",
            "folder_name": "horror_woods",
            "search_query": "scary forest amnesia gameplay no commentary 4k no copyright",
            "reason": "The deep onyx voice enhances the scary forest atmosphere.",
            "hook_style": "Shocking",
            "caption": "I was never supposed to find this in the woods... 💀 #scary",
            "description": "A terrifying 3 AM encounter that changed everything. Watch until the end to see what was behind the tree. #horrorstories #redditreadings",
            "tags": "#horror #scary #3am #redditstories #creepy"
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

            # Jetzt Mapping auf die Dataclass (Punkt-Notation statt Keys)
            final_path = os.path.join(DATA_DIR, parsed_json.get("folder_name", "general"), generate_story_id())

            return StoryStrategy(
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