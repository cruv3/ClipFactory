import json
import requests
import os

from utils import StoryStrategy, generate_story_id, get_trending_backgrounds
from config import (
    OLLAMA_GENERATE_URL, DATA_DIR, 
    OLLAMA_MODEL, OLLAMA_MODEL_BACKUP, STRATEGY_LOG, VIDEO_HISTORY_JSON
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
        strategy_rules = ""

        if os.path.exists(STRATEGY_LOG):
            with open(STRATEGY_LOG, "r", encoding="utf-8") as f:
                strategy_rules = f.read().strip()

        live_trends = get_trending_backgrounds()
        trends_text = ", ".join(live_trends) if live_trends else ""

        last_search_query = ""

        try:
            with open(VIDEO_HISTORY_JSON, "r", encoding="utf-8") as f:
                history = json.load(f)
                if isinstance(history, list) and len(history) > 0:
                    last_entry = history[-1]
                    last_search_query = last_entry.get("bg_video_query", last_entry.get("bg_video_query", ""))
        except Exception as e:
            print(f"[!] Warning: Could not read {VIDEO_HISTORY_JSON}: {e}")

        prompt = f"""
        Analyze this story and decide the visual, vocal, and musical strategy for a VIRAL TikTok/Shorts video.
        
        STORY: "{story_text}"

        CHANNEL RULES (BASED ON RECENT DATA):
        {strategy_rules}

        CURRENT TRENDS FOR INSPIRATION: {trends_text}

        TASK:
        1. Select a Voice: Choose from {self.available_voices}. Match the emotion.
        
        2. Background Video Strategy:
           - We ONLY use stimulating ASMR or gameplay (Brainrot style).
           - Create a 'folder_name' and a specific 'search_query' for youtube (Append "no commentary" and "4k").
           - Avoid the last query: {last_search_query}


        3. Action Words: Identify high-impact Power Words for visual shakes.

        4. Background Music Strategy (NEW):
           - Define the mood (e.g., tense, sad, upbeat, suspicious).
           - Create a 'bg_music_query' for YouTube. 
           - CRITICAL: You MUST include "no copyright" or "royalty free" in the query.
           - Examples: "creepy horror ambient no copyright", "lofi chill hip hop royalty free", "sad cinematic piano no copyright".

        5. Shorts Tagging Strategy:
           - Create a string of 6-8 high-performance hashtags.
           - Mix broad tags (#shorts, #storytime) with niche tags (#redditstories, #aita, #datingfails).
           - Always include #shorts and #reddit. 

        Return ONLY a raw JSON object. Follow this exact structure:
        {{
            "voice": "af_bella",
            "voice_speed": 1.25,
            "folder_name": "beamng_crashes",
            "search_query": "beamng drive cliff crashes no commentary 4k",
            "bg_music_query": "suspenseful dark background music no copyright",
            "reason": "The story is chaotic and destructive.",
            "hook_style": "Shocking",
            "caption": "Wait until the end... 🚩",
            "description": "Crazy storytime! #reddit #storytime",
            "tags": "#shorts #redditstories #storytime #datingfail #aita #drama #tinder",
            "action_words": ["STEAK", "WINDOW", "BATHROOM"]
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
                category = category.replace(" ", "_").lower() 
                
                unique_id = f"{category}_{generate_story_id()}"
                final_path = os.path.join(DATA_DIR, category, unique_id)
                
                clamped_speed = min(2.0, max(1.0, parsed_json.get("voice_speed", 1.2)))
                
                strategy = StoryStrategy(
                    voice=parsed_json.get("voice", "am_onyx"),
                    voice_speed=clamped_speed,
                    hook_style=parsed_json.get("hook_style", "Shocking"),
                    folder_name=category,
                    output_dir=final_path,
                    search_query=parsed_json.get("search_query", "satisfying video no copyright 4k"),
                    reason=parsed_json.get("reason", ""),
                    caption=parsed_json.get("caption", "You won't believe this... #storytime"),
                    description=parsed_json.get("description", "A crazy story that will leave you speechless. #reddit #shorts"),
                    tags=parsed_json.get("tags", "#reddit #storytime #fyp"),
                    action_words=parsed_json.get("action_words", ["WTF", "CRAZY", "SHOCK"]),
                    bg_music_query=parsed_json.get("bg_music_query", "ambient background music no copyright")
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