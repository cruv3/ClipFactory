import os
import shutil
from datetime import datetime

from config import DATA_DIR, VIDEO_CHUNKS_DIR

from dataclasses import dataclass
@dataclass
class StoryStrategy:
    voice: str
    hook_style: str
    folder_name: str
    output_dir: str
    search_query: str
    reason: str
    caption: str
    description: str
    tags: str

def clean_data_folder():
    print(f"\n[*] Cleaning factory floor ({DATA_DIR})...")
    
    if not os.path.exists(DATA_DIR):
        return

    # Diese Sachen lassen wir Finger weg!
    keep_list = [os.path.basename(VIDEO_CHUNKS_DIR),]

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