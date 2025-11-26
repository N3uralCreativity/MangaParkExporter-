"""
Complete MangaPark to MAL Exporter
===================================
1. Scrapes your MangaPark follows using Selenium
2. Enriches manga with MAL IDs via Jikan API
3. Generates XML for MAL import
4. Creates HTML viewing page
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
import time
from difflib import SequenceMatcher
import os

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[ERROR] Selenium is required! Install with: pip install selenium")
    exit(1)

# ==================== CONFIGURATION ====================

BASE_URL = "https://mangapark.io"

# IMPORTANT: Get your cookies from browser after logging in
# 1. Open MangaPark in your browser and log in
# 2. Press F12 -> Application/Storage -> Cookies
# 3. Copy the values below
COOKIES = {
    "skey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI2OTIyMzdjZWIyYTQxMmI5OWM1MGM0YjUiLCJpYXQiOjE3NjQxODQ2NjAsImV4cCI6MTc2Njc3NjY2MH0.xL7vmnOtq_dTmXouOQl22PDF6igqPDWCsNzQKDKGBio",
    "tfv": "1763850143381",
    "theme": "coffee",
    "wd": "876x932"
}

MAL_USERNAME = "mangapark_export"
OUTPUT_DIR = "output"

# =======================================================


def similar(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def print_step(step_num, total_steps, message):
    """Print a formatted step message"""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}/{total_steps}: {message}")
    print('='*80)


def scrape_mangapark_follows():
    """Step 1: Scrape follows from MangaPark using Selenium"""
    print_step(1, 4, "Scraping MangaPark Follows")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(f"{BASE_URL}/my/follows")
        
        # Add cookies
        for name, value in COOKIES.items():
            driver.add_cookie({
                "name": name,
                "value": value,
                "domain": ".mangapark.io"
            })
        
        driver.refresh()
        time.sleep(2)
        
        results = []
        seen = set()
        page = 1
        
        while True:
            print(f"  [INFO] Scraping page {page}...")
            
            url = f"{BASE_URL}/my/follows?page={page}"
            driver.get(url)
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(2)
            except:
                print(f"  [WARN] Timeout on page {page}")
                break
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            links = soup.select("a[href*='/title/']")
            
            count_this_page = 0
            for a in links:
                href = a.get("href", "")
                title = a.get_text(strip=True)
                
                if not title or "/title/" not in href:
                    continue
                
                full_url = href if href.startswith("http") else BASE_URL + href
                key = (title, full_url)
                
                if key not in seen:
                    seen.add(key)
                    results.append({"title": title, "url": full_url})
                    count_this_page += 1
            
            print(f"  [INFO] Found {count_this_page} unique titles on page {page}")
            
            if count_this_page == 0:
                break
            
            page += 1
            
            if page > 100:
                print("  [WARN] Reached page limit")
                break
        
        print(f"\n  ✓ Total manga found: {len(results)}")
        return results
    
    finally:
        driver.quit()


def search_mal_id(title):
    """Search for manga on MAL using Jikan API"""
    try:
        url = "https://api.jikan.moe/v4/manga"
        params = {"q": title, "limit": 5}
        
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code == 429:
            print("    [WARN] Rate limit, waiting 60s...")
            time.sleep(60)
            resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code != 200:
            return None, None, 0
        
        data = resp.json()
        results = data.get("data", [])
        
        if not results:
            return None, None, 0
        
        best_match = None
        best_score = 0
        
        for manga in results:
            mal_title = manga.get("title", "")
            mal_title_english = manga.get("title_english", "")
            mal_id = manga.get("mal_id")
            
            scores = [
                similar(title, mal_title),
                similar(title, mal_title_english) if mal_title_english else 0,
            ]
            score = max(scores)
            
            if score > best_score:
                best_score = score
                best_match = (mal_id, mal_title, score)
        
        if best_match and best_score > 0.6:
            return best_match
        else:
            return None, None, 0
            
    except Exception as e:
        return None, None, 0


def enrich_with_mal_ids(manga_list):
    """Step 2: Enrich manga with MAL IDs"""
    print_step(2, 4, "Finding MAL IDs")
    
    total = len(manga_list)
    found_count = 0
    low_confidence = 0
    
    print(f"  [INFO] Processing {total} manga (this will take ~{total} seconds)")
    print("  [INFO] Rate limit: 1 request/second\n")
    
    enriched_list = []
    
    for idx, manga in enumerate(manga_list, 1):
        title = manga["title"]
        
        # Skip obvious chapter titles
        if title.lower().startswith(("chapter", "ch.", "vol.")):
            print(f"  [{idx}/{total}] ⏭️  Skipping '{title}' (chapter title)")
            enriched_list.append({
                **manga,
                "mal_id": "0",
                "mal_title": None,
                "confidence": 0
            })
            continue
        
        print(f"  [{idx}/{total}] 🔍 {title[:60]}{'...' if len(title) > 60 else ''}")
        
        mal_id, mal_title, score = search_mal_id(title)
        
        if mal_id:
            found_count += 1
            if score < 0.8:
                low_confidence += 1
                print(f"            ⚠️  MAL ID {mal_id} (confidence: {score:.1%})")
            else:
                print(f"            ✓ MAL ID {mal_id} (confidence: {score:.1%})")
            
            enriched_list.append({
                **manga,
                "mal_id": str(mal_id),
                "mal_title": mal_title,
                "confidence": score
            })
        else:
            print(f"            ✗ Not found")
            enriched_list.append({
                **manga,
                "mal_id": "0",
                "mal_title": None,
                "confidence": 0
            })
        
        time.sleep(1)  # Rate limiting
    
    print(f"\n  ✓ Found: {found_count}/{total} ({found_count/total*100:.1f}%)")
    if low_confidence > 0:
        print(f"  ⚠️  Low confidence matches: {low_confidence}")
    
    return enriched_list


def generate_mal_xml(manga_list, output_path):
    """Step 3: Generate MAL XML file"""
    print_step(3, 4, "Generating MAL XML")
    
    root = ET.Element("myanimelist")
    
    # MyInfo section
    myinfo = ET.SubElement(root, "myinfo")
    ET.SubElement(myinfo, "user_id").text = "0"
    ET.SubElement(myinfo, "user_name").text = MAL_USERNAME
    ET.SubElement(myinfo, "user_export_type").text = "2"
    
    total = len(manga_list)
    found = sum(1 for m in manga_list if m["mal_id"] != "0")
    
    ET.SubElement(myinfo, "user_total_manga").text = str(total)
    ET.SubElement(myinfo, "user_total_plantoread").text = str(found)
    
    # Manga entries
    for m in manga_list:
        entry = ET.SubElement(root, "manga")
        
        ET.SubElement(entry, "manga_mangadb_id").text = m["mal_id"]
        ET.SubElement(entry, "manga_title").text = m["title"]
        ET.SubElement(entry, "manga_volumes").text = "0"
        ET.SubElement(entry, "manga_chapters").text = "0"
        
        ET.SubElement(entry, "my_id").text = "0"
        ET.SubElement(entry, "my_read_volumes").text = "0"
        ET.SubElement(entry, "my_read_chapters").text = "0"
        ET.SubElement(entry, "my_status").text = "Plan to Read"
        ET.SubElement(entry, "my_score").text = "0"
        ET.SubElement(entry, "my_tags").text = ""
        
        ET.SubElement(entry, "manga_mangapark_url").text = m["url"]
        if m.get("mal_title"):
            ET.SubElement(entry, "manga_mal_title").text = m["mal_title"]
        if m.get("confidence"):
            ET.SubElement(entry, "manga_confidence").text = f"{m['confidence']:.2f}"
    
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    
    print(f"  ✓ XML saved to: {output_path}")
    print(f"  ✓ Entries with MAL ID: {found}/{total}")


def generate_html_page(manga_list, output_path):
    """Step 4: Generate HTML viewing page"""
    print_step(4, 4, "Generating HTML Page")
    
    # Sort: MAL IDs first, then alphabetically
    manga_list.sort(key=lambda x: (x["mal_id"] == "0", x["title"].lower()))
    
    found_count = sum(1 for m in manga_list if m["mal_id"] != "0")
    not_found_count = len(manga_list) - found_count
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MangaPark to MAL Export</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        
        .stat {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px 30px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }}
        
        .stat-value {{ font-size: 2rem; font-weight: bold; }}
        .stat-label {{ font-size: 0.9rem; opacity: 0.9; margin-top: 5px; }}
        
        .controls {{
            padding: 20px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .search-box {{ flex: 1; min-width: 250px; }}
        
        .search-box input {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .filter-buttons {{ display: flex; gap: 10px; flex-wrap: wrap; }}
        
        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e9ecef;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s;
        }}
        
        .filter-btn:hover {{
            border-color: #667eea;
            color: #667eea;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .manga-list {{ padding: 40px; max-height: 800px; overflow-y: auto; }}
        
        .manga-item {{
            display: flex;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            transition: background 0.3s;
        }}
        
        .manga-item:hover {{ background: #f8f9fa; }}
        
        .manga-status {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 20px;
            flex-shrink: 0;
        }}
        
        .status-found {{
            background: #10b981;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }}
        
        .status-not-found {{
            background: #ef4444;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
        }}
        
        .manga-content {{ flex: 1; min-width: 0; }}
        
        .manga-title {{
            font-size: 1.1rem;
            font-weight: 500;
            color: #1f2937;
            margin-bottom: 5px;
        }}
        
        .manga-info {{ font-size: 0.85rem; color: #6b7280; }}
        
        .manga-links {{
            display: flex;
            gap: 10px;
            margin-left: 20px;
            flex-shrink: 0;
        }}
        
        .manga-link {{
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.3s;
        }}
        
        .mal-link {{
            background: #2e51a2;
            color: white;
        }}
        
        .mal-link:hover {{
            background: #1e3a8a;
            transform: translateY(-2px);
        }}
        
        .mangapark-link {{
            background: #667eea;
            color: white;
        }}
        
        .mangapark-link:hover {{
            background: #5568d3;
            transform: translateY(-2px);
        }}
        
        .mal-link.disabled {{
            background: #d1d5db;
            color: #9ca3af;
            cursor: not-allowed;
            pointer-events: none;
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
        }}
        
        .confidence-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            margin-left: 8px;
        }}
        
        .confidence-high {{ background: #d1fae5; color: #065f46; }}
        .confidence-medium {{ background: #fef3c7; color: #92400e; }}
        .confidence-low {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 MangaPark to MAL Export</h1>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(manga_list)}</div>
                    <div class="stat-label">Total Manga</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{found_count}</div>
                    <div class="stat-label">Found on MAL</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{not_found_count}</div>
                    <div class="stat-label">Not Found</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{found_count/len(manga_list)*100:.1f}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>
        </header>
        
        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Search manga...">
            </div>
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="found">✓ Found</button>
                <button class="filter-btn" data-filter="not-found">✗ Not Found</button>
            </div>
        </div>
        
        <div class="manga-list" id="mangaList">
"""
    
    for manga in manga_list:
        has_mal_id = manga["mal_id"] != "0"
        status_class = "status-found" if has_mal_id else "status-not-found"
        
        if has_mal_id:
            confidence = manga.get("confidence", 0)
            if confidence >= 0.9:
                conf_badge = '<span class="confidence-badge confidence-high">High</span>'
            elif confidence >= 0.7:
                conf_badge = '<span class="confidence-badge confidence-medium">Medium</span>'
            else:
                conf_badge = '<span class="confidence-badge confidence-low">Low</span>'
            
            status_text = f"MAL ID: {manga['mal_id']}{conf_badge}"
            mal_url = f"https://myanimelist.net/manga/{manga['mal_id']}"
            mal_disabled = ""
        else:
            status_text = "Not found on MAL"
            mal_url = "#"
            mal_disabled = "disabled"
        
        html += f"""
            <div class="manga-item" data-status="{'found' if has_mal_id else 'not-found'}">
                <div class="manga-status {status_class}"></div>
                <div class="manga-content">
                    <div class="manga-title">{manga['title']}</div>
                    <div class="manga-info">{status_text}</div>
                </div>
                <div class="manga-links">
                    <a href="{mal_url}" class="manga-link mal-link {mal_disabled}" target="_blank">MAL</a>
                    <a href="{manga['url']}" class="manga-link mangapark-link" target="_blank">MangaPark</a>
                </div>
            </div>
"""
    
    html += """
        </div>
        
        <div class="no-results" id="noResults" style="display: none;">
            <h2>🔍 No manga found</h2>
            <p>Try adjusting your search or filters</p>
        </div>
    </div>
    
    <script>
        const searchInput = document.getElementById('searchInput');
        const filterButtons = document.querySelectorAll('.filter-btn');
        const mangaItems = document.querySelectorAll('.manga-item');
        const noResults = document.getElementById('noResults');
        const mangaList = document.getElementById('mangaList');
        
        let currentFilter = 'all';
        
        function filterManga() {
            const searchTerm = searchInput.value.toLowerCase();
            let visibleCount = 0;
            
            mangaItems.forEach(item => {
                const title = item.querySelector('.manga-title').textContent.toLowerCase();
                const status = item.dataset.status;
                
                const matchesSearch = title.includes(searchTerm);
                const matchesFilter = currentFilter === 'all' || status === currentFilter;
                
                if (matchesSearch && matchesFilter) {
                    item.style.display = 'flex';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            if (visibleCount === 0) {
                mangaList.style.display = 'none';
                noResults.style.display = 'block';
            } else {
                mangaList.style.display = 'block';
                noResults.style.display = 'none';
            }
        }
        
        searchInput.addEventListener('input', filterManga);
        
        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                currentFilter = button.dataset.filter;
                filterManga();
            });
        });
    </script>
</body>
</html>
"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"  ✓ HTML page saved to: {output_path}")


def main():
    print("\n" + "="*80)
    print(" "*20 + "MANGAPARK TO MAL COMPLETE EXPORTER")
    print("="*80)
    print()
    print("This tool will:")
    print("  1. Scrape your MangaPark follows")
    print("  2. Find MAL IDs for each manga")
    print("  3. Generate MAL-compatible XML")
    print("  4. Create a browsable HTML page")
    print()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        # Step 1: Scrape
        manga_list = scrape_mangapark_follows()
        
        if not manga_list:
            print("\n[ERROR] No manga found. Check your cookies!")
            return
        
        # Step 2: Enrich
        enriched_list = enrich_with_mal_ids(manga_list)
        
        # Step 3: Generate XML
        xml_path = os.path.join(OUTPUT_DIR, "mangapark_to_mal.xml")
        generate_mal_xml(enriched_list, xml_path)
        
        # Step 4: Generate HTML
        html_path = os.path.join(OUTPUT_DIR, "manga_list.html")
        generate_html_page(enriched_list, html_path)
        
        # Summary
        print("\n" + "="*80)
        print(" "*30 + "✓ COMPLETE!")
        print("="*80)
        print(f"\nFiles generated in '{OUTPUT_DIR}/' folder:")
        print(f"  • {xml_path} - Import this to MAL")
        print(f"  • {html_path} - Open in browser to view")
        print()
        
        # Try to open HTML
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(html_path)}")
            print("  ✓ HTML page opened in your browser")
        except:
            print(f"  → Open this file in your browser: {html_path}")
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
