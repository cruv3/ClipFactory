import os
import json
from .trending import get_trending_backgrounds

import config

def generate_prompt(story_text, use_rtx_XX90, strategy_log, video_history_path, word_min=150, word_max=250):
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
    if use_rtx_XX90:
        mode_instruction = f"""
        MODE: HIGH-END CINEMATIC DIRECTOR (RTX 3090)
        - GOAL: Create a high-retention Reddit-style video (approx. 65 seconds).
        - WORD COUNT: The total narration MUST be between {word_min} and {word_max} words. 
        - DO NOT SUMMARIZE. Use the full emotional range of the story. Extend story if needed.
        
        SCENE RULES:
        1. Generate EXACTLY 12-15 scenes. Number them correctly in the JSON.
        2. NO REPETITION in visual prompts. Do not just say 'intense expressions' every time.
        3. VISUAL VARIETY: Mix 'Extreme Close-ups', 'Wide Shots', 'Dutch Angles', and 'Slow Motion'.
        4. LTX-SPECIFIC: Describe textures (silk, tears, wood), lighting (golden hour, harsh fluorescent, candlelight), and movement (panning left, handheld shake, zooming in).

        EXAMPLE OF A GOOD SCENE:
        {{
            "narration": "I looked at her shimmering white dress - the one MY education paid for - and I just... snapped.",
            "visual_prompt": "Extreme close-up on the maid of honor's eyes, pupils dilating with rage, reflection of the white wedding dress in her iris. Cinematic lighting, moody shadows, 8k, hyper-detailed skin textures."
        }}
        """
        json_fields = """"script_timeline": [
            {
                "narration": "Spoken text (2-3 sentences per scene to reach word count)",
                "visual_prompt": "Unique cinematic LTX prompt (no 'intense expressions' copy-paste!)"
            }
        ],"""
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
    You are an expert viral video strategist and director.
    Analyze this story and create a viral video strategy.
    
    STORY: "{story_text}"

    {mode_instruction}

    {voice_menu}

    CHANNELS RULES:
    {strategy_rules}

    Return ONLY a raw JSON object matching this exact schema:
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