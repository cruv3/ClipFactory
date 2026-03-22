import json
import requests
import os

from utils import StoryStrategy, generate_story_id
import config
from story_analyzer_utils.generate_prompt import generate_prompt

class StoryAnalyzer:
    def __init__(self):
        self.max_retries = 3

    def analyzer(self, story_text):      
        print(f"[*] Starting Analysis (Hardware Mode: {'RTX 3090' if config.USE_RTX_XX90 else 'Classic'})")
        
        # Modelle definieren
        models_to_try = [config.LLM_MODEL]
        if config.LLM_MODEL_BACKUP:
            models_to_try.append(config.LLM_MODEL_BACKUP)

        info_feedback = ""

        for current_model in models_to_try:
            attempt = 0
            while attempt < self.max_retries:
                attempt += 1
                print(f"[*] Analyzing with '{current_model}' (Attempt {attempt}/{self.max_retries})...")

                # Prompt generieren (inkl. potenziellem Feedback)
                prompt = generate_prompt(
                    story_text=story_text,
                    use_rtx_XX90=config.USE_RTX_XX90,
                    strategy_log=config.STRATEGY_LOG,
                    video_history_path=config.VIDEO_HISTORY_JSON,
                    word_min=config.WORD_MIN,
                    word_max=config.WORD_MAX
                )
                
                if info_feedback:
                    prompt = f"{info_feedback}\n\n{prompt}"

                payload = {
                    "model": current_model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "num_ctx": 8192
                    },
                    "keep_alive": 0
                }

                try:
                    response = requests.post(config.API_GENERATE_SCRIPT, json=payload, timeout=7200)
                    response.raise_for_status()
                    response_data = response.json()
                    raw_content = response_data.get("response", "").strip()

                    parsed_json = json.loads(raw_content)

                    # --- QUALITÄTS CHECK (Nur im RTX Modus wichtig) ---
                    if config.USE_RTX_XX90:
                        timeline = parsed_json.get("script_timeline", [])
                        full_script = " ".join([b.get("narration", "") for b in timeline])
                        word_count = len(full_script.split())

                        if word_count < config.WORD_MIN:
                            print(f"[!] REJECTED: Script too short ({word_count} words). Min is {config.WORD_MIN}.")
                            info_feedback = f"CRITICAL FEEDBACK: Your previous response was only {word_count} words. THAT IS TOO SHORT! You MUST expand the narration in each scene to reach at least {config.WORD_MIN} words total. Be more descriptive!"
                            continue # Nächster Versuch

                        if word_count > config.WORD_MAX:
                            print(f"[!] REJECTED: Script too long ({word_count} words). Max is {config.WORD_MAX}.")
                            info_feedback = f"CRITICAL FEEDBACK: Your previous response was {word_count} words. That exceeds the limit of {config.WORD_MAX}. Condense it slightly while keeping all scenes."
                            continue

                        print(f"[+] Quality Check passed! ({word_count} words, {len(timeline)} scenes)")

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
                        script_timeline=parsed_json.get("script_timeline", []), 
                        bg_music_query=parsed_json.get("bg_music_query", "no copyright music"),
                        reason=parsed_json.get("reason", "Master decision"),
                        caption=parsed_json.get("caption", ""),
                        description=parsed_json.get("description", ""),
                        tags=parsed_json.get("tags", ""),
                        action_words=parsed_json.get("action_words", [])
                    )
                    return strategy

                except json.JSONDecodeError:
                    print(f"[!] JSON Error from {current_model}. Retrying...")
                    info_feedback = "CRITICAL: Your last response was not a valid JSON. Ensure you ONLY output the JSON object."
                    continue
                except Exception as e:
                    print(f"[!] Error with {current_model}: {e}")
                    break

        print("[!] FATAL: All models and retries failed.")
        return None

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
        print("\n" + "="*70)
        print(f"🚀 MASTER STRATEGY READY: {strategy.folder_name.upper()}")
        print("="*70)
        
        print(f"🎙️ AUDIO & VIBE:")
        print(f"   - Voice:       {strategy.voice} (Speed: {strategy.voice_speed})")
        print(f"   - Music Query: {strategy.bg_music_query}")
        print(f"   - Mood/Reason: {strategy.reason}")
        print("-" * 70)
        
        print(f"📱 SOCIAL MEDIA META:")
        print(f"   - Caption:     {strategy.caption}")
        print(f"   - Hook Style:  {strategy.hook_style}")
        print(f"   - Tags:        {strategy.tags}")
        print(f"   - Action Words:{', '.join(strategy.action_words) if strategy.action_words else 'None'}")
        print(f"   - Output Dir:  {strategy.output_dir}")
        print("-" * 70)
        
        if strategy.script_timeline:
            print(f"🎬 VISUALS (High-End AI Mode - {len(strategy.script_timeline)} Scenes):")
            for i, scene in enumerate(strategy.script_timeline): 
                print(f"   [Scene {i+1}]:\n      {scene}\n")
        else:
            print(f"🎮 VISUALS (Classic Mode):")
            print(f"   - Background Search: {strategy.search_query}")
            
        print("="*70 + "\n")