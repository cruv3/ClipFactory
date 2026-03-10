import requests

def rewrite_for_tiktok(raw_text, hook_style="Shocking"):
    print(f"\n[*] 🧠 Ollama is rewriting the script (Hook Style: {hook_style})...")
    
    # The magic prompt that formats the text for TikTok
    prompt = f"""
    You are a professional TikTok scriptwriter. 
    Rewrite the following Reddit story into a captivating, viral script for a 60-second video.
    
    RULES:
    1. The first sentence MUST be an extreme hook (Style: {hook_style}) that immediately grabs the viewer's attention.
    2. Use extremely short, concise sentences. No complex phrasing! Perfect for an AI TTS voice.
    3. Omit unimportant details, get straight to the climax of the story.
    4. No greetings (like "Hey guys") and no hashtags at the end.
    5. Write ONLY the spoken text. No stage directions, no [brackets].
    
    Here is the original story:
    {raw_text}
    """
    
    # Default address for Ollama (running locally on port 11434)
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2",  # Adjust if using a different model
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Throws an error if Ollama is unreachable
        
        data = response.json()
        script = data.get("response", "").strip()
        
        print("[+] Script generated successfully!\n")
        return script
        
    except requests.exceptions.ConnectionError:
        print("[!] ERROR: Could not connect to Ollama.")
        print("[!] Is Ollama running in the background? (Check http://localhost:11434 in your browser)")
        return None
    except Exception as e:
        print(f"[!] An error occurred: {e}")
        return None

# --- TEST RUN ---
if __name__ == "__main__":
    # A small test text to see if Ollama responds
    test_story = "Yesterday I noticed my dog staring at the blank wall at night, growling. I thought it was a mouse at first, but then I heard someone whispering my name from inside the wall."
    
    finished_script = rewrite_for_tiktok(test_story, "Mysterious")
    
    if finished_script:
        print("=== GENERATED TIKTOK SCRIPT ===")
        print(finished_script)
        print("===============================")