import os
import shutil
from datetime import datetime
import requests
import json
import glob
import yt_dlp
import subprocess
import time 
import random

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

def get_random_username():
    """Generiert einen zufälligen, authentisch wirkenden Reddit/Internet Username."""
    
    adjectives = [
        # Moods & Personality
        "Silent", "Happy", "Toxic", "Sleepy", "Lost", "Crazy", "Bored", 
        "Angry", "Salty", "Spicy", "Clumsy", "Awkward", "Silly", "Drunk",
        "Confused", "Lazy", "Grumpy", "Sneaky", "Suspicious", "Anxious",
        "Tired", "Exhausted", "Lonely", "Introverted", "Clueless", "Paranoid",
        "Overthinking", "Sad", "Depressed", "Hyper", "Chill", "Nervous",
        
        # Internet & Gaming
        "Noob", "Typical", "Average", "Random", "Secret", "Hidden",
        "Sweaty", "Casual", "Filthy", "Dank", "Cursed", "Based", "Epic",
        "Legendary", "Cosmic", "Retro", "Glitched", "Caffeinated", "AFK",
        "Tryhard", "Underrated", "Overrated", "Forgotten",
        
        # Physical & Quirky
        "Fluffy", "Crunchy", "Squishy", "Moist", "Soggy", "Crusty", 
        "Shiny", "Sparkly", "Dusty", "Rusty", "Frozen", "Melted", "Burnt", 
        "Radioactive", "Sticky", "Heavy", "Tiny", "Giant", "Invisible",
        
        # Colors & Nature
        "Crimson", "Azure", "Golden", "Midnight", "Shadow", "Neon",
        "Wild", "Feral", "Rabid", "Tame", "Stray", "Furious"
    ]
    
    nouns = [
        # Animals (Meme-heavy)
        "Panda", "Ninja", "Unicorn", "Kitten", "Pirate", "Penguin", 
        "Dragon", "Goblin", "Frog", "Doge", "Cat", "TrashPanda", "Raccoon", 
        "Possum", "Turtle", "Platypus", "Hamster", "Rat", "Bear", "Wolf", 
        "Fox", "Owl", "Sloth", "Moth", "Duck", "Goose", "Capybara",
        
        # Food
        "Cabbage", "Potato", "Noodle", "Taco", "Burrito", "Burger", 
        "Pizza", "Onion", "Mango", "Banana", "Apple", "Lemon", "Melon", 
        "Waffle", "Pancake", "Toast", "Bread", "Sandwich", "Cheese", "Bean",
        "Nugget", "Dumpling", "Cookie", "Muffin", "Bacon",
        
        # Internet/Gaming
        "Wizard", "Robot", "Gamer", "Student", "Guy", "Dude", "Bro", 
        "Girl", "Throwaway", "Account", "User", "Human", "Memer", "Poster", 
        "Lurker", "Scroller", "Troll", "Player", "NPC", "Main", "Alt", "Smurf",
        
        # Random Objects & Concepts
        "Sock", "Shoe", "Chair", "Lamp", "Spoon", "Mug", "Brick", "Rock",
        "Tree", "Mistake", "Regret", "Accident", "Error", "Glitch", "Paradox"
    ]

    format_choice = random.randint(1, 4)
    
    if format_choice == 1:
        # AdjektivNomenZahl (z.B. SleepyPotato42)
        return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1, 9999)}"
        
    elif format_choice == 2:
        # Adjektiv_Nomen_Zahl (z.B. Toxic_Gamer_99)
        return f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(1, 99)}"
        
    elif format_choice == 3:
        # Nur Adjektiv und Nomen, keine Zahl (z.B. MoistCabbage)
        return f"{random.choice(adjectives)}{random.choice(nouns)}"
        
    else:
        # Throwaway Account (Klassiker für Story-Subreddits)
        return f"Throwaway{random.randint(10000, 999999)}"

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


def download_and_slice(folder_name, search_query):
        clean_query = search_query.lower().replace("4k", "").replace("1080p", "").replace("no commentary", "").strip()
        core_theme = " ".join(clean_query.split()[:3])

        queries_to_try = [
            f"{search_query} -facecam -streamer -reaction -shorts no commentary cinematic",
            f"{search_query} -facecam -streamer -shorts no commentary",
            f"{clean_query} gameplay no commentary -shorts -facecam",
            f"{core_theme} gameplay no commentary -shorts -facecam",
            "minecraft parkour gameplay no commentary 4k -shorts"
        ]

        print(f"\n[!] Inventory for '{folder_name}' empty. Searching YouTube: {search_query}")
        
        category_dir = os.path.join(VIDEO_CHUNKS_DIR, folder_name)
        os.makedirs(category_dir, exist_ok=True)
        
        temp_video = os.path.join(category_dir, "temp_source.mp4")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': temp_video,
            'quiet': True,
            'noprogress': True,
            'noplaylist': True,
            'retries': 3,
            'fragment_retries': 3,
            'ignoreerrors': True,
            'max_downloads': 1,
            'match_filter': yt_dlp.utils.match_filter_func("duration > 480 & height >= 1080 & !is_live"),
        }

        download_success = False
        for i, query in enumerate(queries_to_try):
            print(f"[*] Search Attempt {i+1}/4: '{query}'")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(f"ytsearch10:{query}", download=True)
            except Exception:
                pass

            if os.path.exists(temp_video):
                print(f"[+] Download successful on attempt {i+1}!")
                download_success = True
                break
            else:
                print(f"[-] Attempt {i+1} failed to find a valid video.")

        if not download_success:
            print("[!] CRITICAL: All fallback attempts failed. Check internet or update yt-dlp.")
            return False

        print(f"[+] Slicing into 90s chunks...")
        
        chunk_pattern = os.path.join(category_dir, "chunk_%03d.mp4")
        ffmpeg_command = f'ffmpeg -y -ss 00:01:30 -i "{temp_video}" -c copy -map 0 -segment_time 00:01:30 -f segment "{chunk_pattern}"'
        
        try:
            subprocess.run(ffmpeg_command, check=True, shell=True)
            time.sleep(1)

            generated_chunks = glob.glob(os.path.join(category_dir, "chunk_*.mp4"))
            
            for chunk in generated_chunks:
                file_size_mb = os.path.getsize(chunk) / (1024 * 1024)
                if file_size_mb < 5: 
                    print(f"[-] Deleting tiny chunk (possible remainder): {chunk} ({file_size_mb:.2f}MB)")
                    os.remove(chunk)

            if os.path.exists(temp_video):
                os.remove(temp_video)
        except subprocess.CalledProcessError as e:
            print(f"[!] FFmpeg failed: {e}")

def get_available_chunk(folder_name, search_query):
    category_dir = os.path.join(VIDEO_CHUNKS_DIR, folder_name)
    os.makedirs(category_dir, exist_ok=True)
    
    chunks = sorted(glob.glob(os.path.join(category_dir, "chunk_*.mp4")))

    if not chunks:
        download_and_slice(folder_name, search_query)
        chunks = sorted(glob.glob(os.path.join(category_dir, "chunk_*.mp4")))
        
    return chunks[0] if chunks else None



if __name__ == "__main__":
    print("[*] Sammle die aktuelle TikTok/Shorts Meta...")
    trends = get_trending_backgrounds()
    print(f"\n[+] {len(trends)} heiße Trends gefunden:")
    for t in trends:
        print(f" - {t}")