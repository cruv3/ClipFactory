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
    
import os
import asyncio
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
import moviepy.video.fx.all as vfx

# Deine Unter-Module
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
        self.logger = "bar" # Zeigt einen schönen Ladebalken in der Konsole

    # Parameter angepasst, damit sie zur main.py passen!
    def create_video(self, word_timestamps, audio_path, strategy, bg_music_path=None):
        print(f"\n🎬 [*] Starting Video Production (Hardware: {'RTX 3090' if USE_RTX_XX90 else 'Classic'})")
        os.makedirs(strategy.output_dir, exist_ok=True)

        # 1. AUDIO LADEN
        try:
            audio_clip = AudioFileClip(audio_path)
            final_audio = audio_clip
        except Exception as e:
            print(f"[!] Failed to load voice audio: {e}")
            return None

        # 2. HINTERGRUND BESCHAFFEN (KI oder Lokal)
        # Wir übergeben die Strategy, damit der Generator auf die "script_timeline" zugreifen kann
        bg_video_path = self.generator.get_background_video(strategy)
        
        if not bg_video_path or not os.path.exists(bg_video_path):
            print("[!] No background video available/generated.")
            return None

        # 3. AUDIO MIXEN (Stimme + Musik)
        if bg_music_path and os.path.exists(bg_music_path):
            try:
                bg_music_clip = AudioFileClip(bg_music_path).volumex(0.1) # 10% Lautstärke für Hintergrund
                
                # Musik loopt oder schneidet sich auf die Länge der Sprachaufnahme
                if bg_music_clip.duration > audio_clip.duration:
                    bg_music_clip = bg_music_clip.subclip(0, audio_clip.duration)
                
                final_audio = CompositeAudioClip([audio_clip, bg_music_clip])
            except Exception as e:
                print(f"[!] Music mix failed (continuing without music): {e}")

        # 4. VIDEO CLIPS VORBEREITEN
        try:
            video_clip = VideoFileClip(bg_video_path)
            
            # Falls das Video länger ist als das Audio, abschneiden
            if video_clip.duration > audio_clip.duration:
                video_clip = video_clip.subclip(0, audio_clip.duration)
            
            # 9:16 Zuschneiden & Resizen
            v_w, v_h = video_clip.size
            target_w = int((v_h * (9/16)) // 2) * 2
            video_clip = vfx.crop(video_clip, width=target_w, height=v_h, x_center=v_w/2, y_center=v_h/2)
            video_clip = video_clip.resize(height=self.res_height)
        except Exception as e:
            print(f"[!] Failed to process background video: {e}")
            return None

        # 5. TEXT OVERLAYS
        print("[*] Generating dynamic subtitles...")
        action_words_list = [aw.upper() for aw in strategy.action_words] if strategy.action_words else []
        text_overlays = self.text_engine.generate_text_overlays(
            word_timestamps, 
            video_clip.w, 
            action_words_list
        )

        # 6. FINALER ZUSAMMENBAU
        final = CompositeVideoClip([video_clip] + text_overlays).set_audio(final_audio)
        output_path = os.path.join(strategy.output_dir, f"{strategy.folder_name}_FINAL.mp4")

        # 7. RENDERN
        print(f"[*] Rendering Video ({self.res_height}p @ {self.fps}fps) with {self.threads} threads...")
        try:
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
        except Exception as e:
            print(f"[!] Rendering crashed: {e}")
            return None

        # 8. SPEICHER FREIGEBEN (Extrem wichtig für den RAM!)
        finally:
            try: video_clip.close()
            except: pass
            try: audio_clip.close()
            except: pass
            try: bg_music_clip.close()
            except: pass
            try: final.close()
            except: pass

        return output_path


# =====================================================================
# ISOLIERTER TEST-RUN (Direkt ausführbar!)
# =====================================================================
if __name__ == "__main__":
    from story_analyzer import StoryAnalyzer
    from voice_engine import VoiceEngine
    from utils import StoryStrategy

    print("\n" + "="*50)
    print("🧪 ISOLATED COMPONENT TEST: ANALYZER -> TTS -> VIDEO")
    print("="*50)

    # 1. Fake Story (ca. 150-200 Wörter)
    test_story = """
    AITA for canceling my wedding because my fiancé demanded I sell my dog? 
    I (28F) have a Golden Retriever named Max. I've had him for 5 years, way before I met my fiancé, Mark (30M). 
    Mark never really liked dogs, but he tolerated Max. Or so I thought. 
    We were planning our wedding for next spring. Everything was booked. The venue, the flowers, my dream dress. 
    Last night, Mark sat me down and said we needed to talk. 
    He told me that once we are married, he doesn't want Max in the house anymore. He said a dog doesn't fit into our "new elegant lifestyle" and demanded I give Max to a shelter before the wedding. 
    I was absolutely stunned. I looked at him and said, "Max is my family. If he goes, I go." 
    Mark laughed, thinking I was bluffing. I took off my engagement ring, put it on the table, and walked out with Max. 
    His family is now blowing up my phone, calling me immature for throwing away a marriage over an animal. 
    But I don't feel bad. Am I the jerk?
    """

    # 2. Module laden
    analyzer = StoryAnalyzer()
    voice_eng = VoiceEngine()
    video_eng = VideoEngine(is_test=True) # is_test=True für schnelles Rendern in niedriger Quali

    # 3. Pipeline durchlaufen
    print("\n[STEP 1] Running Master Intelligence (Ollama)...")

    strategy = StoryStrategy(
        voice='af_bella', 
        voice_speed=1.25, 
        hook_style='Dramatic', 
        folder_name='wedding_dog_dilemma', 
        output_dir=os.path.join(os.getcwd(), 'data', 'test_render'),
        search_query='', 
        bg_music_query='dramatic tension no copyright', 
        reason="The story highlights the conflict between pet loyalty and relationships.", 
        caption='Would you sacrifice your wedding for a dog?', 
        description='', 
        tags='#shorts #reddit #aita #doglife', 
        action_words=['Sacrifice', 'Loyalty'], 
        script_timeline=[
            {'narration': "I have a Golden Retriever named Max. I've had him for 5 years, way before I met my fiancé, Mark.", 
             'visual_prompt': 'Wide shot of Max playing in the grass under golden hour light, showing his fluffy coat and wagging tail.'},
            {'narration': 'Mark never really liked dogs, but he tolerated Max. Or so I thought.', 
             'visual_prompt': 'Dutch angle of Mark watching Max from a distance with a stern expression, shadows cast on his face.'}
        ]
    )

    print(strategy)

    if strategy and strategy.script_timeline:
        first_scene = strategy.script_timeline[0]
        strategy.script_timeline = [first_scene] 
        
        single_narration = first_scene.get("narration", "")
        print(f"\n[!] ISOLATING SCENE 1:")
        print(f"    🗣️ Text: {single_narration}")
        print(f"    🎥 Prompt: {first_scene.get('visual_prompt', '')}")
        
        print("\n[STEP 2] Generating Audio for Single Scene...")
        voice_path = voice_eng.generate_audio(text=single_narration, strategy=strategy)
        
        if voice_path:
            word_timestamps = voice_eng.get_word_timestamps(voice_path)
            
            print("\n[STEP 3] Rendering Single Scene Clip...")
            final_video = video_eng.create_video(
                word_timestamps=word_timestamps, 
                audio_path=voice_path, 
                strategy=strategy,
                bg_music_path=None 
            )
            
            if final_video:
                print(f"\n[✅] TEST COMPLETE!")
                print(f"    Check your output here: {final_video}")
            else:
                print("\n[❌] Video rendering failed.")
        else:
            print("\n[❌] Audio generation failed.")
    else:
        print("\n[❌] Story Analyzer did not return a timeline. Check your LLM Connection!")