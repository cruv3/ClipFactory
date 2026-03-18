import os
import platform
import random
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip
import moviepy.video.fx.all as vfx
import time
import math
import re

import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from config import (
    VIDEO_CHUNKS_DIR, TEST_RUN, FONT_PATH
)

if platform.system() == "Windows":
    IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
    change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})
else:
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

class VideoEngineOld:
    def create_video(self, word_timestamps, audio_path, strategy, bg_music_path=None):
        print("\n[*] Starting video production...")
        os.makedirs(strategy.output_dir, exist_ok=True)

        bg_video_path = self._get_available_chunk(strategy.folder_name, strategy.search_query)
        if not bg_video_path:
            print("[!] No background video available.")
            return None

        print(f"[*] Using background chunk: {bg_video_path}")
        
        try:      
            audio_clip = AudioFileClip(audio_path)
            final_audio = audio_clip
            bg_music_clip = None

            if bg_music_path and os.path.exists(bg_music_path):
                print(f"[*] Mixing Voice with Background Music (10% volume)...")
                try:
                    bg_music_clip = AudioFileClip(bg_music_path)
                    
                    # 1. Musik-Lautstärke auf 10% drosseln
                    bg_music_clip = bg_music_clip.volumex(0.1)
                    
                    if bg_music_clip.duration > audio_clip.duration:
                        bg_music_clip = bg_music_clip.subclip(0, audio_clip.duration)
                    
                    # 3. Stimme und Musik übereinanderlegen
                    final_audio = CompositeAudioClip([audio_clip, bg_music_clip])
                except Exception as e:
                    print(f"[!] Warnung: Konnte Hintergrundmusik nicht mischen. Error: {e}")
                    final_audio = audio_clip # Fallback auf reine Stimme
            else:
                print("[-] Kein Background Music Path übergeben oder Datei fehlt. Render nur mit Stimme.")

            video_clip = VideoFileClip(bg_video_path)

            # --- ANTI-DUPLICATE HASH BUSTER ---
            color_shift = random.uniform(0.98, 1.02)
            video_clip = video_clip.fx(vfx.colorx, color_shift)
            
            # Video auf Audiolänge kürzen
            video_clip = video_clip.subclip(0, audio_clip.duration)
            (w, h) = video_clip.size
            target_width = int((h * (9 / 16)) // 2) * 2
            video_clip = vfx.crop(video_clip, width=target_width, height=h, x_center=w/2, y_center=h/2)
            video_clip = video_clip.resize(newsize=(1080, 1920))

            action_words_list = [aw.upper() for aw in strategy.action_words]
            text_overlays = self._create_text_clips(word_timestamps, 1080, action_words_list)
            final_video = CompositeVideoClip([video_clip] + text_overlays).set_audio(final_audio)
            
            output_path = os.path.join(strategy.output_dir, f"{strategy.folder_name}.mp4")

            print("[*] Rendering Video...")
            final_video.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                fps=30, 
                preset="slow",      # 'medium' oder 'slow' für bessere Kompression/Qualität
                bitrate="8000k",      # Hohe Bitrate für scharfe Kanten
                ffmpeg_params=[
                    "-pix_fmt", "yuv420p",
                    "-crf", "18",      # Constant Rate Factor: 18 ist visuell verlustfrei
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2" # Fix für ungerade Dimensionen
                ],
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
            
            # --- NEU ---
            try:
                if 'bg_music_clip' in locals() and bg_music_clip: 
                    bg_music_clip.close()
            except Exception: pass
            
            try:
                if 'final_audio' in locals() and final_audio != audio_clip: 
                    final_audio.close()
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
        
        return output_path

    def _create_text_clips(self, word_data, video_width, action_words=[]):
        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"[!] Font not found: {FONT_PATH}")
        
        font = FONT_PATH
        base_fontsize = 100  
        max_allowed_width = int(video_width * 0.85) 
        gap = 15
        
        # Nur noch Standard Farben (kein Rot mehr)
        color_active = "#FFDD00"
        stroke_active_color = "#B8860B"
        color_inactive = "#FFFFFF"
        stroke_inactive_color = "#B0B0B0"
        
        stroke_width = 6.0

        # Die Funktion ist jetzt wieder simpler (kein is_action Parameter mehr nötig für Größe/Farbe)
        def make_clean_text(txt, c_fill, c_stroke):
            bg_clip = TextClip(
                txt=txt, fontsize=base_fontsize, font=font,
                color=c_stroke, stroke_color=c_stroke, 
                stroke_width=stroke_width * 2, method='label'
            )
            fg_clip = TextClip(
                txt=txt, fontsize=base_fontsize, font=font,
                color=c_fill, method='label'
            )
            return CompositeVideoClip([bg_clip, fg_clip.set_position('center')], size=bg_clip.size)

        # HILFSFUNKTION: Entfernt alle Satzzeichen für den Check
        def clean_for_match(word):
            return re.sub(r'[^A-Z0-9]', '', word)

        text_clips = []
        
        for i in range(len(word_data)):
            current_word_item = word_data[i]
            word_text = f' {current_word_item["word"].upper()} '
            start_t = current_word_item["start"]

            if i < len(word_data) - 1:
                end_t = word_data[i+1]["start"]
            else:
                end_t = current_word_item["end"]

            dur = max(0.1, min(end_t - start_t, 1.5))
            
            raw_word_1 = current_word_item["word"].upper()
            is_action_1 = clean_for_match(raw_word_1) in action_words

            is_even = i % 2 == 0
            if is_even:
                pair_text_1 = word_text
                raw_word_2 = word_data[i+1]["word"].upper() if i+1 < len(word_data) else ""
                pair_text_2 = f' {raw_word_2} ' if raw_word_2 else ""
                
                is_action_2 = clean_for_match(raw_word_2) in action_words

                # Ganz normale Farbzuweisung (Aktives Wort gelb, inaktives weiß)
                c1, s1_c = color_active, stroke_active_color
                c2, s2_c = color_inactive, stroke_inactive_color
            else:
                raw_word_1_prev = word_data[i-1]["word"].upper()
                pair_text_1 = f' {raw_word_1_prev} '
                pair_text_2 = word_text
                
                is_action_1_prev = clean_for_match(raw_word_1_prev) in action_words

                # Ganz normale Farbzuweisung (Inaktives Wort weiß, aktives gelb)
                c1, s1_c = color_inactive, stroke_inactive_color
                c2, s2_c = color_active, stroke_active_color

            # Left/Top Clip
            clip_left = make_clean_text(pair_text_1, c1, s1_c)
            clip_left = clip_left.set_start(start_t).set_duration(dur)

            # Right/Bottom Clip
            clip_right = None
            if pair_text_2.strip(): 
                clip_right = make_clean_text(pair_text_2, c2, s2_c)
                clip_right = clip_right.set_start(start_t).set_duration(dur)

            # --- POSITIONIERUNG (HORIZONTAL NEBENEINANDER MIT KURZEM SHAKE) ---
            if clip_right:
                total_w = clip_left.w + gap + clip_right.w
                
                if total_w > max_allowed_width:
                    scale = max_allowed_width / total_w
                    clip_left = clip_left.resize(scale)
                    clip_right = clip_right.resize(scale)
                    total_w = max_allowed_width
                
                start_x = (video_width - total_w) / 2
                
                base_y_left = (1920 - clip_left.h) / 2
                base_y_right = (1920 - clip_right.h) / 2
                
                left_is_action = (is_even and is_action_1) or (not is_even and is_action_1_prev)
                right_is_action = (is_even and is_action_2) or (not is_even and is_action_1)

                # Linkes Wort (Kurzer Shake für die ersten 0.2 Sekunden)
                if left_is_action:
                    clip_left = clip_left.set_position(
                        lambda t, x=start_x, y=base_y_left: (x, y + (math.sin(t * 80) * 8 if t < 0.2 else 0))
                    )
                else:
                    clip_left = clip_left.set_position((start_x, 'center'))

                # Rechtes Wort (Kurzer Shake für die ersten 0.2 Sekunden)
                if right_is_action:
                    clip_right = clip_right.set_position(
                        lambda t, x=(start_x + clip_left.w + gap), y=base_y_right: (x, y + (math.sin(t * 80) * 8 if t < 0.2 else 0))
                    )
                else:
                    clip_right = clip_right.set_position((start_x + clip_left.w + gap, 'center'))
                
                text_clips.append(clip_left)
                text_clips.append(clip_right)
            else:
                if clip_left.w > max_allowed_width:
                    clip_left = clip_left.resize(width=max_allowed_width)
                
                base_y_single = (1920 - clip_left.h) / 2
                
                # Einzelnes Wort (Kurzer Shake für die ersten 0.2 Sekunden)
                if is_action_1:
                    clip_left = clip_left.set_position(
                        lambda t, y=base_y_single: ('center', y + (math.sin(t * 80) * 8 if t < 0.2 else 0))
                    )
                else:
                    clip_left = clip_left.set_position('center')
                    
                text_clips.append(clip_left)
        
        return text_clips
    
