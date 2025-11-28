"""
True desktop application using PyQt6
No browser needed - native Windows app with embedded web view
"""

import sys
import json
import threading
import time
import os
import webbrowser
import requests
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class BackendAPI(QObject):
    """Backend API exposed to JavaScript"""
    
    progressUpdate = pyqtSignal(int, int, dict)  # percent, step, log
    
    def __init__(self):
        super().__init__()
        self.current_progress = {"percent": 0, "step": 0, "logs": [], "status": "idle"}
    
    @pyqtSlot(str, result=str)
    def start_export(self, config_json):
        """Start export with given configuration"""
        try:
            config = json.loads(config_json)
            site = config.get('site', 'mangapark')
            mode = config.get('mode', 'authenticated')
            cookies = config.get('cookies', {})
            # Check cookies for MangaPark
            if site == 'mangapark' and mode == 'authenticated' and (not cookies.get('skey') or not cookies.get('tfv')):
                return json.dumps({"status": "error", "message": "Missing cookies"})
            # Check cookies for MangaDex
            if site == 'mangadex' and mode == 'authenticated':
                required = ['sidCookie', 'ssidCookie', 'sidccCookie']
                missing = [k for k in required if not cookies.get(k)]
                if missing:
                    return json.dumps({"status": "error", "message": f"Missing MangaDex cookies: {', '.join(missing)}"})
            if not SELENIUM_AVAILABLE:
                return json.dumps({"status": "error", "message": "Selenium not installed. Please run: pip install selenium"})
            self.current_progress = {"percent": 0, "step": 0, "logs": [], "status": "running"}
            def run_export():
                def emit_log(message, log_type="info"):
                    log_entry = {"type": log_type, "message": message, "time": ""}
                    self.current_progress["logs"].append(log_entry)
                    self.progressUpdate.emit(self.current_progress["percent"], self.current_progress["step"], log_entry)
                try:
                    emit_log(f"Starting export for {site} in {mode} mode...")
                    self.current_progress["step"] = 1
                    if site == 'mangapark':
                        manga_list = self.scrape_mangapark(cookies if mode == 'authenticated' else None, emit_log)
                        emit_log(f"Found {len(manga_list)} manga", "success")
                        self.current_progress["percent"] = 30
                        self.current_progress["step"] = 2
                        emit_log("Enriching with MAL IDs...")
                        enriched_list = self.enrich_with_mal_ids(manga_list, emit_log)
                        self.current_progress["percent"] = 60
                        self.current_progress["step"] = 3
                        emit_log("Generating MAL XML...")
                        os.makedirs("output", exist_ok=True)
                        xml_path = os.path.join("output", "mangapark_to_mal.xml")
                        self.generate_mal_xml(enriched_list, xml_path, emit_log)
                        self.current_progress["percent"] = 80
                        self.current_progress["step"] = 4
                        emit_log("Generating HTML report...")
                        html_path = os.path.join("output", "manga_list.html")
                        self.generate_html(enriched_list, html_path, emit_log)
                        self.current_progress["percent"] = 100
                        self.current_progress["status"] = "success"
                        self.current_progress["output_files"] = {"xml": xml_path, "html": html_path}
                        emit_log("Export completed successfully!", "success")
                    elif site == 'mangadex':
                        from backend_export import MangaDexExporter
                        exporter = MangaDexExporter(cookies, emit_log)
                        result = exporter.export_full()
                        self.current_progress["percent"] = 100
                        self.current_progress["status"] = result.get("status", "success")
                        self.current_progress["output_files"] = result.get("files", {})
                        emit_log("Export completed for MangaDex!", "success")
                except Exception as e:
                    self.current_progress["status"] = "error"
                    emit_log(f"Export failed: {str(e)}", "error")
                    import traceback
                    traceback.print_exc()
            thread = threading.Thread(target=run_export, daemon=True)
            thread.start()
            return json.dumps({"status": "started"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def scrape_mangapark(self, cookies, emit_log):
        """Scrape MangaPark follows or public list"""
        emit_log("Initializing Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            results = []
            seen = set()
            
            if cookies:
                # Authenticated mode - scrape /my/follows
                emit_log("Authenticated mode: Scraping your follows list...")
                driver.get("https://mangapark.io/my/follows")
                
                for name, value in cookies.items():
                    if value:
                        driver.add_cookie({
                            "name": name,
                            "value": value,
                            "domain": ".mangapark.io"
                        })
                
                driver.refresh()
                time.sleep(3)
                
                page = 1
                while True:
                    emit_log(f"Scraping page {page}...")
                    self.current_progress["percent"] = min(90, page * 10)
                    
                    url = f"https://mangapark.io/my/follows?page={page}"
                    driver.get(url)
                    time.sleep(5)  # Wait for page to load
                    
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    links = soup.select("a[href*='/title/']")
                    
                    count = 0
                    for a in links:
                        href = a.get("href", "")
                        title = a.get_text(strip=True)
                        
                        if not title or "/title/" not in href:
                            continue
                        
                        full_url = href if href.startswith("http") else "https://mangapark.io" + href
                        key = (title, full_url)
                        
                        if key not in seen:
                            seen.add(key)
                            results.append({"title": title, "url": full_url})
                            count += 1
                    
                    emit_log(f"Found {count} titles on page {page}")
                    
                    if count == 0 or page > 100:
                        break
                    
                    page += 1
            else:
                # Public mode - scrape /latest
                emit_log("Public mode: Scraping latest manga...")
                driver.get("https://mangapark.io/latest")
                time.sleep(3)
                
                # Scroll to load more content
                for i in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    emit_log(f"Loading more content... ({i+1}/5)")
                    self.current_progress["percent"] = (i + 1) * 18
                    time.sleep(2)
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                links = soup.select("a[href*='/title/']")
                
                for a in links:
                    href = a.get("href", "")
                    title = a.get_text(strip=True)
                    
                    if not title or "/title/" not in href:
                        continue
                    
                    full_url = href if href.startswith("http") else "https://mangapark.io" + href
                    key = (title, full_url)
                    
                    if key not in seen:
                        seen.add(key)
                        results.append({"title": title, "url": full_url})
                
                emit_log(f"Found {len(results)} manga")
            
            self.current_progress["percent"] = 90
            return results
            
        except Exception as e:
            emit_log(f"Scraping error: {str(e)}", "error")
            raise
        finally:
            emit_log("Closing browser...")
            driver.quit()
    
    def enrich_with_mal_ids(self, manga_list, emit_log):
        """Enrich manga list with MAL IDs (parallélisé, 1 req/s)"""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        lock = threading.Lock()
        enriched = [None] * len(manga_list)
        total = len(manga_list)
        found_count = 0
        last_req_time = [0]

        def worker(idx, manga):
            title = manga["title"]
            if title.lower().startswith(("chapter", "ch.", "vol.")):
                return None
            emit_log(f"Searching MAL: {title[:40]}...")
            # Respect rate limit
            with lock:
                now = time.time()
                wait = max(0, 1 - (now - last_req_time[0]))
                if wait > 0:
                    time.sleep(wait)
                last_req_time[0] = time.time()
                mal_id, mal_title, score = self.search_mal_id(title)
            if mal_id:
                result = {"title": title, "url": manga["url"], "mal_id": mal_id, "mal_title": mal_title, "score": score}
            else:
                result = {"title": title, "url": manga["url"], "mal_id": "0", "mal_title": "", "score": 0}
            return (idx, result, bool(mal_id))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, idx, manga) for idx, manga in enumerate(manga_list)]
            for done_idx, fut in enumerate(as_completed(futures), 1):
                res = fut.result()
                if res:
                    idx, result, found = res
                    enriched[idx] = result
                    if found:
                        found_count += 1
                progress = 30 + int((done_idx / total) * 30)
                self.current_progress["percent"] = progress
        emit_log(f"Found {found_count}/{total} on MAL ({found_count/total*100:.1f}%)", "success")
        return [e for e in enriched if e]
    
    def search_mal_id(self, title):
        """Search MAL for manga ID"""
        try:
            url = "https://api.jikan.moe/v4/manga"
            params = {"q": title, "limit": 5}
            resp = requests.get(url, params=params, timeout=10)
            
            if resp.status_code == 429:
                time.sleep(2)
                return None, None, 0
            
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
                ratio = SequenceMatcher(None, title.lower(), mal_title.lower()).ratio()
                
                if ratio > best_score:
                    best_score = ratio
                    best_match = manga
            
            if best_match and best_score > 0.6:
                return str(best_match["mal_id"]), best_match["title"], best_score
            
            return None, None, 0
        except:
            return None, None, 0
    
    def generate_mal_xml(self, manga_list, output_path, emit_log):
        """Generate MAL XML file"""
        root = ET.Element("myanimelist")
        
        myinfo = ET.SubElement(root, "myinfo")
        ET.SubElement(myinfo, "user_name").text = "mangapark_export"
        ET.SubElement(myinfo, "user_export_type").text = "2"
        ET.SubElement(myinfo, "user_total_manga").text = str(len(manga_list))
        
        for m in manga_list:
            if m["mal_id"] != "0":
                entry = ET.SubElement(root, "manga")
                ET.SubElement(entry, "manga_mangadb_id").text = m["mal_id"]
                ET.SubElement(entry, "manga_title").text = m["title"]
                ET.SubElement(entry, "my_status").text = "Plan to Read"
                ET.SubElement(entry, "manga_mangapark_url").text = m["url"]
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        emit_log(f"XML saved: {output_path}", "success")
    
    def generate_html(self, manga_list, output_path, emit_log):
        """Generate HTML report"""
        manga_list.sort(key=lambda x: (x["mal_id"] == "0", x["title"].lower()))
        found = sum(1 for m in manga_list if m["mal_id"] != "0")
        
        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>MangaPark Export</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box}}
