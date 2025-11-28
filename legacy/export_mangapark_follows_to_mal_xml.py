import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
import time

# For headless browsing (optional, will try if available)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[INFO] Selenium not available. Install with: pip install selenium")
    print("[INFO] Will try requests-based scraping instead.")

# --------- CONFIG ---------
BASE_URL = "https://mangapark.io"  # or .org if you use that
COOKIE_HEADER = r"""
Your Cookies Here
""".strip()

# Optional: put your MAL username here (only used in <myinfo>, not for login)
MAL_USERNAME = "mangapark_export"
OUTPUT_XML = "mangapark_follows_mal.xml"
# --------------------------


def create_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0 Safari/537.36"
        ),
        "Cookie": COOKIE_HEADER,
    })
    return s


def scrape_follows_selenium(cookies_str):
    """
    Use Selenium to scrape follows (handles JavaScript rendering)
    """
    print("[INFO] Using Selenium to scrape follows...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Go to MangaPark
        driver.get(f"{BASE_URL}/my/follows")
        
        # Add cookies
        for cookie in cookies_str.split("; "):
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                driver.add_cookie({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".mangapark.io"
                })
        
        # Reload with cookies
        driver.refresh()
        
        results = []
        seen = set()
        page = 1
        
        while True:
            print(f"[INFO] Scraping page {page}...")
            
            url = f"{BASE_URL}/my/follows?page={page}"
            driver.get(url)
            
            # Wait for content to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                # Additional wait for dynamic content
                time.sleep(2)
            except:
                print(f"[WARN] Timeout waiting for page {page}")
                break
            
            # Parse the rendered HTML
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Save first page for debugging
            if page == 1:
                with open("debug_selenium_page1.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("[DEBUG] Saved Selenium HTML to debug_selenium_page1.html")
            
            # Look for links to manga titles
            links = soup.select("a[href*='/title/']")
            print(f"[DEBUG] Found {len(links)} potential manga links")
            
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
            
            print(f"[INFO] Found {count_this_page} unique titles on page {page}.")
            
            if count_this_page == 0:
                break
            
            page += 1
            
            # Safety limit
            if page > 100:
                print("[WARN] Reached page limit of 100")
                break
        
        return results
    
    finally:
        driver.quit()


def scrape_follows(session):
    """
    Scrape all followed titles from /my/follows
    First tries Selenium if available, falls back to requests
    Returns a list of dicts: { 'title': ..., 'url': ... }
    """
    # Try Selenium first if available
    if SELENIUM_AVAILABLE:
        try:
            return scrape_follows_selenium(COOKIE_HEADER)
        except Exception as e:
            print(f"[WARN] Selenium failed: {e}")
            print("[INFO] Falling back to requests-based scraping...")
    
    # Fallback to requests (won't work well for dynamic content)
    results = []
    seen = set()

    page = 1
    while True:
        html_url = f"{BASE_URL}/my/follows?page={page}"
        print(f"[INFO] Fetching {html_url}...")
        resp = session.get(html_url)
        
        if resp.status_code != 200:
            print(f"[WARN] Got status {resp.status_code}, stopping.")
            break
        
        # Save HTML for debugging
        if page == 1:
            with open("debug_page1.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print("[DEBUG] Saved HTML to debug_page1.html")
        
        # Try to parse HTML
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("a[href*='/title/']")
        print(f"[DEBUG] Found {len(links)} links with '/title/' in HTML")
        
        count_this_page = 0
        for a in links:
            href = a.get("href") or ""
            title = a.get_text(strip=True)
            if not title or "/title/" not in href:
                continue
            
            full_url = href if href.startswith("http") else BASE_URL + href
            key = (title, full_url)
            if key not in seen:
                seen.add(key)
                results.append({"title": title, "url": full_url})
                count_this_page += 1
        
        if count_this_page == 0:
            break
        
        print(f"[INFO] Found {count_this_page} unique titles on page {page}.")
        page += 1

    print(f"[DONE] Total unique follows found: {len(results)}")
    return results


def build_mal_xml(manga_list, username):
    """
    Build a MyAnimeList-style XML <myanimelist> tree containing manga entries.
    All entries are set to 'Plan to Read' with 0 chapters read.
    """
    root = ET.Element("myanimelist")

    # ---- myinfo section (MAL expects one) ----
    myinfo = ET.SubElement(root, "myinfo")
    ET.SubElement(myinfo, "user_id").text = "0"
    ET.SubElement(myinfo, "user_name").text = username
    # 1 = anime, 2 = manga (commonly used in tools that parse MAL XML) :contentReference[oaicite:0]{index=0}
    ET.SubElement(myinfo, "user_export_type").text = "2"

    total = len(manga_list)
    ET.SubElement(myinfo, "user_total_anime").text = "0"
    ET.SubElement(myinfo, "user_total_manga").text = str(total)
    ET.SubElement(myinfo, "user_total_watching").text = "0"
    ET.SubElement(myinfo, "user_total_reading").text = "0"
    ET.SubElement(myinfo, "user_total_completed").text = "0"
    ET.SubElement(myinfo, "user_total_onhold").text = "0"
    ET.SubElement(myinfo, "user_total_dropped").text = "0"
    ET.SubElement(myinfo, "user_total_plantowatch").text = "0"
    ET.SubElement(myinfo, "user_total_plantoread").text = str(total)

    # ---- each <manga> entry ----
    for m in manga_list:
        entry = ET.SubElement(root, "manga")

        # MAL ID is unknown from MangaPark, so we set it to 0.
        # Some tools and imports still work with ID=0 and matching by title. :contentReference[oaicite:1]{index=1}
        ET.SubElement(entry, "manga_mangadb_id").text = "0"

        # Basic info
        ET.SubElement(entry, "manga_title").text = m["title"]
        ET.SubElement(entry, "manga_volumes").text = "0"
        ET.SubElement(entry, "manga_chapters").text = "0"

        # User-specific info
        ET.SubElement(entry, "my_id").text = "0"
        ET.SubElement(entry, "my_read_volumes").text = "0"
        ET.SubElement(entry, "my_read_chapters").text = "0"
        ET.SubElement(entry, "my_status").text = "Plan to Read"
        ET.SubElement(entry, "my_score").text = "0"
        ET.SubElement(entry, "my_times_read").text = "0"
        ET.SubElement(entry, "my_reread_value").text = "0"
        ET.SubElement(entry, "my_tags").text = ""

        # Non-standard, but used by some community tools – we store MangaPark URL here.
        ET.SubElement(entry, "manga_mangapark_url").text = m["url"]

    return root


def save_xml(root, path):
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print(f"[DONE] XML saved to {path}")


def main():
    session = create_session()
    follows = scrape_follows(session)

    if not follows:
        print("[WARN] No follows found. Check that your COOKIE_HEADER is correct "
              "and that you are logged in when copying it.")
        return

    xml_root = build_mal_xml(follows, MAL_USERNAME)
    save_xml(xml_root, OUTPUT_XML)


if __name__ == "__main__":
    main()
