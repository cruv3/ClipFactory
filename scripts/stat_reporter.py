import json
import os
import time
import requests
import yt_dlp

from config import (
    OLLAMA_MODEL, OLLAMA_MODEL_BACKUP ,OLLAMA_GENERATE_URL, VIDEO_HISTORY_JSON, STRATEGY_LOG
)
from scripts.ai_service_provider import OllamaProvider

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
        You are the Lead Data Analyst and Viral Content Strategist for a highly successful Reddit Story channel on TikTok, YouTube Shorts, and Instagram Reels.
        
        Here is the performance data of our recent videos:
        {stats_text}
        
        Analyze this data deeply to find patterns. Structure your response EXACTLY using the following sections:

        ### 1. Key Insights & Reasoning
        Analyze which combination of Subreddit, Voice, and Hook generated the highest views and engagement (Likes to Views ratio). 
        Explain WHY you think these specific combinations worked or failed. Base your reasoning on short-form video audience psychology (e.g., attention spans, emotional triggers).

        ### 2. Strategic Recommendations
        Based on your insights, suggest 2 or 3 new strategic combinations or slight variations we should test in the next batch of videos to maximize viral potential.

        ### 3. ACTIONABLE RULES FOR NEXT BATCH
        Write 3 to 5 strict, precise rules based strictly on this data. These rules will be fed directly into our AI Video Generator. 
        Keep these rules direct and commanding (e.g., "Always pair Voice X with Subreddit Y", "Avoid Hook style Z").
        """
        
        print("[*] 🧠 Ollama is analyzing the stats and generating a strategy...")

        models_to_try = [OLLAMA_MODEL]
        if OLLAMA_MODEL_BACKUP:
            models_to_try.append(OLLAMA_MODEL_BACKUP)
        
        for current_model in models_to_try:
            print(f"\n[*] 🧠 Ollama creating stat report using model: '{current_model}'...")
        
            payload = {
                "model": current_model,
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

                if response.status_code == 200:
                    with open(VIDEO_HISTORY_JSON, "w", encoding="utf-8") as f:
                        json.dump([], f)
                    print("Video history JSON has been wiped clean for the next cycle.")
                    return
                
            except requests.exceptions.ConnectionError:
                print("[!] ERROR: Could not connect to Ollama.")
            except Exception as e:
                print(f"[!] An error occurred during AI analysis: {e}")

        print(f"[!] ERROR: All models exhausted. Could not generate a stat report.")
        return None

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

if __name__ == "__main__":
    reporter = StatReporter()
    
    # Run the analysis cycle
    reporter.let_ai_analyze()