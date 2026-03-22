import os
import time
import pickle
import json
import shutil
import asyncio

from instagrapi import Client
from playwright.async_api import async_playwright
from moviepy.editor import VideoFileClip
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import (
    IG_USERNAME, IG_PASSWORD, 
    TIKTOK_COOKIES, TIKTOK_USERNAME,
    YOUTUBE_CLIENT_SECRETS, YOUTUBE_TOKEN_PICKLE, YOUTUBE_SCOPES, VIDEO_HISTORY_JSON, IG_SETTINGS_FILE
)

class VideoUploader:
    async def distribute_video(self, video_path, strategy):
        results = {}
        final_tags = f"{strategy.tags} #shorts #viral"
        caption = f"{strategy.caption}\n\n{final_tags}"
        yt_title = strategy.caption[:100]

        platforms = [
            {"name": "Instagram", "func": lambda: self._upload_to_instagram(video_path, caption)},
            {"name": "TikTok", "func": lambda: self._upload_to_tiktok(video_path, caption)},
            {"name": "YouTube", "func": lambda: self._upload_to_youtube(video_path, yt_title, caption, final_tags)}
        ]

        for p in platforms:
            success_url = None
            for attempt in range(1, 4):
                print(f"[*] Upload to {p['name']} - Attempt {attempt}/3...")
                try:
                    if p['name'] == "TikTok":
                        success_url = await self._upload_to_tiktok(video_path, caption)
                    else:
                        success_url = p['func']()

                    if success_url:
                        print(f"[+] {p['name']} upload successful!")
                        break 
                except Exception as e:
                    print(f"[!] Attempt {attempt} failed for {p['name']}: {e}")
                
                if attempt < 3:
                    await asyncio.sleep(30 * attempt)

            if success_url:
                results[p['name']] = success_url
                self._log_video_to_history(success_url, strategy, p['name'], video_path)
            else:
                results[p['name']] = "❌ Failed"

        temp_run_dir = os.path.dirname(video_path)
        if os.path.exists(temp_run_dir) and "__" in temp_run_dir:
            try:
                shutil.rmtree(temp_run_dir)
                print(f"[+] Run folder cleaned up: {temp_run_dir}")
            except Exception as e:
                print(f"[!] Could not cleanup run folder: {e}")

        return results

    def _get_video_duration(self, video_path):
            try:
                with VideoFileClip(video_path) as video:
                    return int(video.duration)
            except:
                return 0
            
    def _log_video_to_history(self, uploaded_url, strategy, platform, video_path):
        if not uploaded_url:
            return

        history_file = VIDEO_HISTORY_JSON
        history = []

        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                history = []

        # New Enhanced Entry
        new_entry = {
            "video_id": f"vid_{int(time.time())}",
            "platform": platform,
            "url": uploaded_url,
            "subreddit": strategy.folder_name,
            "voice": strategy.voice,
            "voice_speed": strategy.voice_speed,
            "hook_style": strategy.hook_style,
            "bg_music": strategy.bg_music_query,
            "bg_video_query": strategy.search_query,
            "duration": self._get_video_duration(video_path),
            "caption": strategy.caption,
            "tags": strategy.tags,
            "action_words": strategy.action_words,
            "posted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "views": 0,
            "likes": 0,
            "comments": 0,
        }

        history.append(new_entry)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)

    def _upload_to_instagram(self, video_path, caption):
        print(f"\n[*] Starting Instagram upload for: {video_path}")
        
        try:
            cl = Client()

            if os.path.exists(IG_SETTINGS_FILE):
                print("[*] Loading Instagram session from file...")
                cl.load_settings(IG_SETTINGS_FILE)
            
            cl.login(IG_USERNAME, IG_PASSWORD)
            cl.dump_settings(IG_SETTINGS_FILE)
            # upload_clip is specifically for Reels
            media = cl.clip_upload(
                path=video_path,
                caption=caption
            )
            
            # Construct the URL from the media code
            ig_url = f"https://www.instagram.com/reel/{media.code}/"
            print(f"[+] Instagram upload successful! URL: {ig_url}")
            return ig_url
            
        except Exception as e:
            print(f"[!] Instagram upload failed: {e}")
            return None

    def _upload_to_youtube(self, video_path, title, description, tags):
        print(f"\n[*] Starting YouTube upload for: {video_path}")
        youtube = self._get_youtube_service()
        
        if not youtube:
            print("[!] YouTube Upload abgebrochen (Keine API Verbindung).")
            return None

        try:
            if isinstance(tags, str):
                tag_list = [tag.strip().replace('#', '') for tag in tags.split() if tag.strip()]
            else:
                tag_list = tags

            body = {
                'snippet': {
                    'title': title[:100], 
                    'description': description,
                    'tags': tag_list,
                    'categoryId': '24' 
                },
                'status': {
                    'privacyStatus': 'public', 
                    'selfDeclaredMadeForKids': False
                }
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            print("[*] Lade zu YouTube hoch... Bitte warten.")
            response = request.execute()
            video_id = response.get('id')
            yt_url = f"https://www.youtube.com/shorts/{video_id}"
            print(f"[+] YouTube upload successful! URL: {yt_url}")
            
            return yt_url

        except Exception as e:
            print(f"[!] YouTube upload failed: {e}")
            return None

    def _get_youtube_service(self):
        """Holt oder erneuert das YouTube Access-Token."""
        creds = None
        
        # Lade gespeicherte Session, falls vorhanden
        if os.path.exists(YOUTUBE_TOKEN_PICKLE):
            with open(YOUTUBE_TOKEN_PICKLE, 'rb') as token:
                creds = pickle.load(token)
                
        # Wenn wir keine gültigen Zugangsdaten haben, müssen wir uns einloggen
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("[*] Erneuere abgelaufenes YouTube Token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(YOUTUBE_CLIENT_SECRETS):
                    print(f"[!] ERROR: {YOUTUBE_CLIENT_SECRETS} nicht gefunden!")
                    print("Lade die OAuth 2.0 Client-ID aus der Google Cloud Console herunter.")
                    return None
                    
                print("[*] Öffne Browser für erstmaligen YouTube Login...")
                # Öffnet ein lokales Browser-Fenster für den Google Login
                flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRETS, YOUTUBE_SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Speichere die neuen Zugangsdaten für das nächste Mal (die .pickle Datei)
            with open(YOUTUBE_TOKEN_PICKLE, 'wb') as token:
                pickle.dump(creds, token)
                
        return build('youtube', 'v3', credentials=creds)
    
    def _parse_netscape_cookies(self, file_path):
        cookies = []
        if not os.path.exists(file_path):
            return cookies

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Kommentare und leere Zeilen ignorieren
                if line.startswith('#') or not line.strip():
                    continue
                
                parts = line.strip().split('\t')
                if len(parts) < 7:
                    continue

                # Netscape Format zu Playwright Dictionary konvertieren
                cookie = {
                    'name': parts[5],
                    'value': parts[6],
                    'domain': parts[0],
                    'path': parts[2],
                    'secure': parts[3].upper() == 'TRUE',
                    'expires': int(float(parts[4])) if parts[4] != '0' else int(time.time() + 31536000),
                    'sameSite': 'None' # Oft nötig für TikTok
                }
                cookies.append(cookie)
        return cookies
    
    async def _upload_to_tiktok(self, video_path, caption):
        print(f"\n[*] Starting native TikTok Async upload (Modal-Buster Mode)...")

        async with async_playwright() as p:
            # Wir nutzen Chromium (Headless für Docker)
            browser = await p.chromium.launch(headless=True)
            
            # Session über die ID setzen
            context = await browser.new_context()
            await context.add_cookies(self._parse_netscape_cookies(TIKTOK_COOKIES))
            
            page = await context.new_page()
            # Wichtig: Ein großes Viewport hilft, dass Buttons nicht außerhalb des Bildes sind
            await page.set_viewport_size({"width": 1280, "height": 720})

            try:
                print("[*] Navigating to TikTok Upload...")
                await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="load")
                
                # 1. Datei hochladen
                print("[*] Uploading video file...")
                file_input = page.locator('input[type="file"]')
                await file_input.set_input_files(video_path)
                
                # 2. Warten, bis das Beschreibungsfeld da ist
                # TikTok braucht hier oft 5-10 Sekunden zum Initialisieren
                print("[*] Waiting for video processing...")
                editor = page.locator("//div[@contenteditable='true']")
                await editor.wait_for(state="visible", timeout=60000)

                # --- DER MODAL BUSTER ---
                # Wir drücken einmal 'Escape', um einfache Pop-ups zu schließen
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(2000)

                # 3. Beschreibung setzen
                print("[*] Setting description...")
                # 'force=True' klickt DURCH das TUX-Overlay hindurch!
                await editor.click(force=True) 
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                
                await page.keyboard.type(caption)
                print("[+] Description set.")

                # 4. Posten
                # Wir warten kurz, bis der Post-Button aktiv wird
                post_btn = page.get_by_role("button", name="Post")

                
                print("[*] Clicking Post button...")
                post_btn = page.get_by_role("button", name="Post")
                await post_btn.click(timeout=120000)
                
                post_now_btn = page.get_by_text("Post now")
                if await post_now_btn.is_visible():
                    print("[!] Modal: 'Continue to post?' detected. Clicking 'Post now'...")
                    await post_now_btn.click(force=True)

                print("[*] Waiting for video link...")
                try:
                    await page.wait_for_selector('a[data-tt="components_PostInfoCell_a"]', timeout=20000)
                    video_link_locator = page.locator('a[data-tt="components_PostInfoCell_a"]').first
                    relative_url = await video_link_locator.get_attribute("href")
                    if relative_url:
                        full_url = f"https://www.tiktok.com{relative_url}" if relative_url.startswith("/") else relative_url
                        print(f"[*] Video link extracted: {full_url}")
                        return full_url
                except Exception as e:
                    print(f"[!] Link extraction failed: {e}")
                    debug_img = f"data/tiktok_stuck_after_post_{int(time.time())}.png"
                    await page.screenshot(path=debug_img)
                    print(f"[🔍] Saved DEBUG SCREENSHOT to see what blocked the upload: {debug_img}")

                return f"https://www.tiktok.com/@{TIKTOK_USERNAME}"

            except Exception as e:
                # Screenshot für die Diagnose im Docker speichern
                error_img = f"data/tiktok_error_{int(time.time())}.png"
                await page.screenshot(path=error_img)
                print(f"[!] TikTok Error: {e}. Screenshot saved to {error_img}")
                return None
            finally:
                await browser.close()

# --- TEST RUN ---
if __name__ == "__main__":
    from utils import StoryStrategy
    
    mock_strat = StoryStrategy(
        voice="am_onyx",
        hook_style="Shocking",
        folder_name="AmItheAsshole",
        output_dir="data/story_001_test",
        search_query="minecraft parkour gameplay long no commentary no copyright",
        reason="Deep voice matches the serious tone of the family drama.",
        caption="Am I the idiot for ruining my sister's wedding? 👰🔥",
        description="My sister wanted a child-free wedding, but I brought my kids anyway. Now the whole family is divided. Who is wrong here?",
        tags="#aita #redditstories #familydrama #wedding #storytime #minecraft",
        voice_speed=1.0,
        bg_music_query="test_this",
        action_words=["test"],
    )
    test_video_file = "data/This app took meetings from blah to BRILLIANT!.mp4"

    async def run_test():
        uploader = VideoUploader()
        
        if not os.path.exists(test_video_file):
            print(f"[!] TEST ABORTED: File not found at {test_video_file}")
            return

        print(f"[*] Starting test upload for: {test_video_file}")
        #await uploader._upload_to_tiktok(test_video_file, mock_strat.caption)
        await uploader._upload_to_instagram(test_video_file, "This app took meetings from blah to BRILLIANT! 😂🏆")
        print("\n=== FINAL UPLOAD REPORT COMPLETE ===")

    asyncio.run(run_test())