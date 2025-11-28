"""
Backend module for manga export functionality
Refactored from export_mangapark_follows_to_mal_xml.py
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional
from datetime import datetime

class MangaParkExporter:
    def __init__(self, cookies: Dict[str, str], progress_callback: Optional[Callable] = None):
        """
        Initialize MangaPark exporter
        
        Args:
            cookies: Dictionary containing skey, tfv, theme, wd cookies
            progress_callback: Function(percent, step, message) to report progress
        """
        self.cookies = cookies
        self.progress_callback = progress_callback or (lambda p, s, m: None)
        self.session = requests.Session()
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://mangapark.net/',
        })
        
        # Set cookies
        for name, value in cookies.items():
            if value:
                self.session.cookies.set(name, value, domain='.mangapark.net')
    
    def log(self, percent: int, step: int, message: str, log_type: str = "info"):
        """Send progress update"""
        log_entry = {
            "type": log_type,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        self.progress_callback(percent, step, log_entry)
    
    def scrape_follows(self) -> List[Dict]:
        """
        Scrape user's followed manga from MangaPark
        
        Returns:
            List of manga dictionaries with title, url, etc.
        """
        self.log(5, 0, "🔍 Connecting to MangaPark...", "info")
        
        manga_list = []
        page = 1
        
        try:
            while True:
                self.log(10 + (page * 5), 0, f"📄 Scraping page {page}...", "info")
                
                url = f"https://mangapark.net/auser/follows?page={page}"
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    self.log(15, 0, f"❌ Failed to fetch page {page}: Status {response.status_code}", "error")
                    break
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find manga entries (adjust selectors based on actual HTML structure)
                manga_items = soup.select('.item, .manga-item, [class*="manga"]')
                
                if not manga_items:
                    self.log(20, 0, f"✅ Scraped {len(manga_list)} manga from {page-1} pages", "success")
                    break
                
                for item in manga_items:
                    try:
                        title_elem = item.select_one('a[href*="/manga/"], .title a, h3 a')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')
                        
                        if not url.startswith('http'):
                            url = 'https://mangapark.net' + url
                        
                        manga_list.append({
                            'title': title,
                            'url': url,
                            'site': 'mangapark',
                            'mal_id': None,
                            'status': 'reading'
                        })
                        
                    except Exception as e:
                        self.log(20, 0, f"⚠️ Error parsing item: {str(e)}", "warning")
                        continue
                
                page += 1
                time.sleep(1)  # Rate limiting
                
                # Safety limit
                if page > 50:
                    self.log(25, 0, "⚠️ Reached page limit (50)", "warning")
                    break
        
        except Exception as e:
            self.log(25, 0, f"❌ Scraping error: {str(e)}", "error")
            raise
        
        return manga_list
    
    def enrich_with_mal_ids(self, manga_list: List[Dict]) -> List[Dict]:
        """
        Enrich manga list with MAL IDs using MAL API or Jikan (parallélisé, 1 req/s)
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        self.log(30, 1, "✨ Starting MAL enrichment...", "info")
        total = len(manga_list)
        jikan_base = "https://api.jikan.moe/v4"
        lock = threading.Lock()
        last_req_time = [0]
        results = [None] * total

        def worker(idx, manga):
            progress = 30 + int((idx / total) * 30)
            self.log(progress, 1, f"🔎 Searching MAL for: {manga['title']}", "info")
            try:
                with lock:
                    now = time.time()
                    wait = max(0, 1 - (now - last_req_time[0]))
                    if wait > 0:
                        time.sleep(wait)
                    last_req_time[0] = time.time()
                    search_url = f"{jikan_base}/manga?q={manga['title']}&limit=1"
                    response = requests.get(search_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        mal_id = data['data'][0].get('mal_id')
                        manga['mal_id'] = mal_id
                        self.log(progress, 1, f"✅ Found MAL ID {mal_id} for {manga['title']}", "success")
                    else:
                        self.log(progress, 1, f"⚠️ No MAL match for {manga['title']}", "warning")
                else:
                    self.log(progress, 1, f"⚠️ MAL API error: {response.status_code}", "warning")
            except Exception as e:
                self.log(progress, 1, f"❌ Error enriching {manga['title']}: {str(e)}", "error")
            results[idx] = manga

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, idx, manga) for idx, manga in enumerate(manga_list)]
            for done_idx, fut in enumerate(as_completed(futures), 1):
                pass  # Just wait for all to finish

        self.log(60, 1, f"✨ Enrichment complete! Found {sum(1 for m in results if m.get('mal_id'))} MAL matches", "success")
        return results
        return manga_list
    
    def generate_mal_xml(self, manga_list: List[Dict]) -> str:
        """
        Generate MAL-compatible XML export file
        
        Args:
            manga_list: List of manga dictionaries with mal_id
            
        Returns:
            XML string
        """
        self.log(65, 2, "📄 Generating MAL XML...", "info")
        
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<myanimelist>']
        
        for manga in manga_list:
            if not manga.get('mal_id'):
                continue
            
            xml_parts.append('  <manga>')
            xml_parts.append(f'    <manga_mangadb_id>{manga["mal_id"]}</manga_mangadb_id>')
            xml_parts.append(f'    <manga_title><![CDATA[{manga["title"]}]]></manga_title>')
            xml_parts.append('    <my_status>Reading</my_status>')
            xml_parts.append('    <my_score>0</my_score>')
            xml_parts.append('  </manga>')
        
        xml_parts.append('</myanimelist>')
        
        self.log(80, 2, f"✅ Generated XML with {len([m for m in manga_list if m.get('mal_id')])} entries", "success")
        return '\n'.join(xml_parts)
    
    def generate_html_report(self, manga_list: List[Dict]) -> str:
        """
        Generate HTML report with all manga (matched and unmatched)
        
        Args:
            manga_list: List of manga dictionaries
            
        Returns:
            HTML string
        """
        self.log(85, 2, "📄 Generating HTML report...", "info")
        
        matched = [m for m in manga_list if m.get('mal_id')]
        unmatched = [m for m in manga_list if not m.get('mal_id')]
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MangaPark Export Report</title>
    <style>
        body {{ font-family: system-ui; background: #0f172a; color: #e2e8f0; padding: 40px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #667eea; }}
        .stats {{ display: flex; gap: 20px; margin: 30px 0; }}
        .stat {{ background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #1e293b; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #334155; }}
        .matched {{ color: #10b981; }}
        .unmatched {{ color: #f59e0b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 MangaPark Export Report</h1>
        <div class="stats">
            <div class="stat">
                <div>Total Manga</div>
                <div class="stat-value">{len(manga_list)}</div>
            </div>
            <div class="stat">
                <div>Matched (MAL)</div>
                <div class="stat-value matched">{len(matched)}</div>
            </div>
            <div class="stat">
                <div>Unmatched</div>
                <div class="stat-value unmatched">{len(unmatched)}</div>
            </div>
        </div>
        
        <h2>✅ Matched Manga ({len(matched)})</h2>
        <table>
            <tr><th>Title</th><th>MAL ID</th><th>URL</th></tr>
"""
        
        for manga in matched:
            html += f"""            <tr>
                <td>{manga['title']}</td>
                <td class="matched">{manga['mal_id']}</td>
                <td><a href="{manga['url']}" target="_blank">View</a></td>
            </tr>
"""
        
        html += f"""        </table>
        
        <h2>⚠️ Unmatched Manga ({len(unmatched)})</h2>
        <table>
            <tr><th>Title</th><th>URL</th></tr>
"""
        
        for manga in unmatched:
            html += f"""            <tr>
                <td>{manga['title']}</td>
                <td><a href="{manga['url']}" target="_blank">View</a></td>
            </tr>
"""
        
        html += """        </table>
    </div>
</body>
</html>"""
        
        self.log(90, 2, "✅ HTML report generated", "success")
        return html
    
    def save_files(self, manga_list: List[Dict], xml_content: str, html_content: str) -> Dict[str, str]:
        """
        Save XML and HTML files to output directory
        
        Returns:
            Dictionary with file paths
        """
        self.log(92, 3, "💾 Saving files...", "info")
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save XML
        xml_file = output_dir / f"mangapark_export_{timestamp}.xml"
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        self.log(94, 3, f"✅ Saved XML: {xml_file.name}", "success")
        
        # Save HTML
        html_file = output_dir / f"mangapark_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        self.log(96, 3, f"✅ Saved HTML: {html_file.name}", "success")
        
        # Save JSON backup
        json_file = output_dir / f"mangapark_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(manga_list, f, indent=2, ensure_ascii=False)
        self.log(98, 3, f"✅ Saved JSON backup: {json_file.name}", "success")
        
        return {
            "xml": str(xml_file.absolute()),
            "html": str(html_file.absolute()),
            "json": str(json_file.absolute())
        }
    
    def export_full(self) -> Dict:
        """
        Run complete export process
        
        Returns:
            Dictionary with results and file paths
        """
        try:
            self.log(0, 0, "🚀 Starting export process...", "info")
            
            # Step 1: Scrape follows
            manga_list = self.scrape_follows()
            self.log(25, 0, f"✅ Step 1 complete: Found {len(manga_list)} manga", "success")
            
            # Step 2: Enrich with MAL IDs
            manga_list = self.enrich_with_mal_ids(manga_list)
            self.log(60, 1, f"✅ Step 2 complete: Matched {sum(1 for m in manga_list if m['mal_id'])} manga", "success")
            
            # Step 3: Generate files
            xml_content = self.generate_mal_xml(manga_list)
            html_content = self.generate_html_report(manga_list)
            self.log(90, 2, "✅ Step 3 complete: Files generated", "success")
            
            # Step 4: Save files
            file_paths = self.save_files(manga_list, xml_content, html_content)
            self.log(100, 3, "🎉 Export completed successfully!", "success")
            
            return {
                "status": "success",
                "total_manga": len(manga_list),
                "matched": sum(1 for m in manga_list if m['mal_id']),
                "files": file_paths
            }
            
        except Exception as e:
            self.log(0, 0, f"💥 Export failed: {str(e)}", "error")
            return {
                "status": "error",
                "error": str(e)
            }


class MangaDexExporter:
    def __init__(self, cookies: dict, progress_callback=None):
        self.cookies = cookies
        self.progress_callback = progress_callback
        self.current_progress = {"percent": 0, "step": 0, "logs": [], "status": "idle"}

    def log(self, percent, step, message, type_="info"):
        if self.progress_callback:
            self.progress_callback(percent, step, {"message": message, "type": type_})

    def scrape_follows(self):
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from bs4 import BeautifulSoup
        import time
        self.log(0, 0, "🔍 Scraping MangaDex follows...", "info")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get("https://mangadex.org/follows")
            for name, value in self.cookies.items():
                if value:
                    driver.add_cookie({"name": name, "value": value, "domain": ".mangadex.org"})
            driver.refresh()
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            manga_cards = soup.select("a.manga_title")
            results = []
            for card in manga_cards:
                title = card.get_text(strip=True)
                url = card.get("href")
                if url and not url.startswith("http"):
                    url = "https://mangadex.org" + url
                results.append({"title": title, "url": url})
            self.log(25, 0, f"✅ Found {len(results)} MangaDex follows", "success")
            return results
        except Exception as e:
            self.log(0, 0, f"❌ Error scraping MangaDex: {str(e)}", "error")
            return []
        finally:
            driver.quit()

    def enrich_with_mal_ids(self, manga_list):
        # Réutilise la logique optimisée de MangaPark
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading, time, requests
        lock = threading.Lock()
        last_req_time = [0]
        total = len(manga_list)
        results = [None] * total
        def worker(idx, manga):
            progress = 30 + int((idx / total) * 30)
            self.log(progress, 1, f"🔎 Searching MAL for: {manga['title']}", "info")
            try:
                with lock:
                    now = time.time()
                    wait = max(0, 1 - (now - last_req_time[0]))
                    if wait > 0:
                        time.sleep(wait)
                    last_req_time[0] = time.time()
                    search_url = f"https://api.jikan.moe/v4/manga?q={manga['title']}&limit=1"
                    response = requests.get(search_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        mal_id = data['data'][0].get('mal_id')
                        manga['mal_id'] = mal_id
                        self.log(progress, 1, f"✅ Found MAL ID {mal_id} for {manga['title']}", "success")
                    else:
                        self.log(progress, 1, f"⚠️ No MAL match for {manga['title']}", "warning")
                else:
                    self.log(progress, 1, f"⚠️ MAL API error: {response.status_code}", "warning")
            except Exception as e:
                self.log(progress, 1, f"❌ Error enriching {manga['title']}: {str(e)}", "error")
            results[idx] = manga
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, idx, manga) for idx, manga in enumerate(manga_list)]
            for fut in as_completed(futures):
                pass
        self.log(60, 1, f"✨ Enrichment complete! Found {sum(1 for m in results if m.get('mal_id'))} MAL matches", "success")
        return results

    def generate_mal_xml(self, manga_list):
        """
        Generate MAL-compatible XML export file
        
        Args:
            manga_list: List of manga dictionaries with mal_id
            
        Returns:
            XML string
        """
        self.log(65, 2, "📄 Generating MAL XML...", "info")
        
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<myanimelist>']
        
        for manga in manga_list:
            if not manga.get('mal_id'):
                continue
            
            xml_parts.append('  <manga>')
            xml_parts.append(f'    <manga_mangadb_id>{manga["mal_id"]}</manga_mangadb_id>')
            xml_parts.append(f'    <manga_title><![CDATA[{manga["title"]}]]></manga_title>')
            xml_parts.append('    <my_status>Reading</my_status>')
            xml_parts.append('    <my_score>0</my_score>')
            xml_parts.append('  </manga>')
        
        xml_parts.append('</myanimelist>')
        
        self.log(80, 2, f"✅ Generated XML with {len([m for m in manga_list if m.get('mal_id')])} entries", "success")
        return '\n'.join(xml_parts)
    
    def generate_html_report(self, manga_list):
        """
        Generate HTML report with all manga (matched and unmatched)
        
        Args:
            manga_list: List of manga dictionaries
            
        Returns:
            HTML string
        """
        self.log(85, 2, "📄 Generating HTML report...", "info")
        
        matched = [m for m in manga_list if m.get('mal_id')]
        unmatched = [m for m in manga_list if not m.get('mal_id')]
        
        html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>MangaDex Export Report</title>
    <style>
        body {{ font-family: system-ui; background: #0f172a; color: #e2e8f0; padding: 40px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #667eea; }}
        .stats {{ display: flex; gap: 20px; margin: 30px 0; }}
        .stat {{ background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #1e293b; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #334155; }}
        .matched {{ color: #10b981; }}
        .unmatched {{ color: #f59e0b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 MangaDex Export Report</h1>
        <div class="stats">
            <div class="stat">
                <div>Total Manga</div>
                <div class="stat-value">{len(manga_list)}</div>
            </div>
            <div class="stat">
                <div>Matched (MAL)</div>
                <div class="stat-value matched">{len(matched)}</div>
            </div>
            <div class="stat">
                <div>Unmatched</div>
                <div class="stat-value unmatched">{len(unmatched)}</div>
            </div>
        </div>
        <h2>✅ Matched Manga ({len(matched)})</h2>
        <table>
            <tr><th>Title</th><th>MAL ID</th><th>URL</th></tr>
"""
        for manga in matched:
            html += f"            <tr>\n                <td>{manga['title']}</td>\n                <td class=\"matched\">{manga['mal_id']}</td>\n                <td><a href=\"{manga['url']}\" target=\"_blank\">View</a></td>\n            </tr>\n"
        html += f"        </table>\n        <h2>⚠️ Unmatched Manga ({len(unmatched)})</h2>\n        <table>\n            <tr><th>Title</th><th>URL</th></tr>\n"
        for manga in unmatched:
            html += f"            <tr>\n                <td>{manga['title']}</td>\n                <td><a href=\"{manga['url']}\" target=\"_blank\">View</a></td>\n            </tr>\n"
        html += "        </table>\n    </div>\n</body>\n</html>"
        return html

    def save_files(self, manga_list, xml_content, html_content):
        from pathlib import Path
        import json
        from datetime import datetime
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        xml_file = output_dir / f"mangadex_export_{timestamp}.xml"
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        html_file = output_dir / f"mangadex_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        json_file = output_dir / f"mangadex_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(manga_list, f, indent=2, ensure_ascii=False)
        return {
            "xml": str(xml_file.absolute()),
            "html": str(html_file.absolute()),
            "json": str(json_file.absolute())
        }
    
    def export_full(self):
        try:
            self.log(0, 0, "🚀 Starting MangaDex export process...", "info")
            manga_list = self.scrape_follows()
            self.log(25, 0, f"✅ Step 1 complete: Found {len(manga_list)} manga", "success")
            manga_list = self.enrich_with_mal_ids(manga_list)
            self.log(60, 1, f"✅ Step 2 complete: Matched {sum(1 for m in manga_list if m.get('mal_id'))} manga", "success")
            xml_content = self.generate_mal_xml(manga_list)
            html_content = self.generate_html_report(manga_list)
            self.log(90, 2, "✅ Step 3 complete: Files generated", "success")
            file_paths = self.save_files(manga_list, xml_content, html_content)
            self.log(100, 3, "🎉 MangaDex export completed successfully!", "success")
            return {
                "status": "success",
                "total_manga": len(manga_list),
                "matched": sum(1 for m in manga_list if m.get('mal_id')),
                "files": file_paths
            }
        except Exception as e:
            self.log(0, 0, f"💥 MangaDex export failed: {str(e)}", "error")
            return {"status": "error", "error": str(e)}


def export_mangapark(cookies: Dict[str, str], progress_callback: Optional[Callable] = None) -> Dict:
    """
    Main export function
    
    Args:
        cookies: Dictionary with skey, tfv, theme, wd
        progress_callback: Function(percent, step, message) for progress updates
        
    Returns:
        Export result dictionary
    """
    exporter = MangaParkExporter(cookies, progress_callback)
    return exporter.export_full()
