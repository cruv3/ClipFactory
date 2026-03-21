import math
import re
from moviepy.editor import TextClip, CompositeVideoClip
from config import FONT_PATH
import os

class VideoTextEngine:
    def __init__(self, font_path=FONT_PATH, base_fontsize=100):
        self.font = font_path
        self.base_fontsize = base_fontsize
        self.color_active = "#FFDD00"
        self.stroke_active_color = "#B8860B"
        self.color_inactive = "#FFFFFF"
        self.stroke_inactive_color = "#B0B0B0"
        self.stroke_width = 6.0

    def clean_for_match(self, word):
        return re.sub(r'[^A-Z0-9]', '', word)

    def make_clean_text(self, txt, c_fill, c_stroke):
        bg_clip = TextClip(
            txt=txt, fontsize=self.base_fontsize, font=self.font,
            color=c_stroke, stroke_color=c_stroke, 
            stroke_width=self.stroke_width * 2, method='label'
        )
        fg_clip = TextClip(
            txt=txt, fontsize=self.base_fontsize, font=self.font,
            color=c_fill, method='label'
        )
        return CompositeVideoClip([bg_clip, fg_clip.set_position('center')], size=bg_clip.size)
    
    def generate_text_overlays(self, word_data, video_width, action_words=[]):
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