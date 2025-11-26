import xml.etree.ElementTree as ET

def generate_html(input_xml, output_html):
    """Generate an HTML page listing all manga"""
    
    print(f"[INFO] Loading XML from {input_xml}...")
    tree = ET.parse(input_xml)
    root = tree.getroot()
    
    manga_list = []
    
    for manga in root.findall("manga"):
        title_elem = manga.find("manga_title")
        mal_id_elem = manga.find("manga_mangadb_id")
        url_elem = manga.find("manga_mangapark_url")
        
        if title_elem is None:
            continue
        
        title = title_elem.text or "Unknown"
        mal_id = mal_id_elem.text if mal_id_elem is not None else "0"
        mangapark_url = url_elem.text if url_elem is not None else ""
        
        has_mal_id = mal_id != "0"
        
        manga_list.append({
            "title": title,
            "mal_id": mal_id,
            "has_mal_id": has_mal_id,
            "mangapark_url": mangapark_url
        })
    
    # Sort: MAL IDs first, then alphabetically
    manga_list.sort(key=lambda x: (not x["has_mal_id"], x["title"].lower()))
    
    found_count = sum(1 for m in manga_list if m["has_mal_id"])
    not_found_count = len(manga_list) - found_count
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MangaPark Follows - MAL Export</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
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
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        .controls {{
            padding: 20px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .search-box {{
            flex: 1;
            min-width: 250px;
        }}
        
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
        
        .filter-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
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
        
        .manga-list {{
            padding: 40px;
        }}
        
        .manga-item {{
            display: flex;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            transition: background 0.3s;
        }}
        
        .manga-item:hover {{
            background: #f8f9fa;
        }}
        
        .manga-item:last-child {{
            border-bottom: none;
        }}
        
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
        
        .manga-content {{
            flex: 1;
            min-width: 0;
        }}
        
        .manga-title {{
            font-size: 1.1rem;
            font-weight: 500;
            color: #1f2937;
            margin-bottom: 5px;
        }}
        
        .manga-info {{
            font-size: 0.85rem;
            color: #6b7280;
        }}
        
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
            box-shadow: 0 4px 12px rgba(46, 81, 162, 0.4);
        }}
        
        .mangapark-link {{
            background: #667eea;
            color: white;
        }}
        
        .mangapark-link:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
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
        
        .no-results-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8rem;
            }}
            
            .stats {{
                gap: 20px;
            }}
            
            .stat {{
                padding: 10px 20px;
            }}
            
            .manga-item {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .manga-links {{
                margin-left: 32px;
                margin-top: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 MangaPark Follows</h1>
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
                <button class="filter-btn" data-filter="found">✓ Found on MAL</button>
                <button class="filter-btn" data-filter="not-found">✗ Not Found</button>
            </div>
        </div>
        
        <div class="manga-list" id="mangaList">
"""
    
    for manga in manga_list:
        status_class = "status-found" if manga["has_mal_id"] else "status-not-found"
        status_text = f"MAL ID: {manga['mal_id']}" if manga["has_mal_id"] else "Not found on MAL"
        mal_url = f"https://myanimelist.net/manga/{manga['mal_id']}" if manga["has_mal_id"] else "#"
        mal_disabled = "" if manga["has_mal_id"] else "disabled"
        
        html += f"""
            <div class="manga-item" data-status="{'found' if manga['has_mal_id'] else 'not-found'}">
                <div class="manga-status {status_class}"></div>
                <div class="manga-content">
                    <div class="manga-title">{manga['title']}</div>
                    <div class="manga-info">{status_text}</div>
                </div>
                <div class="manga-links">
                    <a href="{mal_url}" class="manga-link mal-link {mal_disabled}" target="_blank" rel="noopener">MAL</a>
                    <a href="{manga['mangapark_url']}" class="manga-link mangapark-link" target="_blank" rel="noopener">MangaPark</a>
                </div>
            </div>
"""
    
    html += """
        </div>
        
        <div class="no-results" id="noResults" style="display: none;">
            <div class="no-results-icon">🔍</div>
            <h2>No manga found</h2>
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
    
    print(f"[INFO] Writing HTML to {output_html}...")
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[DONE] HTML page created!")
    print(f"[INFO] Open {output_html} in your browser to view the list")


if __name__ == "__main__":
    generate_html("mangapark_follows_mal_enriched.xml", "manga_list.html")
