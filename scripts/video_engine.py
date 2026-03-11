import os
import glob
import subprocess
import yt_dlp
import platform
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip
import moviepy.video.fx.all as vfx
from PIL import Image, ImageDraw
import numpy as np
import time

from config import (
    VIDEO_CHUNKS_DIR, TEST_RUN
)

if platform.system() == "Windows":
    IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
    change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})
else:
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

class VideoEngine:
    def create_video(self, word_timestamps, audio_path, strategy):
        print("\n[*] Starting video production...")
        os.makedirs(strategy.output_dir, exist_ok=True)

        bg_video_path = self._get_available_chunk(strategy.folder_name, strategy.search_query)
        if not bg_video_path:
            print("[!] No background video available.")
            return False

        print(f"[*] Using background chunk: {bg_video_path}")
        
        try:      
            audio_clip = AudioFileClip(audio_path)
            video_clip = VideoFileClip(bg_video_path)
            
            # Video auf Audiolänge kürzen
            video_clip = video_clip.subclip(0, audio_clip.duration)
            (w, h) = video_clip.size
            target_width = int((h * (9 / 16)) // 2) * 2
            video_clip = vfx.crop(video_clip, width=target_width, height=h, x_center=w/2, y_center=h/2)

            text_overlays = self._create_text_clips(word_timestamps)
            final_video = CompositeVideoClip([video_clip] + text_overlays).set_audio(audio_clip)
            
            output_path = os.path.join(strategy.output_dir, f"{strategy.folder_name}.mp4")

            print("[*] Rendering Video...")
            final_video.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                fps=30, 
                preset="fast", 
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                logger=None
            )

        except Exception as e:
                    print(f"[!] Rendering Error: {e}")
                    return False
        finally:
            print("[*] Cleaning up resources...")
            try:
                if 'final_video' in locals():
                    if hasattr(final_video, 'audio') and final_video.audio:
                        final_video.audio.close()
                    final_video.close()
            except Exception: pass
            
            try:
                if 'audio_clip' in locals(): audio_clip.close()
            except Exception: pass
            
            try:
                if 'video_clip' in locals(): video_clip.close()
            except Exception: pass

            try:
                if 'text_overlays' in locals():
                    for txt in text_overlays:
                        txt.close()
            except Exception: pass

        time.sleep(2)
        # Benutzten Chunk löschen
        if not TEST_RUN:
            if os.path.exists(bg_video_path):
                try:
                    os.remove(bg_video_path)
                    print(f"[+] Used chunk deleted. Video saved at: {output_path}\n")
                except OSError as e:
                    print(f"[!] Could not delete chunk immediately (Errno 9 possible). OS holds lock. Error: {e}")
        return True

    def _create_text_clips(self, word_data):
        text_clips = []
        
        for data in word_data:
            word = data["word"]
            start_t = data["start"]
            dur = data["end"] - data["start"]
            if dur <= 0: dur = 0.1

            txt_clip = TextClip(
                txt=word,
                fontsize=90,       # Etwas größer, da die Box fehlt
                color='white',    # Gelb knallt auf Minecraft-Hintergrund oft am besten
                font='Arial-Bold', # Achte darauf, dass die Schriftart installiert ist
                stroke_color='black', # Ein schwarzer Umriss macht den Text ohne Box lesbar
                stroke_width=3,
                method='label'
            ).set_start(start_t).set_duration(dur).set_position('center')

            text_clips.append(txt_clip)
        
        return text_clips
    
    def _create_rounded_box(self, width, height, color, opacity, radius=25):
        # Ein transparentes RGBA Bild erstellen
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Die abgerundete Box zeichnen
        r, g, b = color
        alpha = int(opacity * 255)
        draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=(r, g, b, alpha))
        
        return np.array(img)

    def _download_and_slice(self, folder_name, search_query):
        forbidden_stuff = " -facecam -streamer -reaction -shorts"
        full_query = f"{search_query} {forbidden_stuff} no commentary cinematic"
        print(f"\n[!] Inventory for '{folder_name}' empty. Searching YouTube: {search_query}")
        
        category_dir = os.path.join(VIDEO_CHUNKS_DIR, folder_name)
        os.makedirs(category_dir, exist_ok=True)
        
        temp_video = os.path.join(category_dir, "temp_source.mp4")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': temp_video,
            'quiet': True,
            'noplaylist': True,
            'retries': 10,
            'fragment_retries': 10,
            'match_filter': yt_dlp.utils.match_filter_func("duration > 600"),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(f"ytsearch1:{full_query}", download=True)
        except Exception as e:
            print(f"[!] yt-dlp Error during search: {e}")

        if not os.path.exists(temp_video):
            print(f"[!] WARNING: Download failed for '{full_query}'. Trying safe fallback...")
            fallback_query = "minecraft parkour gameplay no commentary 4k -shorts"
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(f"ytsearch1:{fallback_query}", download=True)
            except Exception:
                pass

            if not os.path.exists(temp_video):
                print("[!] CRITICAL: Even fallback download failed.")
                return False
            
        print(f"[+] Download complete. Slicing into 90s chunks...")
        
        # Chunks landen direkt im Kategorie-Ordner
        chunk_pattern = os.path.join(category_dir, "chunk_%03d.mp4")
        ffmpeg_command = f'ffmpeg -y -ss 00:00:10 -i "{temp_video}" -c copy -map 0 -segment_time 00:01:30 -f segment "{chunk_pattern}"'
        
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
    
# --- TEST RUN ---
if __name__ == "__main__":
    import dataclasses

    # Wir bauen eine Mock-Klasse, damit wir StoryStrategy nicht importieren müssen
    @dataclasses.dataclass
    class MockStrategy:
        folder_name: str
        search_query: str
        output_dir: str

    strategy = MockStrategy(
        folder_name="minecraft",
        search_query="minecraft parkour no copyright gameplay",
        output_dir="data/test_output"
    )

    # 1. Wir simulieren Whisper Word-Timestamps
    # Normalerweise kämen diese von deinem Transcriber-Skript
    mock_word_timestamps = [
        {"word": "THIS", "start": 0.0, "end": 0.5},
        {"word": "IS", "start": 0.5, "end": 0.8},
        {"word": "A", "start": 0.8, "end": 1.0},
        {"word": "TEST", "start": 1.0, "end": 1.5},
        {"word": "OF", "start": 1.5, "end": 1.8},
        {"word": "THE", "start": 1.8, "end": 2.0},
        {"word": "FACTORY", "start": 2.0, "end": 2.8},
    ]

    # Pfad zu einer Test-Audio (Du musst eine kurze .wav oder .mp3 in data/test_audio.mp3 legen)
    test_audio = "data/test/test_audio.wav" 

    if not os.path.exists(test_audio):
        print(f"[!] TEST ABORTED: Please place a file at {test_audio}")
    else:
        engine = VideoEngine()
        
        # Hier kannst du die Flags zum Testen SCHNELL ändern:
        engine.FLAGS["USE_TEXT_BOX_BG"] = True
        engine.FLAGS["USE_TEXT_SHADOW"] = True
        
        success = engine.create_video(
            word_timestamps=mock_word_timestamps,
            audio_path=test_audio,
            strategy=strategy
        )

        if success:
            print(f"[✅] Test video created in {strategy.output_dir}")