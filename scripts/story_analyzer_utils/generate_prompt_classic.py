import json
import os

from story_analyzer_utils.trending import get_trending_backgrounds

def generate_prompt_classic(strategy_log, video_history, available_voices, story_text):
    strategy_rules = ""

    if os.path.exists(strategy_log):
        with open(strategy_log, "r", encoding="utf-8") as f:
            strategy_rules = f.read().strip()

    live_trends = get_trending_backgrounds()
    trends_text = ", ".join(live_trends) if live_trends else ""

    last_search_query = ""

    try:
        with open(video_history, "r", encoding="utf-8") as f:
            history = json.load(f)
            if isinstance(history, list) and len(history) > 0:
                last_entry = history[-1]
                last_search_query = last_entry.get("bg_video_query", last_entry.get("bg_video_query", ""))
    except Exception as e:
        print(f"[!] Warning: Could not read {video_history}: {e}")

    prompt = f"""
    Analyze this story and decide the visual, vocal, and musical strategy for a VIRAL TikTok/Shorts video.
    
    STORY: "{story_text}"

    CHANNEL RULES (BASED ON RECENT DATA):
    {strategy_rules}

    CURRENT TRENDS FOR INSPIRATION: {trends_text}

    TASK:
    1. Select a Voice: Choose from {available_voices}. Match the emotion.
    
    2. Background Video Strategy:
       - We ONLY use stimulating ASMR or gameplay (Brainrot style).
       - Create a 'folder_name' and a specific 'search_query' for youtube (Append "no commentary" and "4k").
       - Avoid the last query: {last_search_query}
       - Avoid banned query: ["shredder satisfying paper shredding",]


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