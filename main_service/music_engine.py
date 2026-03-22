import os
import random
import yt_dlp

class MusicEngine:
    def __init__(self):
        pass

    def fetch_background_music(self, strategy):
        safe_query = f"{strategy.bg_music_query} royalty free background music no copyright"
        print(f"\n[*] 🎵 Searching YouTube for Commercial-Safe Music: '{safe_query}'")
        
        os.makedirs(strategy.output_dir, exist_ok=True)
        
        final_mp3 = os.path.join(strategy.output_dir, "bg_music.mp3")
        
        if os.path.exists(final_mp3):
            print(f"[+] 🎵 Background music already exists at {final_mp3}")
            return final_mp3

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(strategy.output_dir, 'bg_music.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'quiet': True,
            'noprogress': True,
            'noplaylist': True,
            # Suchfilter: Keine 10-Stunden-Loops (max 10 Minuten)
            'match_filter': yt_dlp.utils.match_filter_func("duration < 600"), 
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Wir holen die Top 3 Ergebnisse
                search_query = f"ytsearch3:{safe_query}"
                info = ydl.extract_info(search_query, download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    print("[-] [!] No royalty free music found.")
                    return None

                # Wir wählen zufällig eines der Top 3 Ergebnisse aus (für Abwechslung)
                entries = list(info['entries'])
                chosen_track = random.choice(entries)
                print(f"[*] Downloading Track: '{chosen_track.get('title', 'Unknown')}'")

                # Track herunterladen
                ydl.download([chosen_track['webpage_url']])

            if os.path.exists(final_mp3):
                print(f"[+] 🎵 Commercial-Safe Music saved successfully: {final_mp3}")
                return final_mp3
            else:
                print("[-] [!] Music download failed (File not found after conversion).")
                return None

        except Exception as e:
            print(f"[!] Fehler beim Audio-Download via yt-dlp: {e}")
            return None

# --- TEST RUN ---
if __name__ == "__main__":
    import dataclasses

    @dataclasses.dataclass
    class MockStrategy:
        bg_music_query: str
        output_dir: str

    test_strategy = MockStrategy(
        bg_music_query="creepy tense dark piano",
        output_dir="data/test_music_run"
    )

    music_eng = MusicEngine()
    music_eng.fetch_background_music(test_strategy)