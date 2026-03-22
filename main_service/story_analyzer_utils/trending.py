import requests
import json 

def get_trending_backgrounds():
    """Holt die aktuellsten Suchtrends für Background-Videos direkt von YouTube."""

    base_queries = [
        # --- KATEGORIE 1: High-Speed & Focus Gaming (Hält die Augen auf dem Screen) ---
        "gta 5 parkour no commentary",
        "gta 5 mega ramp no commentary",
        "minecraft parkour gameplay no commentary",
        "subway surfers gameplay no commentary",
        "csgo surf gameplay no commentary",
        "trackmania stunts no commentary",
        
        # --- KATEGORIE 2: Oddly Satisfying (Beruhigend, gut für emotionale Stories) ---
        "satisfying kinetic sand cutting asmr",
        "satisfying slime mixing no commentary",
        "soap cutting asmr 4k",
        "oddly satisfying 3d animation loop",
        "power washing satisfying no commentary",
        "carpet cleaning satisfying asmr",
        
        # --- KATEGORIE 3: Chaos & Zerstörung (Perfekt für Drama, Revenge & Wut-Stories) ---
        "beamng drive crashes no commentary",
        "hydraulic press satisfying no commentary",
        "shredding machine satisfying video"
    ]
    
    trending_keywords = []
    
    for query in base_queries:
        url = f"http://suggestqueries.google.com/complete/search?client=chrome&ds=yt&q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            suggestions = json.loads(response.text)[1]

            trending_keywords.extend(suggestions[:3])
        except Exception as e:
            print(f"[!] Konnte Trends für '{query}' nicht laden: {e}")
            
    return trending_keywords