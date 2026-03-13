import requests
import os

from config import USED_POSTS_LOG

class RedditScraper():
    def __init__(self):
        self.used_posts = self._load_used_posts()
        self.headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 HeadlessViralEngine/1.1'
        }
        self.subreddits= [
            "AmItheAsshole", 
            "TrueOffMyChest", 
            "tifu",
            "BestofRedditorUpdates",
            "EntitledParents", 
            "MaliciousCompliance", 
            "LetsNotMeet",
            "ShortScaryStories"
        ]

    def get_top_story(self, limit=25):
        print("\n[*] Starting multi-subreddit analysis...")
        print(f"[*] Found {len(self.used_posts)} already used stories in memory.")

        combined_subs = "+".join(self.subreddits)
        url = f"https://www.reddit.com/r/{combined_subs}/top.json?limit={limit}&t=day"
        
        print(f"[*] Fetching combined feed: r/{combined_subs}")

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            for child in data['data']['children']:
                post = child['data']
                post_id = post.get('id')

                # Check ob die Story schon mal genutzt wurde
                if post_id in self.used_posts:
                    continue

                title = post.get('title', '')
                text = post.get('selftext', '')
                
                word_count = len(text.split())
                # Qualitäts-Check: Zu kurze Texte ignorieren
                if word_count < 100:
                    self._save_used_post(post_id)
                    continue

                score = post.get('score', 0)
                sub = post.get('subreddit', '')

                print("\n==========================================")
                print(f"NEW STORY FOUND IN r/{sub}")
                print(f"Engagement: {score} Upvotes")
                print("==========================================\n")

                self._save_used_post(post_id)
                # Kombiniere Titel und Text für den Rewriter
                return f"{title}. {text}"

        except Exception as e:
            print(f"[!] Error scraping Reddit: {e}")
            return None
        
        return None
    
    def _save_used_post(self, post_id):
            self.used_posts.add(post_id)
            with open(USED_POSTS_LOG, "a") as f:
                f.write(f"{post_id}\n")

    def _load_used_posts(self):
        if not os.path.exists(USED_POSTS_LOG):
            return set()
        with open(USED_POSTS_LOG, "r") as f:
            return set(line.strip() for line in f)

# --- TEST RUN ---
if __name__ == "__main__":
    scraper = RedditScraper()

    story = scraper.get_top_story()
    
    if story:
        print(story + "...")
        print(len(story.split()))
    else:
        print("No new stories found today.")