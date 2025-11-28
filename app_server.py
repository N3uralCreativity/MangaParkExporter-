"""
Desktop app using Flask server + default browser
Simpler and more reliable than pywebview
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import threading
import webbrowser
import time
from pathlib import Path
import backend_export

app = Flask(__name__)
CORS(app)

# Global state
current_progress = {"percent": 0, "step": 0, "logs": [], "status": "idle"}
export_thread = None

@app.route('/')
def index():
    """Serve the main HTML interface"""
    html_file = Path("mangapark_gui_web.html")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Inject backend API calls
    api_js = """
    <script>
    // Backend API endpoints
    const API_BASE = 'http://localhost:5000';
    
    // Override startDemo to use real export
    window.originalStartDemo = window.startDemo;
    window.startDemo = async function() {
        const config = {
            cookies: {
                skey: document.getElementById('skeyCookie')?.value || '',
                tfv: document.getElementById('tfvCookie')?.value || '',
                theme: document.getElementById('themeCookie')?.value || '',
                wd: document.getElementById('wdCookie')?.value || ''
            }
        };
        
        if (!config.cookies.skey || !config.cookies.tfv) {
            showToast('Please enter at least skey and tfv cookies', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/export/start`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            const result = await response.json();
            
            if (result.status === 'started') {
                showToast('Export started! Check progress below', 'success');
                startProgressPolling();
            } else {
                showToast('Failed to start export', 'error');
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        }
    };
    
    // Poll for progress updates
    let progressInterval = null;
    function startProgressPolling() {
        if (progressInterval) clearInterval(progressInterval);
        
        progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/export/progress`);
                const data = await response.json();
                
                if (data.percent !== undefined) {
                    updateProgress(data.percent);
                }
                
                if (data.step !== undefined) {
                    updateStep(data.step, 'active');
                }
                
                // Add new logs
                if (data.logs && data.logs.length > 0) {
                    const logContainer = document.getElementById('logContainer');
                    const currentLogCount = logContainer?.children.length || 0;
                    
                    for (let i = currentLogCount; i < data.logs.length; i++) {
                        addLog(data.logs[i]);
                    }
                }
                
                // Stop polling if completed or error
                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(progressInterval);
                    progressInterval = null;
                    
                    if (data.status === 'completed') {
                        showToast('Export completed successfully!', 'success');
                    }
                }
            } catch (error) {
                console.error('Progress polling error:', error);
            }
        }, 500);
    }
    </script>
    """
    
    html_content = html_content.replace('</body>', api_js + '</body>')
    return html_content

@app.route('/api/export/start', methods=['POST'])
def start_export():
    """Start export process"""
    global current_progress, export_thread
    
    data = request.json
    cookies = data.get('cookies', {})
    
    # Validate cookies
    if not cookies.get('skey') or not cookies.get('tfv'):
        return jsonify({"status": "error", "message": "Missing required cookies"}), 400
    
    # Reset progress
    current_progress = {"percent": 0, "step": 0, "logs": [], "status": "running"}
    
    def run_export():
        global current_progress
        
        def progress_callback(percent, step, log_entry):
            current_progress["percent"] = percent
            current_progress["step"] = step
            current_progress["logs"].append(log_entry)
            print(f"[{log_entry['time']}] {log_entry['message']}")
        
        try:
            result = backend_export.export_mangapark(cookies, progress_callback)
            current_progress["status"] = "completed" if result["status"] == "success" else "error"
            current_progress["result"] = result
        except Exception as e:
            current_progress["status"] = "error"
            current_progress["logs"].append({
                "type": "error",
                "message": f"Export failed: {str(e)}",
                "time": time.strftime("%H:%M:%S")
            })
    
    export_thread = threading.Thread(target=run_export)
    export_thread.daemon = True
    export_thread.start()
    
    return jsonify({"status": "started"})

@app.route('/api/export/progress', methods=['GET'])
def get_progress():
    """Get current export progress"""
    return jsonify(current_progress)

@app.route('/api/sites', methods=['GET'])
def get_sites():
    """Get available manga sites"""
    return jsonify([
        {"id": "mangapark", "name": "MangaPark", "url": "https://mangapark.net", "status": "active"},
        {"id": "mangadex", "name": "MangaDex", "url": "https://mangadex.org", "status": "planned"},
        {"id": "mangasee", "name": "MangaSee", "url": "https://mangasee123.com", "status": "planned"}
    ])

def open_browser():
    """Open browser after server starts"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Multi-Site Manga Exporter")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("Opening browser in 1.5 seconds...")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask server
    app.run(host='localhost', port=5000, debug=False, use_reloader=False)
