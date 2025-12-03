"""
Multi-Site Manga Exporter - Desktop Application V3
Complete rewrite with perfect functionality
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
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class BackendAPI(QObject):
    """Backend API exposed to JavaScript"""
    
    # Signals
    progressUpdate = pyqtSignal(int, int, str, str)  # percent, step, message, type
    exportComplete = pyqtSignal(dict)  # result data
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        # Use current directory for output, works in both dev and exe mode
        if getattr(sys, 'frozen', False):
            # Running as compiled exe - use exe directory
            self.output_dir = os.path.join(os.path.dirname(sys.executable), "output")
        else:
            # Running in development
            self.output_dir = "output"
        
        # Export settings
        self.export_settings = {
            'includeUnmatched': True,
            'exportFormat': 'MAL XML + HTML',
            'requestTimeout': 30,
            'maxRetries': 3,
            'rateLimit': 2
        }
    
    @pyqtSlot(str, result=str)
    def start_export(self, config_json):
        """Start export with configuration"""
        if self.is_running:
            return json.dumps({"status": "error", "message": "Export already running"})
        
        if not SELENIUM_AVAILABLE:
            return json.dumps({"status": "error", "message": "Selenium not installed"})
        
        try:
            config = json.loads(config_json)
            mode = config.get('mode', 'authenticated')
            cookies = config.get('cookies', {})
            
            # Update export settings from config
            if 'settings' in config:
                self.export_settings.update(config['settings'])
            
            # Update output directory if provided
            if 'outputDirectory' in config:
                custom_output = config['outputDirectory']
                if custom_output and custom_output != './output':
                    self.output_dir = custom_output
            
            # Validate authenticated mode
            if mode == 'authenticated':
                if not cookies.get('skey') or not cookies.get('tfv'):
                    return json.dumps({"status": "error", "message": "Missing required cookies (skey and tfv)"})
            
            # Start export thread
            self.is_running = True
            thread = threading.Thread(target=self._export_worker, args=(mode, cookies), daemon=True)
            thread.start()
            
            return json.dumps({"status": "started", "mode": mode})
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def _export_worker(self, mode, cookies):
        """Worker thread for export"""
        try:
            # Step 1: Scraping (0-25%)
            self._emit_log(0, 1, f"Starting {mode} mode export...", "info")
            self._emit_log(0, 1, "Initializing Chrome browser...", "info")
            
            manga_list = self._scrape_mangapark(mode, cookies)
            
            if not manga_list:
                self._emit_log(0, 1, "No manga found!", "error")
                self.is_running = False
                return
            
            self._emit_log(25, 1, f"✅ Found {len(manga_list)} manga", "success")
            
            # Step 2: Enriching (25-60%)
            self._emit_log(25, 2, "Searching MAL database for IDs...", "info")
            enriched_list = self._enrich_with_mal(manga_list)
            
            # Filter unmatched if setting disabled
            if not self.export_settings.get('includeUnmatched', True):
                original_count = len(enriched_list)
                enriched_list = [m for m in enriched_list if m['mal_id'] != '0']
                filtered = original_count - len(enriched_list)
                if filtered > 0:
                    self._emit_log(58, 2, f"⚠️ Filtered out {filtered} unmatched manga", "info")
            
            found = sum(1 for m in enriched_list if m['mal_id'] != '0')
            self._emit_log(60, 2, f"✅ Matched {found}/{len(enriched_list)} manga on MAL", "success")
            
            # Step 3: Generating Files (60-80%)
            os.makedirs(self.output_dir, exist_ok=True)
            
            export_format = self.export_settings.get('exportFormat', 'MAL XML + HTML')
            xml_path = None
            html_path = None
            json_path = None
            
            # Generate files based on format setting
            if export_format in ['MAL XML + HTML', 'MAL XML Only']:
                self._emit_log(60, 3, "Generating MAL XML export...", "info")
                xml_path = os.path.join(self.output_dir, "mangapark_to_mal.xml")
                self._generate_mal_xml(enriched_list, xml_path)
                self._emit_log(70, 3, "✅ XML file created", "success")
            
            if export_format in ['MAL XML + HTML', 'HTML Only']:
                self._emit_log(70, 3, "Generating HTML visualization...", "info")
                html_path = os.path.join(self.output_dir, "manga_list.html")
                self._generate_html(enriched_list, html_path)
                self._emit_log(80, 3, "✅ HTML file created", "success")
            
            if export_format == 'JSON':
                self._emit_log(70, 3, "Generating JSON export...", "info")
                json_path = os.path.join(self.output_dir, "manga_list.json")
                self._generate_json(enriched_list, json_path)
                self._emit_log(80, 3, "✅ JSON file created", "success")
            
            # Step 4: Complete (80-100%)
            self._emit_log(90, 4, "Saving files...", "info")
            self._emit_log(100, 4, "🎉 Export completed successfully!", "success")
            
            # Emit completion
            result = {
                "status": "success",
                "total": len(enriched_list),
                "found": found,
                "xml_path": xml_path if xml_path else "",
                "html_path": html_path if html_path else "",
                "json_path": json_path if json_path else "",
                "format": export_format
            }
            self.exportComplete.emit(result)
            
        except Exception as e:
            self._emit_log(0, 0, f"❌ Error: {str(e)}", "error")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
    
    def _scrape_mangapark(self, mode, cookies):
        """Scrape MangaPark for manga list"""
        self._emit_log(5, 1, "Starting browser...", "info")
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        results = []
        seen = set()
        
        try:
            if mode == 'authenticated':
                # Authenticated mode
                self._emit_log(10, 1, "Loading your follows list...", "info")
                driver.get("https://mangapark.io/my/follows")
                
                # Add cookies
                for name, value in cookies.items():
                    if value:
                        driver.add_cookie({"name": name, "value": value, "domain": ".mangapark.io"})
                
                driver.refresh()
                time.sleep(3)
                
                page = 1
                while page <= 10:  # Max 10 pages
                    progress = 10 + (page * 1)
                    self._emit_log(progress, 1, f"Scraping page {page}...", "info")
                    
                    url = f"https://mangapark.io/my/follows?page={page}"
                    driver.get(url)
                    time.sleep(4)
                    
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
                    
                    if count == 0:
                        break
                    
                    page += 1
                    
            else:
                # Public mode
                self._emit_log(10, 1, "Loading latest manga...", "info")
                driver.get("https://mangapark.io/latest")
                time.sleep(3)
                
                # Scroll to load more
                for i in range(5):
                    progress = 10 + (i * 2)
                    self._emit_log(progress, 1, f"Loading content ({i+1}/5)...", "info")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
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
            
            return results
            
        finally:
            driver.quit()
    
    def _enrich_with_mal(self, manga_list):
        """Enrich manga list with MAL IDs"""
        enriched = []
        total = len(manga_list)
        found_count = 0
        
        for idx, manga in enumerate(manga_list, 1):
            title = manga["title"]
            
            # Skip chapter titles
            if title.lower().startswith(("chapter", "ch.", "vol.")):
                continue
            
            # Progress calculation
            progress = 25 + int((idx / total) * 35)
            self._emit_log(progress, 2, f"[{idx}/{total}] {title[:50]}...", "info")
            
            mal_id, mal_title, score = self._search_mal(title)
            
            if mal_id:
                enriched.append({
                    "title": title,
                    "url": manga["url"],
                    "mal_id": mal_id,
                    "mal_title": mal_title,
                    "score": score
                })
                found_count += 1
            else:
                enriched.append({
                    "title": title,
                    "url": manga["url"],
                    "mal_id": "0",
                    "mal_title": "",
                    "score": 0
                })
            
            time.sleep(1)  # Rate limit
        
        return enriched
    
    def _search_mal(self, title):
        """Search MAL for manga"""
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
    
    def _generate_mal_xml(self, manga_list, output_path):
        """Generate MAL XML export"""
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
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
    
    def _generate_html(self, manga_list, output_path):
        """Generate HTML visualization"""
        manga_list.sort(key=lambda x: (x["mal_id"] == "0", x["title"].lower()))
        found = sum(1 for m in manga_list if m["mal_id"] != "0")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MangaPark Export - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 50px;
            text-align: center;
        }}
        h1 {{ font-size: 3rem; margin-bottom: 20px; }}
        .stats {{
            display: flex;
            gap: 30px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 30px;
        }}
        .stat {{
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            border-radius: 12px;
            min-width: 120px;
        }}
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 8px;
            display: block;
        }}
        .controls {{
            padding: 30px 50px;
            background: #f8f9fa;
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
            border-bottom: 1px solid #e9ecef;
        }}
        .search-box {{
            flex: 1;
            min-width: 300px;
        }}
        .search-box input {{
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s;
        }}
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        .filter-btn {{
            padding: 12px 24px;
            border: 2px solid #e9ecef;
            background: white;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }}
        .filter-btn:hover {{ border-color: #667eea; color: #667eea; transform: translateY(-2px); }}
        .filter-btn.active {{ background: #667eea; color: white; border-color: #667eea; }}
        .manga-list {{
            padding: 50px;
            max-height: 1000px;
            overflow-y: auto;
        }}
        .manga-item {{
            display: flex;
            align-items: center;
            padding: 25px;
            border-bottom: 1px solid #f0f0f0;
            transition: all 0.3s;
        }}
        .manga-item:hover {{
            background: #f8f9fa;
            transform: translateX(5px);
        }}
        .manga-status {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            margin-right: 25px;
            flex-shrink: 0;
        }}
        .status-found {{
            background: #10b981;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.5);
        }}
        .status-not-found {{
            background: #ef4444;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
        }}
        .manga-content {{ flex: 1; }}
        .manga-title {{
            font-size: 1.15rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
        }}
        .manga-info {{
            font-size: 0.9rem;
            color: #64748b;
        }}
        .manga-links {{
            display: flex;
            gap: 12px;
        }}
        .manga-link {{
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s;
            color: white;
        }}
        .mal-link {{
            background: #2e51a2;
        }}
        .mal-link:hover {{ background: #1e3a8a; transform: translateY(-2px); }}
        .mal-link.disabled {{
            background: #d1d5db;
            color: #9ca3af;
            pointer-events: none;
        }}
        .mangapark-link {{
            background: #667eea;
        }}
        .mangapark-link:hover {{ background: #5568d3; transform: translateY(-2px); }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 10px;
        }}
        .badge-high {{ background: #d1fae5; color: #065f46; }}
        .badge-medium {{ background: #fef3c7; color: #92400e; }}
        .badge-low {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 MangaPark Export</h1>
            <div class="stats">
                <div class="stat">
                    <span class="stat-value">{len(manga_list)}</span>
                    <span class="stat-label">Total Manga</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{found}</span>
                    <span class="stat-label">Found on MAL</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{len(manga_list) - found}</span>
                    <span class="stat-label">Not Found</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{found/len(manga_list)*100:.1f}%</span>
                    <span class="stat-label">Success Rate</span>
                </div>
            </div>
        </header>
        
        <div class="controls">
            <div class="search-box">
                <input type="text" id="search" placeholder="🔍 Search manga...">
            </div>
            <button class="filter-btn active" data-filter="all">All</button>
            <button class="filter-btn" data-filter="found">✓ Found</button>
            <button class="filter-btn" data-filter="not-found">✗ Not Found</button>
        </div>
        
        <div class="manga-list" id="list">'''
        
        for m in manga_list:
            has_id = m["mal_id"] != "0"
            status_class = "status-found" if has_id else "status-not-found"
            mal_url = f"https://myanimelist.net/manga/{m['mal_id']}" if has_id else "#"
            disabled = "" if has_id else "disabled"
            
            info = ""
            if has_id:
                score = m.get("score", 0)
                badge_class = "badge-high" if score > 0.8 else "badge-medium" if score > 0.6 else "badge-low"
                info = f'MAL: {m["mal_title"]}<span class="badge {badge_class}">{score*100:.0f}% match</span>'
            else:
                info = "Not found on MyAnimeList"
            
            html += f'''
            <div class="manga-item" data-status="{'found' if has_id else 'not-found'}">
                <div class="manga-status {status_class}"></div>
                <div class="manga-content">
                    <div class="manga-title">{m["title"]}</div>
                    <div class="manga-info">{info}</div>
                </div>
                <div class="manga-links">
                    <a href="{mal_url}" class="manga-link mal-link {disabled}" target="_blank">MAL</a>
                    <a href="{m["url"]}" class="manga-link mangapark-link" target="_blank">MangaPark</a>
                </div>
            </div>'''
        
        html += '''
        </div>
    </div>
    
    <script>
        const search = document.getElementById('search');
        const items = document.querySelectorAll('.manga-item');
        const btns = document.querySelectorAll('.filter-btn');
        let filter = 'all';
        
        function update() {
            const value = search.value.toLowerCase();
            items.forEach(item => {
                const title = item.querySelector('.manga-title').textContent.toLowerCase();
                const status = item.dataset.status;
                const matchesSearch = title.includes(value);
                const matchesFilter = filter === 'all' || status === filter;
                item.style.display = (matchesSearch && matchesFilter) ? 'flex' : 'none';
            });
        }
        
        search.addEventListener('input', update);
        
        btns.forEach(btn => {
            btn.addEventListener('click', () => {
                btns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                filter = btn.dataset.filter;
                update();
            });
        });
    </script>
</body>
</html>'''
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    def _generate_json(self, manga_list, output_path):
        """Generate JSON export file"""
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_manga": len(manga_list),
            "matched_mal": sum(1 for m in manga_list if m['mal_id'] != '0'),
            "manga": []
        }
        
        for manga in manga_list:
            export_data["manga"].append({
                "title": manga["title"],
                "mal_id": manga["mal_id"],
                "similarity": manga.get("similarity", 0),
                "url": manga.get("url", ""),
                "status": "matched" if manga["mal_id"] != '0' else "unmatched"
            })
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _emit_log(self, percent, step, message, log_type):
        """Emit log message"""
        self.progressUpdate.emit(percent, step, message, log_type)
        print(f"[{percent}%] Step {step}: {message}")
    
    @pyqtSlot(result=str)
    def open_html(self):
        """Open generated HTML file"""
        html_path = os.path.join(self.output_dir, "manga_list.html")
        if os.path.exists(html_path):
            webbrowser.open(f"file:///{os.path.abspath(html_path)}")
            return json.dumps({"status": "success"})
        return json.dumps({"status": "error", "message": "HTML file not found"})
    
    @pyqtSlot(result=str)
    def open_folder(self):
        """Open output folder"""
        if os.path.exists(self.output_dir):
            os.startfile(os.path.abspath(self.output_dir))
            return json.dumps({"status": "success"})
        return json.dumps({"status": "error", "message": "Output folder not found"})


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Multi-Site Manga Exporter v3.0")
        self.showMaximized()  # Start maximized to fill the screen
        
        # Create web view
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        
        # Set up WebChannel
        self.channel = QWebChannel()
        self.api = BackendAPI()
        self.channel.registerObject('backend', self.api)
        self.browser.page().setWebChannel(self.channel)
        
        # Load HTML - support both dev and exe modes
        html_file = Path("mangapark_gui_web.html")
        
        # When frozen (running as .exe), PyInstaller extracts to _MEIPASS
        if getattr(sys, 'frozen', False):
            bundle_dir = Path(sys._MEIPASS)
            html_file = bundle_dir / "mangapark_gui_web.html"
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Inject WebChannel script
        webchannel_script = '''
        <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script type="text/javascript">
        window.backendAPI = null;
        
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.backendAPI = channel.objects.backend;
            
            // Connect signals
            window.backendAPI.progressUpdate.connect(function(percent, step, message, type) {
                console.log(`Progress: ${percent}% | Step: ${step} | ${message}`);
                
                // Update progress bar
                if (typeof updateProgress === 'function') {
                    updateProgress(percent);
                }
                
                // Update step indicator
                if (typeof updateStep === 'function') {
                    if (step > 0 && step <= 4) {
                        if (percent === 100) {
                            updateStep(step - 1, 'done');
                        } else {
                            updateStep(step - 1, 'active');
                        }
                    }
                }
                
                // Add log entry
                if (typeof addLog === 'function') {
                    addLog(message, type);
                }
            });
            
            window.backendAPI.exportComplete.connect(function(result) {
                console.log('Export complete:', result);
                if (typeof showToast === 'function') {
                    showToast('Export completed! Files saved to output folder.', 'success');
                }
                
                // Re-enable buttons
                const startBtn = document.getElementById('startBtn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.innerHTML = '▶️ Start Export';
                }
            });
            
            console.log('✅ Backend API connected and ready!');
        });
        
        // Override startDemo
        window.addEventListener('load', function() {
            setTimeout(function() {
                window.startExport = async function() {
                    if (!window.backendAPI) {
                        if (typeof showToast === 'function') {
                            showToast('Backend not ready, please wait...', 'warning');
                        }
                        return;
                    }
                    
                    // Get mode
                    const activeModeCard = document.querySelector('.mode-card.active');
                    const modeText = activeModeCard ? activeModeCard.querySelector('.mode-title')?.textContent : '';
                    const isPublicMode = modeText === 'Public' || window.currentMode === 'public';
                    
                    // Get config
                    const config = {
                        mode: isPublicMode ? 'public' : 'authenticated',
                        cookies: {
                            skey: document.getElementById('skeyCookie')?.value || '',
                            tfv: document.getElementById('tfvCookie')?.value || '',
                            theme: document.getElementById('themeCookie')?.value || '',
                            wd: document.getElementById('wdCookie')?.value || ''
                        }
                    };
                    
                    // Validate authenticated mode
                    if (!isPublicMode && (!config.cookies.skey || !config.cookies.tfv)) {
                        if (typeof showToast === 'function') {
                            showToast('Please enter skey and tfv cookies for authenticated mode', 'error');
                        }
                        return;
                    }
                    
                    // Reset UI
                    if (typeof resetSteps === 'function') resetSteps();
                    if (typeof updateProgress === 'function') updateProgress(0);
                    const logContainer = document.getElementById('logContainer');
                    if (logContainer) logContainer.innerHTML = '';
                    
                    // Disable start button
                    const startBtn = document.getElementById('startBtn');
                    if (startBtn) {
                        startBtn.disabled = true;
                        startBtn.innerHTML = '<span class="spinner"></span> Exporting...';
                    }
                    
                    // Start export
                    try {
                        const result = await new Promise((resolve) => {
                            window.backendAPI.start_export(JSON.stringify(config), resolve);
                        });
                        
                        const data = JSON.parse(result);
                        if (data.status === 'started') {
                            if (typeof showToast === 'function') {
                                showToast(`Export started in ${data.mode} mode!`, 'success');
                            }
                        } else {
                            if (typeof showToast === 'function') {
                                showToast(data.message || 'Failed to start export', 'error');
                            }
                            if (startBtn) {
                                startBtn.disabled = false;
                                startBtn.innerHTML = '▶️ Start Export';
                            }
                        }
                    } catch (error) {
                        console.error('Export error:', error);
                        if (typeof showToast === 'function') {
                            showToast('Error: ' + error, 'error');
                        }
                        if (startBtn) {
                            startBtn.disabled = false;
                            startBtn.innerHTML = '▶️ Start Export';
                        }
                    }
                };
                
                // Override demo button
                const oldStartDemo = window.startDemo;
                window.startDemo = window.startExport;
            }, 1000);
        });
        
        // Open HTML function
        window.openHTML = function() {
            if (window.backendAPI && window.backendAPI.open_html) {
                window.backendAPI.open_html(function(result) {
                    const data = JSON.parse(result);
                    if (data.status === 'success') {
                        if (typeof showToast === 'function') {
                            showToast('Opening HTML file...', 'success');
                        }
                    } else {
                        if (typeof showToast === 'function') {
                            showToast(data.message || 'HTML file not found', 'error');
                        }
                    }
                });
            } else {
                if (typeof showToast === 'function') {
                    showToast('Please complete an export first', 'warning');
                }
            }
        };
        
        // Open Folder function
        window.openFolder = function() {
            if (window.backendAPI && window.backendAPI.open_folder) {
                window.backendAPI.open_folder(function(result) {
                    const data = JSON.parse(result);
                    if (data.status === 'success') {
                        if (typeof showToast === 'function') {
                            showToast('Opening output folder...', 'success');
                        }
                    } else {
                        if (typeof showToast === 'function') {
                            showToast(data.message || 'Output folder not found', 'error');
                        }
                    }
                });
            } else {
                if (typeof showToast === 'function') {
                    showToast('Please complete an export first', 'warning');
                }
            }
        };
        </script>
        '''
        
        html_content = html_content.replace('</head>', webchannel_script + '</head>')
        self.browser.setHtml(html_content, QUrl.fromLocalFile(str(html_file.absolute())))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Multi-Site Manga Exporter")
    app.setOrganizationName("N3uralCreativity")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
