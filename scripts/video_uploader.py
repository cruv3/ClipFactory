import os
import time
import pickle
import json
import shutil
import asyncio

from instagrapi import Client
from tiktok_uploader.upload import upload_video

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
        if not os.path.exists(video_path):
            print(f"[!] Cannot upload, file not found: {video_path}")
            return

        final_tags = f"{strategy.tags} #shorts #viral"

        caption = f"{strategy.caption}\n\n{final_tags}"
        yt_title = strategy.caption[:100]

        # Instagram
        ig_url = self._upload_to_instagram(video_path, caption)
        if ig_url: self._log_video_to_history(ig_url, strategy)
        
        # TikTok
        tk_url = await asyncio.to_thread(self._upload_to_tiktok, video_path, caption)
        if tk_url: self._log_video_to_history(tk_url, strategy)
        
        # YouTube
        yt_url = self._upload_to_youtube(video_path, yt_title, caption, final_tags)
        if yt_url: self._log_video_to_history(yt_url, strategy)

        temp_run_dir = os.path.dirname(video_path)
        if os.path.exists(temp_run_dir) and "__" in temp_run_dir:
            try:
                shutil.rmtree(temp_run_dir)
                print(f"[+] Run folder cleaned up: {temp_run_dir}")
            except Exception as e:
                print(f"[!] Could not cleanup run folder: {e}")


    
    def _log_video_to_history(self, uploaded_url, strategy):
        if not uploaded_url:
            return

        history_file = VIDEO_HISTORY_JSON
        history = []

        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []

        new_entry = {
            "video_id": f"vid_{int(time.time())}",
            "url": uploaded_url,
            "subreddit": strategy.folder_name,
            "voice": strategy.voice,
            "hook_style": strategy.hook_style,
            "caption": strategy.caption,
            "views": 0,
            "likes": 0,
            "comments": 0,
        }

        history.append(new_entry)
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            print(f"[+] Video-Historie updated: {history_file}")
        except Exception as e:
            print(f"[!] Error writing to {history_file}: {e}")

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

    def _upload_to_tiktok(self, video_path, caption):
        print(f"\n[*] Starting TikTok upload for: {video_path}")
        
        if not os.path.exists(TIKTOK_COOKIES):
            print("[!] TikTok cookies file not found! Skipping TikTok upload.")
            return None
            
        try:
            failed = upload_video(
                filename=video_path,
                description=caption,
                cookies=TIKTOK_COOKIES,
                headless=True # Set to False if you want to watch it happen!
            )
            
            if not failed:
                print("[+] TikTok upload successful!")
                return f"https://www.tiktok.com/@{TIKTOK_USERNAME}"
            else:
                print("[!] TikTok upload failed.")
                return None
                
        except Exception as e:
            print(f"[!] TikTok upload threw an error: {e}")
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
        tags="#aita #redditstories #familydrama #wedding #storytime #minecraft"
    )
    
    uploader = VideoUploader()
    #urls = uploader.distribute_video("data/test/test_story.mp4", mock_strat)
    uploader._upload_to_instagram("test", "test")
    print("\n=== FINAL UPLOAD REPORT ===")