# --- TEST RUN ---
if __name__ == "__main__":
    import dataclasses
    import os
    import time
    
    from voice_engine import VoiceEngine 
    from music_engine import MusicEngine 

    @dataclasses.dataclass
    class MockStrategy:
        voice: str
        voice_speed: float
        hook_style: str
        folder_name: str
        output_dir: str
        search_query: str
        reason: str
        caption: str
        description: str
        tags: str
        action_words: list
        bg_music_query: str

    # Deine Test-Daten inklusive Musik-Vibe
    test_strategy = MockStrategy(
        voice="am_michael",
        voice_speed=1.1,
        hook_style="Humorous",
        folder_name="satisfying_sand",
        output_dir="data/test_run_sand",
        search_query="kinetic sand cutting with cookie cutters no commentary 4k",
        reason="Drama at the office...",
        caption="He said WHAT about my lunches?! 😭😭 #husbandproblems",
        description="This wife's sweet gestures backfired!",
        tags="#lunchboxfails #couplecomedy",
        action_words=["HEART", "LIED", "CAUGHT", "POLAROID", "LAWYER"],
        bg_music_query="sneaky suspicious comedic background music no copyright"
    )

    test_script = """
    I woke up at 5 AM daily, making gourmet lunches and cutting his cheese into a perfect HEART. 
    But he lied! I surprised him at work and CAUGHT his coworker hand-feeding him! 
    I snapped a POLAROID, packed my bags, and immediately called a LAWYER. 
    Am I the jerk?
    """

    print("\n" + "="*40)
    print("🎬 STARTING FULL AUDIO-VISUAL PIPELINE TEST")
    print("="*40)

    # 1. Voice generieren
    voice_eng = VoiceEngine()
    while not voice_eng.model_verified:
        time.sleep(2)
        voice_eng.model_verified = voice_eng.verify_kokoro()

    print("\n[*] 1. Generating Audio (Kokoro)...")
    audio_path = voice_eng.generate_audio(test_script, strategy=test_strategy)
    
    if not audio_path or not os.path.exists(audio_path):
        print("[!] TEST ABORTED: Voice generation failed.")
    else:
        # 2. Timestamps extrahieren
        print("\n[*] 2. Extracting Timestamps (Whisper)...")
        word_timestamps = voice_eng.get_word_timestamps(audio_path)
        print(f"[+] Extracted {len(word_timestamps)} words.")

        # 3. Hintergrundmusik laden (NEU)
        print("\n[*] 3. Fetching Background Music (MusicEngine)...")
        music_eng = MusicEngine()
        bg_music_path = music_eng.fetch_background_music(test_strategy)

        # 4. Video-Assembly mit Voice UND Musik
        print("\n[*] 4. Assembling Video with Voice, Music & Shakes...")
        video_eng = VideoEngine()
        
        success_path = video_eng.create_video(
            word_timestamps=word_timestamps,
            audio_path=audio_path,
            strategy=test_strategy,
            bg_music_path=bg_music_path 
        )

        if success_path:
            print(f"\n[✅] TEST SUCCESSFUL! Video created at: {success_path}")
            print(f"[*] Visual Check: Action Words should shake briefly.")
            print(f"[*] Audio Check: Voice should be clear, Music at 10% volume.")
        else:
            print("\n[!] TEST FAILED during Video Assembly.")