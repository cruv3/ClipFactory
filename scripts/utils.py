import os
import shutil
from datetime import datetime
import requests
import json

from config import DATA_DIR, VIDEO_CHUNKS_DIR, STRATEGY_LOG, VIDEO_HISTORY_JSON

from dataclasses import dataclass
@dataclass
class StoryStrategy:
    voice: str
    voice_speed: float
    hook_style: str
    folder_name: str
    output_dir: str
    search_query: str
    bg_music_query: str
    reason: str
    caption: str
    description: str
    tags: str
    action_words: list

def clean_data_folder():
    print(f"\n[*] Cleaning factory floor ({DATA_DIR})...")
    
    if not os.path.exists(DATA_DIR):
        return

    # Diese Sachen lassen wir Finger weg!
    keep_list = [os.path.basename(VIDEO_CHUNKS_DIR), os.path.basename(STRATEGY_LOG), os.path.basename(VIDEO_HISTORY_JSON)]

    for item in os.listdir(DATA_DIR):
        item_path = os.path.join(DATA_DIR, item)
        
        if item in keep_list:
            continue
            
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            print(f"[!] Could not delete {item}: {e}")
    
    print("[+] Cleanup finished.\n")

def ensure_folders(folders):
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def generate_story_id():
    return datetime.now().strftime("_%Y%m%d_%H%M%S")

def get_trending_backgrounds():
    """Holt die aktuellsten Suchtrends für Background-Videos direkt von YouTube."""

    base_queries = [
        # --- KATEGORIE 1: High-Speed & Focus Gaming (Hält die Augen auf dem Screen) ---
        "gta 5 parkour no commentary",
        "gta 5 mega ramp no commentary",
        "minecraft parkour gameplay no commentary",
        "subway surfers gameplay no commentary",
        "csgo surf gameplay no commentary",
        "trackmania stunts no commentary",
        
        # --- KATEGORIE 2: Oddly Satisfying (Beruhigend, gut für emotionale Stories) ---
        "satisfying kinetic sand cutting asmr",
        "satisfying slime mixing no commentary",
        "soap cutting asmr 4k",
        "oddly satisfying 3d animation loop",
        "power washing satisfying no commentary",
        "carpet cleaning satisfying asmr",
        
        # --- KATEGORIE 3: Chaos & Zerstörung (Perfekt für Drama, Revenge & Wut-Stories) ---
        "beamng drive crashes no commentary",
        "hydraulic press satisfying no commentary",
        "shredding machine satisfying video"
    ]
    
    trending_keywords = []
    
    for query in base_queries:
        url = f"http://suggestqueries.google.com/complete/search?client=chrome&ds=yt&q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            suggestions = json.loads(response.text)[1]

            trending_keywords.extend(suggestions[:3])
        except Exception as e:
            print(f"[!] Konnte Trends für '{query}' nicht laden: {e}")
            
    return trending_keywords

if __name__ == "__main__":
    print("[*] Sammle die aktuelle TikTok/Shorts Meta...")
    trends = get_trending_backgrounds()
    print(f"\n[+] {len(trends)} heiße Trends gefunden:")
    for t in trends:
        print(f" - {t}")