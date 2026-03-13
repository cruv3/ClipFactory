import json
import os
import time
import requests
import yt_dlp
from datetime import datetime

from config import (
    OLLAMA_MODEL, OLLAMA_GENERATE_URL, VIDEO_HISTORY_JSON, STRATEGY_LOG
)
from ollama_provider import OllamaProvider

class StatReporter(OllamaProvider):
    def __init__(self):       
        super().__init__()
        self._ensure_history_file()

    def let_ai_analyze(self):
        print("\n[*] Preparing data for AI analysis...")
        history_data = self._fetch_current_stats()
        
        if not history_data:
            print("[!] No history data to analyze.")
            return
            
        stats_text = "Here is the performance data of our recent videos:\n\n"
        for v in history_data:
            stats_text += f"- URL: {v.get('url', 'N/A')} | Subreddit: {v['subreddit']} | Voice: {v['voice']} | Hook: {v['hook_style']} -> VIEWS: {v['views']}, LIKES: {v['likes']}\n"

        prompt = f"""
        You are the Lead Data Analyst for a highly successful Reddit Story channel on TikTok, YouTube Shorts and Instagram-Reels.
        Here are our current video statistics:
        
        {stats_text}
        
        Write 3 extremely short, precise rules for future videos based strictly on this data.
        Analyze which combination of Subreddit, Voice, and Hook brings the most views.
        Do NOT write any intro or outro. Output only the 3 rules.
        """
        
        print("[*] 🧠 Ollama is analyzing the stats and generating a strategy...")
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(OLLAMA_GENERATE_URL, json=payload)
            response.raise_for_status()
            
            data = response.json()
            ai_response = data.get("response", "").strip()
            
            # Save the AI rules to a text file for the StoryAnalyzer to read later
            with open(STRATEGY_LOG, "w", encoding="utf-8") as f:
                f.write(ai_response)
                
            print(f"[+] AI successfully updated the strategy: {STRATEGY_LOG}")
            print("\n=== NEW AI STRATEGY RULES ===")
            print(ai_response)
            print("=============================\n")

            with open(VIDEO_HISTORY_JSON, "w", encoding="utf-8") as f:
                json.dump([], f)
            print("Video history JSON has been wiped clean for the next cycle.")
            
        except requests.exceptions.ConnectionError:
            print("[!] ERROR: Could not connect to Ollama.")
        except Exception as e:
            print(f"[!] An error occurred during AI analysis: {e}")

    def _fetch_current_stats(self):
        print("\n[*] Starting stealth scrape of video statistics...")
        
        with open(VIDEO_HISTORY_JSON, "r", encoding="utf-8") as f:
            history = json.load(f)

        if not history:
            print("[!] No videos found in history.")
            return []

        for video in history:
            url = video.get('url')
            if not url:
                continue
                
            print(f"[*] Checking stats for: {url}")
            stats = self._get_stats_via_ytdlp(url)
            
            # Update the entries
            video['views'] = stats['views']
            video['likes'] = stats['likes']
            video['comments'] = stats['comments']
            
            time.sleep(3) 

        # Save updated data
        with open(VIDEO_HISTORY_JSON, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
            
        print("[+] All statistics updated successfully!")
        return history

    def _ensure_history_file(self):
        if not os.path.exists(VIDEO_HISTORY_JSON):
            os.makedirs(os.path.dirname(VIDEO_HISTORY_JSON), exist_ok=True)
            with open(VIDEO_HISTORY_JSON, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _get_stats_via_ytdlp(self, url):
        ydl_opts = {
            'quiet': True,
            'skip_download': True, # IMPORTANT: No download, just data!
            'no_warnings': True,
            'extract_flat': False
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                views = info.get('view_count') or 0
                likes = info.get('like_count') or 0
                comments = info.get('comment_count') or 0
                
                return {"views": views, "likes": likes, "comments": comments}
                
        except Exception as e:
            print(f"[!] Error scraping {url}: {e}")
            return {"views": 0, "likes": 0, "comments": 0}
