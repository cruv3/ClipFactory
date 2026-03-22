import json
import requests
import os

from utils import StoryStrategy, generate_story_id, get_trending_backgrounds
from config import (
    DATA_DIR, 
    OLLAMA_MODEL, OLLAMA_MODEL_BACKUP, STRATEGY_LOG, VIDEO_HISTORY_JSON,
    USE_RTX_XX90, LLM_MODEL, API_GENERATE_SCRIPT
)
from scripts.ai_service_provider import AIServiceProvider
from story_analyzer_utils.generate_prompt import generate_prompt

class StoryAnalyzer(AIServiceProvider):
    def __init__(self, ai_temp=0.7, ai_top_p=0.9):
        # Ruft den Health-Check für den RTX 3090 Service auf
        super().__init__()
        
        # Diese Liste wird im Classic-Mode an den Prompt übergeben
        self.available_voices = [
            "af_bella", "am_adam", "af_sky", "af_nicole", 
            "am_michael", "bf_isabella", "bm_george"
        ]
        self.ai_temp = ai_temp
        self.ai_top_p = ai_top_p

    def analyzer(self, story_text):      
        print(f"[*] Starting Analysis (Hardware Mode: {'RTX 3090 / LTX' if USE_RTX_XX90 else '1660 Ti / Classic'})")

        prompt = generate_prompt(
            story_text=story_text,
            use_rtx_3090=USE_RTX_XX90,
            strategy_log=STRATEGY_LOG,
            video_history_path=VIDEO_HISTORY_JSON
        )
            
        payload = {
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.ai_temp,
                "top_p": self.ai_top_p
            }
        }

        try:
            response = requests.post(API_GENERATE_SCRIPT, json=payload, timeout=120)
            response.raise_for_status()

            raw_content = response.json().get("response", "").strip()
            parsed_json = json.loads(raw_content)

            category = parsed_json.get("folder_name", "master_clips").replace(" ", "_").lower()
            unique_id = f"{category}_{generate_story_id()}"
            final_path = os.path.join(DATA_DIR, category, unique_id)

            strategy = StoryStrategy(
                voice=parsed_json.get("voice", "af_bella"),
                voice_speed=min(2.0, max(1.0, parsed_json.get("voice_speed", 1.25))),
                hook_style=parsed_json.get("hook_style", "Dramatic"),
                folder_name=category,
                output_dir=final_path,
                search_query=parsed_json.get("search_query", ""),
                prompts_scene=parsed_json.get("prompts_scene", []), 
                bg_music_query=parsed_json.get("bg_music_query", "no copyright music"),
                reason=parsed_json.get("reason", "Master decision"),
                caption=parsed_json.get("caption", ""),
                description=parsed_json.get("description", ""),
                tags=parsed_json.get("tags", ""),
                action_words=parsed_json.get("action_words", [])
            )

            return strategy

        except Exception as e:
            print(f"[!] Critical Error in Master Intelligence: {e}")
            return None

# --- TEST RUN ---
if __name__ == "__main__":
    analyzer_tool = StoryAnalyzer()\
    
    test_story = """
    AITA for 'accidentally' revealing my sister's pregnancy at her own wedding?... 
    Wait, before you judge me... hear the whole story. 
    My sister, Sarah, has always been the golden child. She literally stole my college fund to pay for her "dream wedding" in Italy. 
    So, there I was... standing at the altar as her maid of honor. 
    The room was silent, filled with expensive flowers and 200 judgmental guests. 
    I looked at her shimmering white dress - the one MY education paid for - and I just... snapped. 
    Instead of the planned speech, I leaned into the microphone and said: 
    'I am so happy for Sarah... especially since she’s finally giving our parents the grandchild they've wanted for months!' 
    The silence was DEAFENING. My mother fainted. Sarah’s face went from white to purple in two seconds. 
    The kicker? Her new husband... had NO idea she was pregnant. 
    Now the whole family is calling me a monster. But honestly? I've never felt better. 
    So... am I the jerk here?
    """
    
    print(f"[*] Starting Master-Analysis with {len(test_story.split())} words...")
    strategy = analyzer_tool.analyzer(test_story)

    if strategy:
        print("\n" + "—"*50)
        print(f"🚀 MASTER STRATEGY READY")
        print(f"VOICE: {strategy.voice} (Speed: {strategy.voice_speed})")
        print(f"MOOD: {strategy.reason}")
        
        if strategy.prompts_scene:
            print(f"VISUALS: {len(strategy.prompts_scene)} AI-Scenes generated.")
            for i, scene in enumerate(strategy.prompts_scene[:3]): # Zeige nur die ersten 3
                print(f"  Scene {i+1}: {scene[:80]}...")
        else:
            print(f"VISUALS: Classic Mode (Search: {strategy.search_query})")
        print("—"*50)