import os
import random
import platform
import numpy as np
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.config import change_settings
from moviepy.editor import (
    CompositeAudioClip, VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, 
    ColorClip, ImageClip
)
import moviepy.video.fx.all as vfx

# Workaround für PIL Versionen
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from config import TEST_RUN, FONT_PATH
from utils import get_available_chunk, get_random_username

# ImageMagick Setup
if platform.system() == "Windows":
    IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
    change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})
else:
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

class VideoEngine:
    def __init__(self, is_test=False):
        self.card_width = 900
        
        self.bg_color_rgb = (0, 18, 43)
        self.highlight_color = "#FFDD00"
        
        self.line_height = 55 
        self.font_size = 42       # Für den Haupt-Story-Text
        self.caption_size = 48    # Startgröße für den Hook oben
        
        self.max_visible_lines = 8
        self.corner_radius = 40

        self.shadow_color_rgba = (0, 0, 0, 160)
        self.shadow_blur = 6                    
        self.shadow_offset_x = 18               
        self.shadow_offset_y = 18               
        self.shadow_pad = 50

        # 2. RENDER SETTINGS
        if is_test:
            self.res_height = 854
            self.fps = 10
            self.preset = "ultrafast"
            self.bitrate = "800k"
        else:
            self.res_height = 1920
            self.fps = 30
            self.preset = "slow" 
            self.bitrate = "8000k"
        
        self.logger = "bar"
        self.res_width = int((self.res_height * (9 / 16)) // 2) * 2

    def _draw_card_background(self, height):
        W, H = self.card_width, height
        
        full_w = W + self.shadow_pad + self.shadow_offset_x
        full_h = H + self.shadow_pad + self.shadow_offset_y
        
        img = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))

        s_x = (self.shadow_pad // 2) + self.shadow_offset_x
        s_y = (self.shadow_pad // 2) + self.shadow_offset_y
        
        shadow_img = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        shadow_draw.rounded_rectangle([s_x, s_y, s_x + W, s_y + H], radius=self.corner_radius, fill=self.shadow_color_rgba)
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(self.shadow_blur))

        card_img = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_img)
        c_x, c_y = self.shadow_pad // 2, self.shadow_pad // 2

        border_size = 1
        
        card_draw.rounded_rectangle(
            [c_x - border_size, c_y - border_size, c_x + W, c_y + H], 
            radius=self.corner_radius, 
            fill=(255, 255, 255, 255) 
        )

        card_draw.rounded_rectangle([c_x, c_y, c_x + W, c_y + H], radius=self.corner_radius, fill=self.bg_color_rgb + (255,))

        img.paste(shadow_img, (0, 0))
        img.paste(card_img, (0, 0), card_img)
        
        return ImageClip(np.array(img))
  

    def _create_profile_icon(self, size=(80, 80), username=None):
        upscale = 4
        canvas_size = (size[0] * upscale, size[1] * upscale)
        img = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        colors = [
            (255, 69, 0), (0, 121, 211), (70, 209, 96), (113, 147, 255),
            (156, 39, 176), (233, 30, 99), (0, 150, 136), (255, 193, 7),
            (96, 125, 139), (244, 67, 54), (103, 58, 183), (3, 169, 244),
            (0, 188, 212), (255, 139, 0), (205, 220, 57)
        ]
        bg_color = random.choice(colors)
        
        draw.ellipse([0, 0, canvas_size[0], canvas_size[1]], fill=bg_color)
        
        border_width = 2 * upscale
        draw.ellipse(
            [border_width, border_width, canvas_size[0] - border_width, canvas_size[1] - border_width], 
            outline=(255, 255, 255, 40), 
            width=border_width
        )

        if username:
            clean_name = ''.join(filter(str.isalnum, username))
            letter = clean_name[0].upper() if clean_name else random.choice(string.ascii_uppercase)
        else:
            letter = random.choice(string.ascii_uppercase)
        
        font_size = int(canvas_size[1] * 0.6) 
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()
        
        shadow_offset = 1 * upscale
        draw.text(
            (canvas_size[0]//2 + shadow_offset, canvas_size[1]//2 + shadow_offset), 
            letter, fill=(0, 0, 0, 70), font=font, anchor="mm"
        )
        
        draw.text((canvas_size[0]//2, canvas_size[1]//2), letter, fill="white", font=font, anchor="mm")
        
        return ImageClip(np.array(img.resize(size, Image.LANCZOS)))

    def _build_ui_card(self, word_data, strategy, duration):
        if not word_data: return ColorClip((10,10), color=(0,0,0)).set_opacity(0)
        
        text_clips, line_starts = self._get_cumulative_text_clips(word_data, duration)
        sorted_lines = sorted(line_starts.keys())
        off = self.shadow_pad // 2

        # --- 1. DYNAMISCHER HOOK (Max 2 Zeilen) ---
        max_hook_w = self.card_width - 80
        current_size = self.caption_size # <--- Nutzt jetzt die neue Variable
        
        while current_size > 24:
            hook = TextClip(strategy.reason, fontsize=current_size, color="white", font=FONT_PATH, 
                            method='caption', size=(max_hook_w, None), align='West')
            if hook.h <= 100: # Leicht angepasst, da Schrift jetzt 48 ist
                break
            hook.close()
            current_size -= 2

        hook = hook.set_duration(duration).set_position((40 + off, 125 + off))
        
        dynamic_header_height = 125 + hook.h + 30

        # --- 2. CARD GRÖSSE BERECHNEN ---
        max_display = min(max(sorted_lines) + 1, self.max_visible_lines) if sorted_lines else 1
        max_h = dynamic_header_height + (max_display * self.line_height) + 20
        
        full_w = self.card_width + self.shadow_pad + self.shadow_offset_x
        full_h = max_h + self.shadow_pad + self.shadow_offset_y

        # --- 3. DYNAMISCHE HINTERGRÜNDE ---
        bg_clips = []
        for i, line_idx in enumerate(sorted_lines):
            start_t = line_starts[line_idx]
            end_t = line_starts[sorted_lines[i+1]] if i+1 < len(sorted_lines) else duration
            
            display_lines = min(line_idx + 1, self.max_visible_lines)
            curr_h = dynamic_header_height + (display_lines * self.line_height) + 20
            
            clip = self._draw_card_background(curr_h).set_start(start_t).set_duration(max(0.1, end_t - start_t))
            clip = clip.set_position(('left', 'top')) 
            bg_clips.append(clip)

        dynamic_background = CompositeVideoClip(bg_clips, size=(full_w, full_h))
    
        # --- 4. STATISCHE HEADER INHALTE ---
        generated_username = get_random_username()
        icon = self._create_profile_icon(username=generated_username).set_duration(duration).set_position((40 + off, 30 + off))
        name = TextClip(generated_username, fontsize=40, color="white", font=FONT_PATH).set_duration(duration).set_position((140 + off, 50 + off))

        # --- 5. TEXT SCROLLING LOGIK ---
        def scroll_logic(t):
            curr = 0
            for wd in word_data:
                if t >= wd["start"]: curr = wd["line"]
            if curr >= self.max_visible_lines:
                return (0, -(curr - (self.max_visible_lines - 1)) * self.line_height)
            return (0, 0)

        viewport_h = self.line_height * self.max_visible_lines
        text_container = CompositeVideoClip(
            [CompositeVideoClip(text_clips, size=(self.card_width-80, 2000)).set_position(scroll_logic)],
            size=(self.card_width-80, viewport_h)
        ).set_position((40 + off, dynamic_header_height + off))

        return CompositeVideoClip([
            dynamic_background,
            icon, name, hook,
            text_container
        ], size=(full_w, full_h)).set_duration(duration)
    
    # --- TEXT & LOGIK ---

    def _get_cumulative_text_clips(self, word_data, duration):
        max_w = self.card_width - 80
        x, y = 0, 0
        
        start_t = word_data[0]["start"] if word_data else 0
        line_starts = {0: start_t}
        clips = []

        for i, wd in enumerate(word_data):
            txt_str = wd["word"]
            tw = TextClip(txt_str, fontsize=self.font_size, font=FONT_PATH).w # Nutzt self.font_size (48)
            
            if x + tw > max_w:
                x = 0
                y += self.line_height
                line_starts[y // self.line_height] = wd["start"]

            line_t = line_starts[y // self.line_height]
            
            base = TextClip(txt_str, fontsize=self.font_size, color="white", font=FONT_PATH)\
                   .set_start(line_t).set_duration(max(0.1, duration - line_t)).set_position((x, y))
            
            end_t = word_data[i+1]["start"] if i+1 < len(word_data) else duration
            high = TextClip(txt_str, fontsize=self.font_size, color=self.highlight_color, font=FONT_PATH)\
                   .set_start(wd["start"]).set_duration(max(0.1, end_t - wd["start"])).set_position((x, y))
            
            clips.extend([base, high])
            wd["line"] = y // self.line_height
            x += tw + 10

        return clips, line_starts
    
    def _merge_script_with_timestamps(self, original_script, word_data):
        script_words = original_script.split()
        merged_data = []
        min_len = min(len(script_words), len(word_data))
        
        for i in range(min_len):
            merged_data.append({
                "word": script_words[i],
                "start": word_data[i]["start"],
                "end": word_data[i]["end"]
            })
            
        last_end = word_data[-1]["end"] if word_data else 0
        for i in range(min_len, len(script_words)):
            merged_data.append({
                "word": script_words[i],
                "start": last_end,
                "end": last_end + 0.3
            })
            last_end += 0.3
            
        return merged_data

    def create_video(self, original_script, word_timestamps, strategy, voice_path=None, bg_music_path=None):
        print(f"[*] Starting Production: {strategy.folder_name} ({self.res_height}p)")
        os.makedirs(strategy.output_dir, exist_ok=True)
        bg_path = get_available_chunk(strategy.folder_name, strategy.search_query)
        if not bg_path: return None

        try:
            merged_words = self._merge_script_with_timestamps(original_script, word_timestamps)

            audio = AudioFileClip(voice_path) if voice_path else None
            dur = audio.duration if audio else merged_words[-1]["end"] + 0.5
            if bg_music_path:
                music = AudioFileClip(bg_music_path).volumex(0.1).set_duration(dur)
                audio = CompositeAudioClip([audio, music]) if audio else music

            video = VideoFileClip(bg_path).subclip(0, dur).resize(height=self.res_height)
            v_w, v_h = video.size
            video = vfx.crop(video, width=int(v_h*(9/16)), height=v_h, x_center=v_w/2, y_center=v_h/2)

            ui_card = self._build_ui_card(merged_words, strategy, dur)
            if self.res_height < 1920: ui_card = ui_card.resize(self.res_height / 1920)

            x_offset_left = 20
            final = CompositeVideoClip([video, ui_card.set_position((x_offset_left, 'center'))], 
                                      size=(self.res_width, self.res_height)).set_audio(audio)

            output = os.path.join(strategy.output_dir, f"{strategy.folder_name}.mp4")
            final.write_videofile(
                output, 
                fps=self.fps, 
                codec="libx264", 
                bitrate=self.bitrate, 
                preset=self.preset, 
                logger=self.logger,
                threads=12 
            )
            return output

        except Exception as e:
            print(f"[!] Error: {e}"); return False
        finally:
            if 'video' in locals(): video.close()
            if 'audio' in locals() and audio: 
                try: audio.close()
                except: pass

# --- MAIN TEST BLOCK ---
if __name__ == "__main__":
    from voice_engine import VoiceEngine 
    import dataclasses

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
    strategy = MockStrategy(
        voice="am_michael",
        voice_speed=1.1,
        hook_style="Humorous",
        folder_name="satisfying_sand",
        output_dir="data/test_run_sand",
        search_query="kinetic sand cutting with cookie cutters no commentary 4k",
        reason="Drama at the office... What can we see about that? Issue?",
        caption="He said WHAT about my lunches?! 😭😭 #husbandproblems",
        description="This wife's sweet gestures backfired!",
        tags="#lunchboxfails #couplecomedy",
        action_words=["HEART", "LIED", "CAUGHT", "POLAROID", "LAWYER"],
        bg_music_query="sneaky suspicious comedic background music no copyright"
    )

    script = "I quietly stopped going to the office... and no one noticed for three months. My company did the classic we are better together thing and told everyone to come in two days a week. I just stayed home."

    v_eng = VoiceEngine()
    audio_file = v_eng.generate_audio(script, strategy)
    word_timestamp = v_eng.get_word_timestamps(audio_file)

    engine = VideoEngine(is_test=True)
    engine.create_video(script, word_timestamp, strategy)