body {{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}}
.container {{max-width:1200px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3)}}
header {{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:40px;text-align:center}}
h1 {{font-size:2.5rem}}
.stats {{display:flex;gap:40px;justify-content:center;margin-top:20px;flex-wrap:wrap}}
.stat {{background:rgba(255,255,255,0.1);padding:15px 30px;border-radius:8px}}
.stat-value {{font-size:2rem;font-weight:bold}}
.stat-label {{font-size:0.9rem;opacity:0.9;margin-top:5px}}
.manga-list {{padding:40px}}
.manga-item {{display:flex;align-items:center;padding:20px;border-bottom:1px solid #e9ecef}}
.manga-item:hover {{background:#f8f9fa}}
.manga-status {{width:12px;height:12px;border-radius:50%;margin-right:20px}}
.status-found {{background:#10b981}}
.status-not-found {{background:#ef4444}}
.manga-title {{flex:1;font-size:1.1rem;font-weight:500}}
.manga-links {{display:flex;gap:10px}}
.manga-link {{padding:8px 16px;border-radius:6px;text-decoration:none;font-size:0.85rem;color:white}}
.mal-link {{background:#2e51a2}}
.mangapark-link {{background:#667eea}}
</style></head><body>
<div class="container">
<header><h1>📚 MangaPark Export</h1>
<div class="stats">
<div class="stat"><div class="stat-value">{len(manga_list)}</div><div class="stat-label">Total</div></div>
<div class="stat"><div class="stat-value">{found}</div><div class="stat-label">Found</div></div>
<div class="stat"><div class="stat-value">{len(manga_list)-found}</div><div class="stat-label">Not Found</div></div>
<div class="stat"><div class="stat-value">{found/len(manga_list)*100:.1f}%</div><div class="stat-label">Success</div></div>
</div></header>
<div class="manga-list">'''
        
        for m in manga_list:
            has_id = m["mal_id"] != "0"
            status = "status-found" if has_id else "status-not-found"
            mal_url = f"https://myanimelist.net/manga/{m['mal_id']}" if has_id else "#"
            
            html += f'''<div class="manga-item">
<div class="manga-status {status}"></div>
<div class="manga-title">{m["title"]}</div>
<div class="manga-links">
<a href="{mal_url}" class="manga-link mal-link" target="_blank">MAL</a>
<a href="{m["url"]}" class="manga-link mangapark-link" target="_blank">MangaPark</a>
</div></div>'''
        
        html += '''</div></div></body></html>'''
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        emit_log(f"HTML saved: {output_path}", "success")
    
    @pyqtSlot(result=str)
    def get_progress(self):
        """Get current progress"""
        return json.dumps(self.current_progress)
    
    @pyqtSlot(result=str)
    def get_sites(self):
        """Get available sites"""
        sites = [
            {"id": "mangapark", "name": "MangaPark", "url": "https://mangapark.net", "status": "active"},
            {"id": "mangadex", "name": "MangaDex", "url": "https://mangadex.org", "status": "planned"},
            {"id": "mangasee", "name": "MangaSee", "url": "https://mangasee123.com", "status": "planned"}
        ]
        return json.dumps(sites)
    
    @pyqtSlot(result=str)
    def open_html(self):
        """Open generated HTML file"""
        html_path = os.path.join("output", "manga_list.html")
        if os.path.exists(html_path):
            webbrowser.open(f"file:///{os.path.abspath(html_path)}")
            return json.dumps({"status": "success"})
        return json.dumps({"status": "error", "message": "HTML file not found"})
    
    @pyqtSlot(result=str)
    def open_folder(self):
        """Open output folder"""
        if os.path.exists("output"):
            os.startfile(os.path.abspath("output"))
            return json.dumps({"status": "success"})
        return json.dumps({"status": "error", "message": "Output folder not found"})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Multi-Site Manga Exporter")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create web view
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        
        # Set up WebChannel for JavaScript communication
        self.channel = QWebChannel()
        self.api = BackendAPI()
        self.channel.registerObject('backend', self.api)
        self.browser.page().setWebChannel(self.channel)
        
        # Connect progress signal to update UI
        self.api.progressUpdate.connect(self.on_progress_update)
        
        # Load HTML
        html_file = Path("mangapark_gui_web.html")
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Inject QWebChannel script and API bridge
        webchannel_script = """
        <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script type="text/javascript">
        let backendAPI = null;
        
        // Initialize WebChannel
        new QWebChannel(qt.webChannelTransport, function(channel) {
            backendAPI = channel.objects.backend;
            window.backendAPI = backendAPI;  // Make it globally accessible
            
            // Connect progress updates
            backendAPI.progressUpdate.connect(function(percent, step, log) {
                if (typeof updateProgress === 'function') updateProgress(percent);
                if (typeof updateStep === 'function') updateStep(step, 'active');
                if (typeof addLog === 'function' && log) {
                    const message = typeof log === 'string' ? log : (log.message || String(log));
                    const type = (typeof log === 'object' && log.type) ? log.type : 'info';
                    addLog(message, type);
                }
            });
            
            console.log('Backend API connected!');
        });
        
        // Override startDemo to use real export
        window.addEventListener('load', function() {
            setTimeout(function() {
                window.originalStartDemo = window.startDemo;
                window.startDemo = async function() {
                    if (!backendAPI) {
                        showToast('Backend not ready, please wait...', 'warning');
                        return;
                    }
                    
                    // Check if we're in public mode by looking at the active mode card
                    const activeModeCard = document.querySelector('.mode-card.active');
                    const modeText = activeModeCard ? activeModeCard.querySelector('.mode-title')?.textContent : '';
                    const isPublicMode = modeText === 'Public' || window.currentMode === 'public';
                    
                    console.log('Mode detected:', modeText, 'isPublic:', isPublicMode);
                    
                    const config = {
                        mode: isPublicMode ? 'public' : 'authenticated',
                        cookies: {
                            skey: document.getElementById('skeyCookie')?.value || '',
                            tfv: document.getElementById('tfvCookie')?.value || '',
                            theme: document.getElementById('themeCookie')?.value || '',
                            wd: document.getElementById('wdCookie')?.value || ''
                        }
                    };
                    
                    // Only check cookies if in authenticated mode
                    if (!isPublicMode && (!config.cookies.skey || !config.cookies.tfv)) {
                        showToast('Please enter at least skey and tfv cookies', 'error');
                        return;
                    }
                    
                    // In public mode, show info message
                    if (isPublicMode) {
                        showToast('Starting public export (latest manga)...', 'success');
                    }
                    
                    try {
                        const result = await new Promise((resolve) => {
                            backendAPI.start_export(JSON.stringify(config), resolve);
                        });
                        
                        const data = JSON.parse(result);
                        if (data.status === 'started') {
                            showToast('Export started! Check progress below', 'success');
                        } else {
                            showToast('Failed to start: ' + (data.message || 'Unknown error'), 'error');
                        }
                    } catch (error) {
                        showToast('Error: ' + error, 'error');
                    }
                };
            }, 1000);
        });
        </script>
        """
        
        html_content = html_content.replace('</head>', webchannel_script + '</head>')
        
        # Load HTML content
        self.browser.setHtml(html_content, QUrl.fromLocalFile(str(html_file.absolute())))
    
    def on_progress_update(self, percent, step, log):
        """Handle progress updates from backend"""
        print(f"Progress: {percent}% | Step: {step} | {log.get('message', '')}")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Multi-Site Manga Exporter")
    app.setOrganizationName("N3uralCreativity")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
