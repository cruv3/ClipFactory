import os
import requests
import glob
import subprocess
import yt_dlp
import time

import config

class VideoGeneratorEngine:
    def __init__(self):
        self.use_ai = config.USE_RTX_XX90
    
    def get_background_video(self, strategy):
        """Entscheidet: KI-Szenen rendern oder YouTube-Chunks nutzen."""
        if self.use_ai and hasattr(strategy, 'script_timeline') and strategy.script_timeline:
            print(f"[*] AI-Mode: Triggering LTX-2.3 on Linux Server...")
            return self._generate_ai_video(strategy)

        return self._get_available_chunk(strategy.folder_name, strategy.search_query)

    def _generate_ai_video(self, strategy):
        prompts = [block.get('visual_prompt', '') for block in strategy.script_timeline]
        payload = {"scenes": prompts, "folder_name": strategy.folder_name}

        try:
            # 1. Den Render-Request an den Linux-Server senden
            response = requests.post(config.API_GENERATE_VIDEO, json=payload, timeout=7200)
            response.raise_for_status()
            
            data = response.json()
            remote_paths = data.get("video_paths", [])
            
            if not config.TEST_RUN:
                print("[*] TEST_RUN is False. Skipping heavy download. Using first remote path as reference.")
                # Wir geben nur den Namen zurück, damit man sieht, dass es geklappt hat
                return remote_paths[0] if remote_paths else None

            print(f"[+] TEST_RUN active: Downloading {len(remote_paths)} clips to Windows...")
            scene_dir = os.path.join(strategy.output_dir, "ai_scenes")
            os.makedirs(scene_dir, exist_ok=True)
            local_clips = []

            for remote_path in remote_paths:
                filename = os.path.basename(remote_path)
                download_url = f"{config.VIDEO_BASE_URL}/download_video/{filename}"
                
                # Datei vom Linux-Server ziehen
                with requests.get(download_url, stream=True) as r:
                    r.raise_for_status()
                    local_path = os.path.join(scene_dir, filename)
                    with open(local_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                local_clips.append(local_path)

            return self._merge_clips(local_clips, strategy)

        except Exception as e:
            print(f"[!] LTX API Error: {e}")
            return None

    def _merge_clips(self, clips, strategy):
        """Klebt die KI-Clips mit FFmpeg verlustfrei zusammen."""
        if not clips: return None
        if len(clips) == 1: return clips[0]

        master_path = os.path.join(strategy.output_dir, "ai_master_bg.mp4")
        list_path = os.path.join(strategy.output_dir, "concat_list.txt")

        with open(list_path, "w") as f:
            for c in clips:
                f.write(f"file '{c.replace('\\', '/')}'\n")

        # Schnelles Zusammenfügen ohne Re-Encoding
        cmd = f'ffmpeg -y -f concat -safe 0 -i "{list_path}" -c copy "{master_path}"'
        subprocess.run(cmd, shell=True, capture_output=True)
        
        return master_path
    
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
        
        category_dir = os.path.join(config.VIDEO_CHUNKS_DIR, folder_name)
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
        category_dir = os.path.join(config.VIDEO_CHUNKS_DIR, folder_name)
        os.makedirs(category_dir, exist_ok=True)
        
        chunks = sorted(glob.glob(os.path.join(category_dir, "chunk_*.mp4")))

        if not chunks:
            self._download_and_slice(folder_name, search_query)
            chunks = sorted(glob.glob(os.path.join(category_dir, "chunk_*.mp4")))
            
        return chunks[0] if chunks else None