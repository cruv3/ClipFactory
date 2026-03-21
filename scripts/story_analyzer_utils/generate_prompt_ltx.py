import os

def generate_prompt_ltx(strategy_log, story_text):
    """
    Erstellt den Prompt für den High-End Modus mit RTX XX90 (LTX-2.3 + ChatTTS).
    Fokus: Detaillierte visuelle Szenenbeschreibungen und emotionale Stimmwahl.
    """
    strategy_rules = ""
    if os.path.exists(strategy_log):
        with open(strategy_log, "r", encoding="utf-8") as f:
            strategy_rules = f.read().strip()

    # Wir definieren hier ein Menü für das LLM, damit die Stimme zum Inhalt passt.
    voice_menu = """
    - [Seed 2]: Deep, calm, serious male voice (Thriller, Horror, Mystery)
    - [Seed 10]: Friendly, expressive, mid-range female voice (AITA, Drama, Gossip)
    - [Seed 88]: Energetic, fast-talking, slightly sarcastic male voice (Funny, Chaotic, Rants)
    - [Seed 5]: Soft, emotional female voice (Sad, Heartbreaking, Relatable)
    """

    prompt = f"""
    Analyze this story and create a HIGH-END CINEMATIC strategy for a TikTok/Shorts video using AI Video (LTX-2.3).
    
    STORY: "{story_text}"

    CHANNEL RULES (VISUAL STYLE):
    {strategy_rules}

    VOICE SEED MENU:
    {voice_menu}

    TASK:
    1. Select the best 'voice_seed' from the menu based on the story's emotion. 
    
    2. AI Video Strategy (LTX-2.3):
       - Create exactly 12 'prompts_scene'.
       - Each scene must be exactly 5 seconds long.
       - Describe cinematic visuals: lighting (e.g., moody, neon, sunlight), camera movement (e.g., slow zoom, pan, close-up), and detailed textures.
       - The 12 scenes must visually represent the story's progression from beginning to end.

    3. Background Music Mood:
       - LTX-2.3 will generate ambient sound, but we still need a background music query for a low-volume music layer.
       - Query must include "no copyright".

    4. Tagging:
       - Use 6-8 viral hashtags including #aiart #aithedrama #redditstories.

    Return ONLY a raw JSON object. Follow this exact structure:
    {{
        "voice": "energetic_narrator",
        "voice_seed": 88,
        "voice_speed": 1.25,
        "folder_name": "ai_cinematic_drama",
        "prompts_scene": [
            "Cinematic close-up of a shattered phone on a dark wooden floor, dramatic side lighting, 4k",
            "Wide shot of a woman looking out of a rain-streaked window, melancholic atmosphere, slow zoom in",
            "... and 10 more scenes matching the story plot ..."
        ],
        "bg_music_query": "tense cinematic violin background no copyright",
        "reason": "The story is a high-stakes betrayal and needs a dark, cinematic look.",
        "hook_style": "Dramatic",
        "caption": "I still can't believe he did this... 🫢",
        "description": "An AI-generated visual journey of a crazy reddit story. #reddit #aiart",
        "tags": "#shorts #redditstories #ai #cinematic #drama #storytime #aithedrama",
        "action_words": ["BETRAYAL", "SHATTERED", "GONE"]
    }}
    """
    return prompt