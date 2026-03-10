import requests
import os

USED_POSTS_FILE = "data/used_posts.txt"

def load_used_posts():
    if not os.path.exists(USED_POSTS_FILE):
        return set()
    with open(USED_POSTS_FILE, "r") as f:
        return set(line.strip() for line in f)
    
def save_used_post(post_id):
    with open(USED_POSTS_FILE, "a") as f:
        f.write(f"{post_id}\n")

def clean_used_posts():
    open(USED_POSTS_FILE, 'w').close()

def get_top_reddit_story(subreddits):
    print("\n[*] start multi-subreddit analyse...")

    used_posts = load_used_posts()
    print(f"[*] Found {len(used_posts)} already used stories in memory.")
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 HeadlessViralEngine/1.1'
    }

    combined_subs = "+".join(subreddits)
    print(f"[*] Fetching combined feed: r/{combined_subs}")

    url = f"https://www.reddit.com/r/{combined_subs}/top.json?limit=25&t=day"
    

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        for child in data['data']['children']:
            post = child['data']
            post_id = post.get('id')

            if post_id in used_posts:
                print(f"    [-] Skipping '{post_id}' (Already used)")
                continue

            title = post.get('title', '')
            text = post.get('selftext', '')
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            sub = post.get('subreddit', '')

            if len(text) < 50:
                continue

            print("\n==========================================")
            print(f"NEW STORY FOUND !")
            print(f"Subreddit: r/{sub}")
            print(f"Engagement: {score} Upvotes & {comments} Comments")
            print("==========================================\n")

            save_used_post(post_id)
            return f"{title}. {text}"

    except Exception as e:
        print(f"[!] Error scraping Reddit: {e}")
        return None
    
    print("[!] No posts found.")
    return None
    
if __name__ == "__main__":
    subreddits = [
        "ShortScaryStories", 
        "TrueOffMyChest", 
        "AmItheAsshole", 
        "confessions",
        "pettyrevenge"
    ]
    
    story = get_top_reddit_story(subreddits)