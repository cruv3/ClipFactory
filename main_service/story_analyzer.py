import json
import requests
import os

from utils import StoryStrategy, generate_story_id
import config
from main_service.story_analyzer_utils.ai_service_provider import AIServiceProvider
from story_analyzer_utils.generate_prompt import generate_prompt

class StoryAnalyzer:
    def __init__(self):
        pass

    def analyzer(self, story_text):      
        print(f"[*] Starting Analysis (Hardware Mode: {'RTX XX90' if config.USE_RTX_XX90 else '1660 Ti / Classic'})")

        prompt = generate_prompt(
            story_text=story_text,
            use_rtx_XX90=config.USE_RTX_XX90,
            strategy_log=config.STRATEGY_LOG,
            video_history_path=config.VIDEO_HISTORY_JSON
        )
            
        # ==============================================================
        # 2. PAYLOAD: Angepasst an dein FastAPI 'ScriptRequest' Model
        # ==============================================================
        payload = {
            "model": config.LLM_MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "keep_alive": 0
        }

        try:
            response = requests.post(config.API_GENERATE_SCRIPT, json=payload, timeout=7200)
            response.raise_for_status()
            response_data = response.json()
            raw_content = response_data.get("response", "").strip()

            parsed_json = json.loads(raw_content)

            category = parsed_json.get("folder_name", "master_clips").replace(" ", "_").lower()
            unique_id = f"{category}_{generate_story_id()}"
            final_path = os.path.join(config.DATA_DIR, category, unique_id)

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

        except json.JSONDecodeError as e:
            print(f"[!] JSON Error (should not happen with Ollama format='json'): {e}")
            print(f"[*] Raw LLM Content was: {raw_content}")
            return None
        except Exception as e:
            print(f"[!] Critical Error in Master Intelligence: {e}")
            return None

        finally:
            print("[*] Analysis finished. (VRAM managed by Ollama)")


# --- TEST RUN ---
if __name__ == "__main__":
    analyzer_tool = StoryAnalyzer()
    
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
            for i, scene in enumerate(strategy.prompts_scene[:3]): 
                print(f"  Scene {i+1}: {scene[:80]}...")
        else:
            print(f"VISUALS: Classic Mode (Search: {strategy.search_query})")
        print("—"*50)