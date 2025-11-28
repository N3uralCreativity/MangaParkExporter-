import webview
import threading
import json
from pathlib import Path

# Import backend
import backend_export

# Global state
current_progress = {"percent": 0, "step": 0, "logs": [], "status": "idle"}

class API:
    def __init__(self):
        self.window = None
    
    def get_progress(self):
        """Get current export progress"""
        return current_progress
    
    def start_export(self, config):
        """Start manga export with given configuration"""
        global current_progress
        current_progress = {"percent": 0, "step": 0, "logs": [], "status": "running"}
        
        def run_export():
            try:
                # Extract config
                cookies = config.get('cookies', {})
                
                # Progress callback
                def progress_callback(percent, step, log_entry):
                    current_progress["percent"] = percent
                    current_progress["step"] = step
                    current_progress["logs"].append(log_entry)
                    
                    # Safe window evaluation
                    try:
                        if self.window and hasattr(self.window, 'evaluate_js'):
                            # Use simple string formatting instead of f-strings with complex objects
                            log_type = log_entry.get('type', 'info')
                            log_msg = log_entry.get('message', '').replace('"', '\\"').replace("'", "\\'")
                            log_time = log_entry.get('time', '')
                            
                            js_code = f"""
                                try {{
                                    if (typeof updateProgress === 'function') updateProgress({percent});
                                    if (typeof updateStep === 'function') updateStep({step}, 'active');
                                    if (typeof addLog === 'function') addLog({{
                                        type: '{log_type}',
                                        message: '{log_msg}',
                                        time: '{log_time}'
                                    }});
                                }} catch(e) {{
                                    console.error('JS error:', e);
                                }}
                            """
                            self.window.evaluate_js(js_code)
                    except Exception as e:
                        print(f"Warning: Could not update UI: {e}")
                
                # Run actual export
                result = backend_export.export_mangapark(cookies, progress_callback)
                
                current_progress["status"] = result["status"]
                
                if result["status"] == "success":
                    try:
                        if self.window and hasattr(self.window, 'evaluate_js'):
                            matched = result.get("matched", 0)
                            total = result.get("total_manga", 0)
                            self.window.evaluate_js(f"""
                                try {{
                                    if (typeof showToast === 'function') {{
                                        showToast('Export completed! {matched}/{total} manga matched', 'success');
                                    }}
                                }} catch(e) {{ console.error(e); }}
                            """)
                    except Exception as e:
                        print(f"Warning: Could not show success toast: {e}")
                else:
                    try:
                        if self.window and hasattr(self.window, 'evaluate_js'):
                            error = result.get("error", "Unknown error").replace("'", "\\'")
                            self.window.evaluate_js(f"""
                                try {{
                                    if (typeof showToast === 'function') {{
                                        showToast('Export failed: {error}', 'error');
                                    }}
                                }} catch(e) {{ console.error(e); }}
                            """)
                    except Exception as e:
                        print(f"Warning: Could not show error toast: {e}")
                
            except Exception as e:
                current_progress["status"] = "error"
                error_msg = str(e).replace("'", "\\'")
                current_progress["logs"].append({"type": "error", "message": f"Error: {error_msg}"})
                try:
                    if self.window and hasattr(self.window, 'evaluate_js'):
                        self.window.evaluate_js(f"""
                            try {{
                                if (typeof showToast === 'function') {{
                                    showToast('Export failed: {error_msg}', 'error');
                                }}
                            }} catch(e) {{ console.error(e); }}
                        """)
                except:
                    print(f"Export error: {error_msg}")
        
        thread = threading.Thread(target=run_export)
        thread.daemon = True
        thread.start()
        
        return {"status": "started"}
    
    def get_sites(self):
        """Get list of available manga sites"""
        return [
            {"id": "mangapark", "name": "MangaPark", "url": "https://mangapark.net", "status": "active"},
            {"id": "mangadex", "name": "MangaDex", "url": "https://mangadex.org", "status": "planned"},
            {"id": "mangasee", "name": "MangaSee", "url": "https://mangasee123.com", "status": "planned"}
        ]
    
    def get_history(self):
        """Get export history"""
        history_file = Path("export_history.json")
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_settings(self, settings):
        """Save user settings"""
        settings_file = Path("settings.json")
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return {"status": "saved"}
    
    def load_settings(self):
        """Load user settings"""
        settings_file = Path("settings.json")
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "theme": "dark",
            "animation_speed": "normal",
            "notifications": True,
            "auto_open_html": False
        }

def create_window():
    """Create the application window"""
    api = API()
    
    # Read HTML file
    html_file = Path("mangapark_gui_web.html")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Inject backend bridge JavaScript
    bridge_js = """
    <script>
    // Backend API bridge
    window.startRealExport = async function() {
        const config = {
            site: 'mangapark',
            mode: selectedMode || 'authenticated',
            cookies: {
                skey: document.getElementById('skeyCookie')?.value || '',
                tfv: document.getElementById('tfvCookie')?.value || '',
                theme: document.getElementById('themeCookie')?.value || '',
                wd: document.getElementById('wdCookie')?.value || ''
            }
        };
        
        // Validate cookies
        if (!config.cookies.skey || !config.cookies.tfv) {
            showToast('Please enter at least skey and tfv cookies', 'error');
            return;
        }
        
        try {
            const result = await pywebview.api.start_export(config);
            if (result.status === 'started') {
                showToast('Export started! Check progress below', 'success');
            }
        } catch (error) {
            showToast('Failed to start export: ' + error, 'error');
        }
    };
    
    // Replace demo button click with real export
    function startDemo() {
        startRealExport();
    }
    </script>
    """
    
    html_content = html_content.replace('</body>', bridge_js + '</body>')
    
    # Create window
    window = webview.create_window(
        'Multi-Site Manga Exporter',
        html=html_content,
        js_api=api,
        width=1400,
        height=900,
        resizable=True,
        background_color='#0f172a',
        text_select=True
    )
    
    api.window = window
    return window

if __name__ == '__main__':
    try:
        window = create_window()
        webview.start(debug=False, http_server=True)
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
