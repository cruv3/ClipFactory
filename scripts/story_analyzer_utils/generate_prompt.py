import os
import json
from .trending import get_trending_backgrounds

def generate_prompt(story_text, use_rtx_3090, strategy_log, video_history_path):
    """
    Erstellt den finalen System-Prompt basierend auf der verfügbaren Hardware.
    """
    strategy_rules = ""
    if os.path.exists(strategy_log):
        with open(strategy_log, "r", encoding="utf-8") as f:
            strategy_rules = f.read().strip()

    last_query = "None"
    if os.path.exists(video_history_path):
        try:
            with open(video_history_path, "r") as f:
                history = json.load(f)
                if history: last_query = history[-1].get("search_query", "None")
        except: pass

    voice_menu = """
    VOICE MENU (KOKORO):
    - 'af_bella': Clear, viral, sympathetic (Best for Drama/Stories)
    - 'am_adam': Deep, calm, masculine (Best for Serious/Horror)
    - 'af_sky': High energy, fast, youthful (Best for Rants/Comedy)
    - 'bf_isabella': British, sophisticated, cold (Best for True Crime)

    HUMAN VOICE INSTRUCTIONS:
    - Choose a 'voice_speed' between 1.1 (normal-fast) and 1.5 (very fast/aggressive).

    """
    

    # 3. Hardware-Check & Modus-Definition
    if use_rtx_3090:
        mode_instruction = """
        MODE: HIGH-END AI VIDEO (RTX 3090)
        - You MUST generate 12 detailed visual scenes ('prompts_scene').
        - Each scene: 5-6 seconds, cinematic description (lighting, camera angle).
        """
        json_fields = '"prompts_scene": ["Scene 1...", "Scene 12..."],'
    else:
        live_trends = get_trending_backgrounds()
        mode_instruction = f"""
        MODE: CLASSIC BRAINROT (1660 Ti / Low VRAM)
        - Focus on a high-impact 'search_query' for YouTube (ASMR/Gameplay).
        - add to search "no copyright"
        - Avoid repeating the last query: {last_query}
        - Current Trends: {", ".join(live_trends)}
        """
        json_fields = '"search_query": "specific youtube search term",'

    # 4. Der finale Prompt-String
    prompt = f"""
    Analyze this story and create a viral video strategy.
    
    STORY: "{story_text}"

    {mode_instruction}

    {voice_menu}

    CHANNELS RULES:
    {strategy_rules}

    Return ONLY a raw JSON:
    {{
        "voice": "af_bella",
        "voice_speed": 1.25,
        "folder_name": "unique_topic_name",
        {json_fields}
        "bg_music_query": "mood + 'no copyright'",
        "caption": "Viral hook for the screen",
        "tags": "#shorts #reddit #aita",
        "action_words": ["WORD1", "WORD2"],
        "reason": "Why did you choose this vibe?"
    }}
    """
    return prompt