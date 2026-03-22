import os
import requests
import glob
import subprocess
import yt_dlp
import time

from config import USE_RTX_XX90, VIDEO_AI_URL, AI_GENERATED_DIR, VIDEO_CHUNKS_DIR

class VideoGeneratorEngine:
    def __init__(self):
        self.use_ai = USE_RTX_XX90
        self.api_url = f"{VIDEO_AI_URL}/generate_video"

    def get_background_video(self, strategy):
        """Entscheidet: KI-Szenen rendern oder YouTube-Chunks nutzen."""
        
        if self.use_ai and strategy.prompts_scene:
            print(f"[*] RTX XX90 & Scene Prompts detected: Starting LTX-2.3 Master Render...")
            ai_video_path = self._generate_ai_video(strategy)
            if ai_video_path:
                return ai_video_path
            print("[!] AI Video failed, falling back to local chunks...")

        print(f"[*] Using Classic Mode for strategy: {strategy.folder_name}")
        return self._get_available_chunk(strategy.folder_name, strategy.search_query)
        
    def _generate_ai_video(self, strategy):
        payload = {
            "scenes": strategy.prompts_scene,
            "folder_name": strategy.folder_name
        }  

        try:
            print(f"[*] Sending 12 scenes to AI Service. This will take a while...")
            response = requests.post(self.api_url, json=payload, timeout=3600)
            response.raise_for_status()
            
            data = response.json()
            output_filename = f"{strategy.folder_name}_final_master.mp4"
            final_path = os.path.join(AI_GENERATED_DIR, output_filename)

            if os.path.exists(final_path):
                print(f"[✅] AI Master Video ready: {final_path}")
                return final_path
                
        except Exception as e:
            print(f"[!] Critical Error calling AI Video API: {e}")
            return None
    
    def _download_and_slice(self, folder_name, search_query):
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

    def _get_available_chunk(self, folder_name, search_query):
        category_dir = os.path.join(VIDEO_CHUNKS_DIR, folder_name)
        os.makedirs(category_dir, exist_ok=True)
        
        chunks = sorted(glob.glob(os.path.join(category_dir, "chunk_*.mp4")))

        if not chunks:
            self._download_and_slice(folder_name, search_query)
            chunks = sorted(glob.glob(os.path.join(category_dir, "chunk_*.mp4")))
            
        return chunks[0] if chunks else None