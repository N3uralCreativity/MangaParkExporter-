import xml.etree.ElementTree as ET
import requests
import time
from difflib import SequenceMatcher

# --------- CONFIG ---------
INPUT_XML = "mangapark_follows_mal.xml"
OUTPUT_XML = "mangapark_follows_mal_enriched.xml"

# MAL API requires authentication
# Get your Client ID from: https://myanimelist.net/apiconfig
MAL_CLIENT_ID = "9f53e7f90704b145d964d9c747f3591a"  # Replace with your MAL API Client ID

# Jikan API (unofficial MAL API, no auth needed but has rate limits)
# Alternative if you don't want to use official MAL API
USE_JIKAN = True  # Set to False to use official MAL API
# --------------------------


def similar(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_mal_via_jikan(title):
    """
    Search for manga on MAL using Jikan API (no auth required)
    Returns: (mal_id, mal_title, similarity_score) or (None, None, 0)
    """
    try:
        url = "https://api.jikan.moe/v4/manga"
        params = {"q": title, "limit": 5}
        
        print(f"  [Jikan] Searching for: {title}")
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code == 429:
            print("  [WARN] Rate limit hit, waiting 60 seconds...")
            time.sleep(60)
            resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code != 200:
            print(f"  [WARN] API returned status {resp.status_code}")
            return None, None, 0
        
        data = resp.json()
        results = data.get("data", [])
        
        if not results:
            print(f"  [WARN] No results found")
            return None, None, 0
        
        # Find best match
        best_match = None
        best_score = 0
        
        for manga in results:
            mal_title = manga.get("title", "")
            mal_title_english = manga.get("title_english", "")
            mal_title_japanese = manga.get("title_japanese", "")
            mal_id = manga.get("mal_id")
            
            # Check similarity with all title variants
            scores = [
                similar(title, mal_title),
                similar(title, mal_title_english) if mal_title_english else 0,
                similar(title, mal_title_japanese) if mal_title_japanese else 0
            ]
            score = max(scores)
            
            if score > best_score:
                best_score = score
                best_match = (mal_id, mal_title, score)
        
        if best_match and best_score > 0.6:  # Threshold for accepting a match
            print(f"  [FOUND] MAL ID {best_match[0]}: {best_match[1]} (confidence: {best_score:.2%})")
            return best_match
        else:
            print(f"  [WARN] Best match too low: {best_score:.2%}")
            return None, None, 0
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None, None, 0


def search_mal_via_official_api(title):
    """
    Search for manga on MAL using official API (requires Client ID)
    Returns: (mal_id, mal_title, similarity_score) or (None, None, 0)
    """
    if not MAL_CLIENT_ID or MAL_CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("  [ERROR] MAL_CLIENT_ID not configured")
        return None, None, 0
    
    try:
        url = "https://api.myanimelist.net/v2/manga"
        params = {"q": title, "limit": 5}
        headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
        
        print(f"  [MAL API] Searching for: {title}")
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            print(f"  [WARN] API returned status {resp.status_code}")
            return None, None, 0
        
        data = resp.json()
        results = data.get("data", [])
        
        if not results:
            print(f"  [WARN] No results found")
            return None, None, 0
        
        # Find best match
        best_match = None
        best_score = 0
        
        for item in results:
            manga = item.get("node", {})
            mal_title = manga.get("title", "")
            mal_id = manga.get("id")
            
            score = similar(title, mal_title)
            
            if score > best_score:
                best_score = score
                best_match = (mal_id, mal_title, score)
        
        if best_match and best_score > 0.6:
            print(f"  [FOUND] MAL ID {best_match[0]}: {best_match[1]} (confidence: {best_score:.2%})")
            return best_match
        else:
            print(f"  [WARN] Best match too low: {best_score:.2%}")
            return None, None, 0
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None, None, 0


def enrich_mal_ids(input_file, output_file):
    """
    Read XML, search for MAL IDs, and create enriched XML
    """
    print(f"[INFO] Loading XML from {input_file}...")
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    manga_entries = root.findall("manga")
    total = len(manga_entries)
    
    print(f"[INFO] Found {total} manga entries to process")
    
    stats = {
        "found": 0,
        "not_found": 0,
        "low_confidence": 0
    }
    
    # Create report file
    with open("mal_id_report.txt", "w", encoding="utf-8") as report:
        report.write("MAL ID Enrichment Report\n")
        report.write("=" * 80 + "\n\n")
        
        for idx, manga in enumerate(manga_entries, 1):
            title_elem = manga.find("manga_title")
            mal_id_elem = manga.find("manga_mangadb_id")
            
            if title_elem is None or mal_id_elem is None:
                continue
            
            title = title_elem.text
            current_id = mal_id_elem.text
            
            print(f"\n[{idx}/{total}] Processing: {title}")
            report.write(f"[{idx}/{total}] {title}\n")
            
            # Skip if already has a valid ID
            if current_id and current_id != "0":
                print(f"  [SKIP] Already has MAL ID: {current_id}")
                report.write(f"  Already has ID: {current_id}\n\n")
                stats["found"] += 1
                continue
            
            # Search for MAL ID
            if USE_JIKAN:
                mal_id, mal_title, score = search_mal_via_jikan(title)
            else:
                mal_id, mal_title, score = search_mal_via_official_api(title)
            
            if mal_id:
                mal_id_elem.text = str(mal_id)
                stats["found"] += 1
                report.write(f"  ✓ Found: MAL ID {mal_id} - {mal_title} (confidence: {score:.2%})\n\n")
                
                if score < 0.8:
                    stats["low_confidence"] += 1
                    report.write(f"  ⚠ Low confidence match!\n\n")
            else:
                stats["not_found"] += 1
                report.write(f"  ✗ Not found on MAL\n\n")
            
            # Rate limiting (Jikan requires 1 request per second)
            if USE_JIKAN:
                time.sleep(1)
            else:
                time.sleep(0.1)  # Be nice to MAL API too
        
        # Write summary
        summary = f"""
Summary:
--------
Total manga: {total}
Found MAL IDs: {stats['found']}
Not found: {stats['not_found']}
Low confidence matches: {stats['low_confidence']}

Success rate: {stats['found']/total*100:.1f}%
"""
        print(summary)
        report.write(summary)
    
    # Save enriched XML
    print(f"\n[INFO] Saving enriched XML to {output_file}...")
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    
    print(f"[DONE] Enriched XML saved!")
    print(f"[INFO] Check 'mal_id_report.txt' for detailed results")


def main():
    print("=" * 80)
    print("MAL ID Enrichment Tool")
    print("=" * 80)
    print()
    
    if USE_JIKAN:
        print("[INFO] Using Jikan API (unofficial, no auth required)")
        print("[INFO] This will take time due to rate limits (1 request/second)")
    else:
        print("[INFO] Using Official MAL API")
        if MAL_CLIENT_ID == "YOUR_CLIENT_ID_HERE":
            print("[ERROR] Please set your MAL_CLIENT_ID in the config section")
            print("[INFO] Get one from: https://myanimelist.net/apiconfig")
            return
    
    print()
    input("Press Enter to start enrichment process...")
    print()
    
    try:
        enrich_mal_ids(INPUT_XML, OUTPUT_XML)
    except FileNotFoundError:
        print(f"[ERROR] Input file '{INPUT_XML}' not found!")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
