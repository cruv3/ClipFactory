import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
import moviepy.video.fx.all as vfx

# Deine neuen Unter-Module
from video_utils.video_text_engine import VideoTextEngine
from video_utils.video_generator import VideoGeneratorEngine
from config import USE_RTX_XX90

class VideoEngine:
    def __init__(self, is_test=False):
        self.text_engine = VideoTextEngine()
        self.generator = VideoGeneratorEngine()
        self.is_test = is_test

        # RENDER SETTINGS
        if is_test:
            self.res_height = 854
            self.fps = 15
            self.preset = "ultrafast"
            self.bitrate = "2000k"
        else:
            self.res_height = 1920
            self.fps = 30
            self.preset = "medium" 
            self.bitrate = "8000k"

        self.threads = 12
        self.logger = "bar"
        self.res_width = int((self.res_height * (9 / 16)) // 2) * 2

    def create_video(self, word_timestamps, audio_path, script_text, strategy, bg_music_path=None):
        print(f"\n[*] Starting Production (Hardware-Mode: {'RTX XX90' if USE_RTX_XX90 else 'Standard'})")
        os.makedirs(strategy.output_dir, exist_ok=True)

        # 1. AUDIO LADEN
        audio_clip = AudioFileClip(audio_path)
        final_audio = audio_clip

        # 2. HINTERGRUND BESCHAFFEN (KI oder Lokal)
        bg_video_path = self.generator.get_background_video(strategy, script_text)
        
        if not bg_video_path:
            print("[!] No background video available/generated.")
            return False

        # 3. AUDIO MIXEN (Stimme + Musik)
        if bg_music_path and os.path.exists(bg_music_path):
            try:
                bg_music_clip = AudioFileClip(bg_music_path).volumex(0.1)
                if bg_music_clip.duration > audio_clip.duration:
                    bg_music_clip = bg_music_clip.subclip(0, audio_clip.duration)
                final_audio = CompositeAudioClip([audio_clip, bg_music_clip])
            except Exception as e:
                print(f"[!] Music mix failed: {e}")

        # 4. VIDEO CLIPS VORBEREITEN
        # Wir laden das Video und schneiden es exakt auf die Audio-Länge
        video_clip = VideoFileClip(bg_video_path).subclip(0, audio_clip.duration)
        
        # 9:16 Zuschneiden & Resizen
        v_w, v_h = video_clip.size
        target_w = int((v_h * (9/16)) // 2) * 2
        video_clip = vfx.crop(video_clip, width=target_w, height=v_h, x_center=v_w/2, y_center=v_h/2)
        video_clip = video_clip.resize(height=self.res_height)

        # 5. TEXT OVERLAYS
        action_words_list = [aw.upper() for aw in strategy.action_words]
        text_overlays = self.text_engine.generate_text_overlays(
            word_timestamps, 
            video_clip.w, 
            action_words_list
        )

        # 6. FINALER ZUSAMMENBAU
        final = CompositeVideoClip([video_clip] + text_overlays).set_audio(final_audio)
        output_path = os.path.join(strategy.output_dir, f"{strategy.folder_name}.mp4")

        # 7. RENDERN
        print(f"[*] Rendering with {self.threads} threads...")
        final.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            fps=self.fps, 
            preset=self.preset, 
            bitrate=self.bitrate,
            threads=self.threads,
            logger=self.logger
        )

        # Resourcen freigeben (Wichtig für Server-Dauerbetrieb)
        video_clip.close()
        audio_clip.close()
        if bg_music_path: bg_music_clip.close()

        return output_path