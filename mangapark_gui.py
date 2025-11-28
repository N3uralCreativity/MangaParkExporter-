"""
MangaPark to MAL Exporter - GUI Version
========================================
Complete visual interface with progress tracking
"""

import sys
import os

# Check dependencies first
from dependency_checker import ensure_dependencies

if not ensure_dependencies():
    # Dependencies were just installed or user cancelled
    # Exit gracefully without waiting for input
    sys.exit(0)

# Now safe to import everything else
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import webbrowser
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
from difflib import SequenceMatcher

# Optional import for browser cookie fetching
try:
    import browser_cookie3
    BROWSER_COOKIE3_AVAILABLE = True
except (ImportError, Exception) as e:
    BROWSER_COOKIE3_AVAILABLE = False
    print(f"Warning: browser_cookie3 not available: {e}")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class MangaParkExporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MangaPark to MAL Exporter")
        
        # Maximize window
        self.root.state('zoomed')  # Windows fullscreen
        self.root.resizable(True, True)
        
        # Queue for thread communication
        self.log_queue = queue.Queue()
        self.running = False
        
        # Results
        self.manga_list = []
        self.enriched_list = []
        self.output_dir = "output"
        
        self.setup_ui()
        self.process_log_queue()
        
    def setup_ui(self):
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Title
        title_frame = tk.Frame(self.root, bg="#667eea", height=100)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="📚 MangaPark to MAL Exporter",
            font=("Segoe UI", 24, "bold"),
            bg="#667eea",
            fg="white"
        )
        title_label.pack(pady=25)
        
        # Main content
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configuration section
        config_frame = tk.LabelFrame(
            main_frame,
            text="⚙️ Configuration",
            font=("Segoe UI", 11, "bold"),
            bg="#f0f0f0",
            padx=15,
            pady=15
        )
        config_frame.pack(fill="x", pady=(0, 15))
        
        # Scraping mode
        mode_frame = tk.Frame(config_frame, bg="#f0f0f0")
        mode_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        tk.Label(
            mode_frame,
            text="Scraping Mode:",
            font=("Segoe UI", 10, "bold"),
            bg="#f0f0f0"
        ).pack(side="left", padx=(0, 15))
        
        self.scraping_mode = tk.StringVar(value="authenticated")
        
        tk.Radiobutton(
            mode_frame,
            text="🔒 Authenticated (with cookies)",
            variable=self.scraping_mode,
            value="authenticated",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            command=self.on_mode_change
        ).pack(side="left", padx=5)
        
        tk.Radiobutton(
            mode_frame,
            text="🌐 Public (no login required)",
            variable=self.scraping_mode,
            value="public",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            command=self.on_mode_change
        ).pack(side="left", padx=5)
        
        # Cookie section (for authenticated mode)
        self.cookie_container = tk.Frame(config_frame, bg="#f0f0f0")
        self.cookie_container.grid(row=1, column=0, sticky="ew", pady=5)
        
        tk.Label(
            self.cookie_container,
            text="MangaPark Cookies:",
            font=("Segoe UI", 10),
            bg="#f0f0f0"
        ).pack(anchor="w", pady=(0, 5))
        
        cookie_frame = tk.Frame(self.cookie_container, bg="#f0f0f0")
        cookie_frame.pack(fill="x")
        cookie_frame.columnconfigure(1, weight=1)
        
        # Individual cookie fields
        tk.Label(cookie_frame, text="skey:", bg="#f0f0f0", width=8).grid(row=0, column=0, sticky="w")
        self.skey_entry = tk.Entry(cookie_frame, width=70)
        self.skey_entry.grid(row=0, column=1, sticky="ew", pady=2)
        
        tk.Label(cookie_frame, text="tfv:", bg="#f0f0f0", width=8).grid(row=1, column=0, sticky="w")
        self.tfv_entry = tk.Entry(cookie_frame, width=70)
        self.tfv_entry.grid(row=1, column=1, sticky="ew", pady=2)
        
        tk.Label(cookie_frame, text="theme:", bg="#f0f0f0", width=8).grid(row=2, column=0, sticky="w")
        self.theme_entry = tk.Entry(cookie_frame, width=70)
        self.theme_entry.grid(row=2, column=1, sticky="ew", pady=2)
        
        tk.Label(cookie_frame, text="wd:", bg="#f0f0f0", width=8).grid(row=3, column=0, sticky="w")
        self.wd_entry = tk.Entry(cookie_frame, width=70)
        self.wd_entry.grid(row=3, column=1, sticky="ew", pady=2)
        
        # Buttons frame
        cookie_buttons_frame = tk.Frame(self.cookie_container, bg="#f0f0f0")
        cookie_buttons_frame.pack(pady=(10, 0), fill="x")
        
        auto_fetch_btn = tk.Button(
            cookie_buttons_frame,
            text="🔄 Auto-Fetch Cookies from Chrome",
            font=("Segoe UI", 9),
            bg="#667eea",
            fg="white",
            activebackground="#5568d3",
            activeforeground="white",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.auto_fetch_cookies
        )
        auto_fetch_btn.pack(side="left", padx=(0, 10))
        
        tutorial_btn = tk.Button(
            cookie_buttons_frame,
            text="❓ How to Get Cookies",
            font=("Segoe UI", 9),
            bg="#f59e0b",
            fg="white",
            activebackground="#d97706",
            activeforeground="white",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.show_cookie_tutorial
        )
        tutorial_btn.pack(side="left")
        
        # Progress section
        progress_frame = tk.LabelFrame(
            main_frame,
            text="📊 Progress",
            font=("Segoe UI", 11, "bold"),
            bg="#f0f0f0",
            padx=15,
            pady=15
        )
        progress_frame.pack(fill="x", pady=(0, 15))
        
        # Step indicators
        steps_container = tk.Frame(progress_frame, bg="#f0f0f0")
        steps_container.pack(fill="x", pady=(0, 10))
        
        self.step_labels = []
        self.step_icons = []
        steps = ["1. Scrape", "2. Enrich", "3. XML", "4. HTML"]
        
        for i, step_text in enumerate(steps):
            step_frame = tk.Frame(steps_container, bg="#f0f0f0")
            step_frame.pack(side="left", expand=True, fill="x", padx=5)
            
            icon = tk.Label(
                step_frame,
                text="⏳",
                font=("Segoe UI", 20),
                bg="#f0f0f0"
            )
            icon.pack()
            self.step_icons.append(icon)
            
            label = tk.Label(
                step_frame,
                text=step_text,
                font=("Segoe UI", 9),
                bg="#f0f0f0"
            )
            label.pack()
            self.step_labels.append(label)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=800
        )
        self.progress_bar.pack(fill="x", pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to start",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#666"
        )
        self.progress_label.pack()
        
        # Stats section
        stats_frame = tk.Frame(progress_frame, bg="#f0f0f0")
        stats_frame.pack(fill="x", pady=(10, 0))
        
        self.stats_labels = []
        stats = ["Total: 0", "Found: 0", "Not Found: 0", "Success: 0%"]
        
        for stat_text in stats:
            stat_label = tk.Label(
                stats_frame,
                text=stat_text,
                font=("Segoe UI", 10, "bold"),
                bg="#e0e0e0",
                fg="#333",
                padx=15,
                pady=8,
                relief="raised"
            )
            stat_label.pack(side="left", expand=True, fill="x", padx=5)
            self.stats_labels.append(stat_label)
        
        # Log section
        log_frame = tk.LabelFrame(
            main_frame,
            text="📋 Log",
            font=("Segoe UI", 11, "bold"),
            bg="#f0f0f0",
            padx=10,
            pady=10
        )
        log_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap="word",
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill="x")
        
        self.start_button = tk.Button(
            button_frame,
            text="▶️ Start Export",
            font=("Segoe UI", 12, "bold"),
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            padx=30,
            pady=12,
            cursor="hand2",
            command=self.start_export
        )
        self.start_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.open_html_button = tk.Button(
            button_frame,
            text="🌐 Open HTML",
            font=("Segoe UI", 12, "bold"),
            bg="#667eea",
            fg="white",
            activebackground="#5568d3",
            activeforeground="white",
            padx=30,
            pady=12,
            cursor="hand2",
            command=self.open_html,
            state="disabled"
        )
        self.open_html_button.pack(side="left", expand=True, fill="x", padx=5)
        
        self.open_folder_button = tk.Button(
            button_frame,
            text="📁 Open Folder",
            font=("Segoe UI", 12, "bold"),
            bg="#6b7280",
            fg="white",
            activebackground="#4b5563",
            activeforeground="white",
            padx=30,
            pady=12,
            cursor="hand2",
            command=self.open_folder,
            state="disabled"
        )
        self.open_folder_button.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
    def log(self, message, color=None):
        """Add message to log queue"""
        self.log_queue.put((message, color))
        # Also print to console for debugging
        print(f"[LOG] {message}")
        
    def process_log_queue(self):
        """Process log messages from queue"""
        try:
            while True:
                message, color = self.log_queue.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert("end", message + "\n")
                if color:
                    # Color the last line
                    last_line = self.log_text.index("end-2c linestart")
                    self.log_text.tag_add(color, last_line, "end-1c")
                    self.log_text.tag_config(color, foreground=color)
                self.log_text.see("end")
                self.log_text.config(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)
    
    def update_step(self, step_num, status):
        """Update step indicator (0-3, status: 'pending'/'running'/'done'/'error')"""
        icons = {
            'pending': '⏳',
            'running': '⚙️',
            'done': '✅',
            'error': '❌'
        }
        colors = {
            'pending': '#999',
            'running': '#667eea',
            'done': '#10b981',
            'error': '#ef4444'
        }
        
        if 0 <= step_num < len(self.step_icons):
            self.step_icons[step_num].config(text=icons.get(status, '⏳'))
            self.step_labels[step_num].config(fg=colors.get(status, '#999'))
    
    def update_stats(self, total=0, found=0, not_found=0):
        """Update statistics display"""
        success_rate = (found / total * 100) if total > 0 else 0
        
        self.stats_labels[0].config(text=f"Total: {total}")
        self.stats_labels[1].config(text=f"Found: {found}", bg="#d1fae5", fg="#065f46")
        self.stats_labels[2].config(text=f"Not Found: {not_found}", bg="#fee2e2", fg="#991b1b")
        self.stats_labels[3].config(text=f"Success: {success_rate:.1f}%")
    
    def on_mode_change(self):
        """Handle scraping mode change"""
        if self.scraping_mode.get() == "authenticated":
            self.cookie_container.grid()
        else:
            self.cookie_container.grid_remove()
    
    def auto_fetch_cookies(self):
        """Auto-fetch cookies from Chrome"""
        # Show warning dialog first
        warning_dialog = tk.Toplevel(self.root)
        warning_dialog.title("Auto-Fetch Warning")
        warning_dialog.geometry("600x600")
        warning_dialog.resizable(False, False)
        warning_dialog.transient(self.root)
        warning_dialog.grab_set()
        
        # Center the dialog
        warning_dialog.update_idletasks()
        x = (warning_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (warning_dialog.winfo_screenheight() // 2) - (600 // 2)
        warning_dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(warning_dialog, bg="#f59e0b", height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="⚠️ Auto-Fetch Warning",
            font=("Segoe UI", 16, "bold"),
            bg="#f59e0b",
            fg="white"
        ).pack(pady=20)
        
        # Content
        content_frame = tk.Frame(warning_dialog, bg="white")
        content_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        tk.Label(
            content_frame,
            text="Auto-fetching cookies can be unstable:",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#333"
        ).pack(anchor="w", pady=(0, 15))
        
        warnings = [
            "🛡️ May be flagged as suspicious by antivirus software",
            "🌐 Only works with Chrome browser",
            "📦 May fail with different Chrome versions",
            "🔐 Requires administrator privileges on some systems",
            "❌ Often fails even when Chrome is closed",
            "🔄 May need to restart application as admin"
        ]
        
        for warning in warnings:
            warning_frame = tk.Frame(content_frame, bg="#fef3c7", relief="solid", borderwidth=1)
            warning_frame.pack(fill="x", pady=5)
            
            tk.Label(
                warning_frame,
                text=warning,
                font=("Segoe UI", 9),
                bg="#fef3c7",
                fg="#92400e",
                anchor="w",
                padx=10,
                pady=8
            ).pack(fill="x")
        
        tk.Label(
            content_frame,
            text="\n💡 Recommended: Use manual method instead\n(Click 'How to Get Cookies' button)",
            font=("Segoe UI", 9, "italic"),
            bg="white",
            fg="#667eea",
            justify="center"
        ).pack(pady=(10, 0))
        
        # Buttons
        button_frame = tk.Frame(warning_dialog, bg="#f0f0f0", height=100)
        button_frame.pack(fill="x", side="bottom")
        button_frame.pack_propagate(False)
        
        button_container = tk.Frame(button_frame, bg="#f0f0f0")
        button_container.pack(expand=True, fill="x", padx=30, pady=20)
        
        result = {"proceed": False}
        
        def on_proceed():
            result["proceed"] = True
            warning_dialog.destroy()
        
        def on_cancel():
            result["proceed"] = False
            warning_dialog.destroy()
        
        proceed_btn = tk.Button(
            button_container,
            text="Proceed Anyway",
            font=("Segoe UI", 11, "bold"),
            bg="#f59e0b",
            fg="white",
            activebackground="#d97706",
            activeforeground="white",
            cursor="hand2",
            padx=30,
            pady=15,
            command=on_proceed
        )
        proceed_btn.pack(side="left", expand=True, fill="both", padx=(0, 10))
        
        cancel_btn = tk.Button(
            button_container,
            text="Cancel (Use Manual)",
            font=("Segoe UI", 11, "bold"),
            bg="#6b7280",
            fg="white",
            activebackground="#4b5563",
            activeforeground="white",
            cursor="hand2",
            padx=30,
            pady=15,
            command=on_cancel
        )
        cancel_btn.pack(side="left", expand=True, fill="both", padx=(10, 0))
        
        # Wait for user decision
        self.root.wait_window(warning_dialog)
        
        if not result["proceed"]:
            return
        
        # Check if browser_cookie3 is available
        if not BROWSER_COOKIE3_AVAILABLE:
            messagebox.showerror(
                "Feature Not Available",
                "Auto-fetch cookies is not available in this version.\n\n"
                "The .exe version has this feature disabled due to Windows security restrictions.\n\n"
                "Please use the manual cookie entry method:\n"
                "1. Click the '?' button for tutorial\n"
                "2. Copy cookies from Chrome DevTools\n"
                "3. Paste them in the fields below"
            )
            return
        
        # User confirmed, proceed with auto-fetch
        try:
            import browser_cookie3
            cookies = browser_cookie3.chrome(domain_name='mangapark.io')
            
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie.name] = cookie.value
            
            if 'skey' in cookie_dict:
                self.skey_entry.delete(0, "end")
                self.skey_entry.insert(0, cookie_dict['skey'])
            if 'tfv' in cookie_dict:
                self.tfv_entry.delete(0, "end")
                self.tfv_entry.insert(0, cookie_dict['tfv'])
            if 'theme' in cookie_dict:
                self.theme_entry.delete(0, "end")
                self.theme_entry.insert(0, cookie_dict['theme'])
            if 'wd' in cookie_dict:
                self.wd_entry.delete(0, "end")
                self.wd_entry.insert(0, cookie_dict['wd'])
            
            messagebox.showinfo("Success", "Cookies fetched successfully from Chrome!")
            
        except ImportError:
            # Offer to install browser_cookie3
            result = messagebox.askyesno(
                "Missing Dependency",
                "browser_cookie3 is not installed.\n\n"
                "Would you like to install it now?"
            )
            
            if result:
                self.install_browser_cookie3()
        except PermissionError:
            # Need admin privileges
            result = messagebox.askyesno(
                "Administrator Required",
                "Fetching cookies from Chrome requires administrator privileges.\n\n"
                "Would you like to restart the application as administrator?"
            )
            
            if result:
                self.restart_as_admin()
        except Exception as e:
            error_msg = str(e)
            
            # Provide helpful error messages based on the error type
            if "Could not find" in error_msg or "chrome" in error_msg.lower():
                messagebox.showerror(
                    "Chrome Cookies Not Accessible",
                    "Could not access Chrome cookies.\n\n"
                    "Common issues:\n"
                    "• Chrome encrypts cookies on newer versions\n"
                    "• Windows security blocks cookie access\n"
                    "• Chrome profile not found or corrupted\n\n"
                    "💡 Solution: Use the manual method instead\n"
                    "(Click 'How to Get Cookies' button)"
                )
            elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                messagebox.showerror(
                    "Access Denied",
                    "Cannot access Chrome cookie database.\n\n"
                    "This is a known limitation on Windows 10/11.\n"
                    "Chrome encrypts cookies with user credentials.\n\n"
                    "💡 Please use the manual method:\n"
                    "Click 'How to Get Cookies' button for instructions"
                )
            else:
                messagebox.showerror(
                    "Auto-Fetch Failed",
                    f"Failed to fetch cookies:\n\n{error_msg}\n\n"
                    "💡 This feature is unreliable on windows 11.\n"
                    "Please use the manual method instead:\n"
                    "Click 'How to Get Cookies' button for step-by-step guide"
                )
    
    def restart_as_admin(self):
        """Restart the application with administrator privileges"""
        import ctypes
        import sys
        
        try:
            # Get the current script path
            script = os.path.abspath(sys.argv[0])
            
            # Request elevation
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                script,
                None,
                1  # SW_SHOWNORMAL
            )
            
            # Close current instance
            self.root.quit()
            sys.exit(0)
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to restart as administrator:\n\n{str(e)}"
            )
    
    def show_cookie_tutorial(self):
        """Show tutorial window for getting cookies manually"""
        tutorial = tk.Toplevel(self.root)
        tutorial.title("How to Get MangaPark Cookies")
        tutorial.geometry("700x600")
        tutorial.resizable(False, False)
        tutorial.transient(self.root)
        
        # Center the window
        tutorial.update_idletasks()
        x = (tutorial.winfo_screenwidth() // 2) - (700 // 2)
        y = (tutorial.winfo_screenheight() // 2) - (600 // 2)
        tutorial.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(tutorial, bg="#667eea", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🍪 Cookie Tutorial",
            font=("Segoe UI", 18, "bold"),
            bg="#667eea",
            fg="white"
        ).pack(pady=25)
        
        # Content with scrollbar
        content_frame = tk.Frame(tutorial, bg="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Tutorial content
        steps = [
            {
                "title": "Step 1: Open MangaPark in Chrome",
                "text": "• Go to https://mangapark.io\n• Make sure you are logged in to your account"
            },
            {
                "title": "Step 2: Open Developer Tools",
                "text": "• Press F12 on your keyboard\n• OR Right-click anywhere → 'Inspect'\n• OR Menu (⋮) → More Tools → Developer Tools"
            },
            {
                "title": "Step 3: Navigate to Application Tab",
                "text": "• Click on the 'Application' tab at the top\n• (If you don't see it, click the >> arrow to find it)"
            },
            {
                "title": "Step 4: Find Cookies",
                "text": "• In the left sidebar, expand 'Cookies'\n• Click on 'https://mangapark.io'"
            },
            {
                "title": "Step 5: Copy Cookie Values",
                "text": "You need to copy 4 cookies:\n\n"
                      "1. skey - Long JWT token (starts with 'eyJ...')\n"
                      "2. tfv - Numbers (e.g., '1763850143381')\n"
                      "3. theme - Text (e.g., 'coffee' or 'dark')\n"
                      "4. wd - Window dimensions (e.g., '876x932')\n\n"
                      "• Click on each cookie name\n"
                      "• Double-click the 'Value' column\n"
                      "• Press Ctrl+C to copy\n"
                      "• Paste into the corresponding field"
            },
            {
                "title": "⚠️ Important Notes",
                "text": "• Cookies expire after some time - you may need to refresh them\n"
                      "• Keep Chrome logged into MangaPark\n"
                      "• Don't share your cookies with anyone (they give access to your account)"
            }
        ]
        
        for i, step in enumerate(steps):
            # Step frame
            step_frame = tk.Frame(scrollable_frame, bg="white", pady=10)
            step_frame.pack(fill="x", pady=10)
            
            # Title
            title_label = tk.Label(
                step_frame,
                text=step["title"],
                font=("Segoe UI", 11, "bold"),
                bg="white",
                fg="#667eea",
                anchor="w"
            )
            title_label.pack(fill="x", pady=(0, 5))
            
            # Content box
            content_box = tk.Frame(step_frame, bg="#f8f9fa", relief="solid", borderwidth=1)
            content_box.pack(fill="x", padx=20)
            
            text_label = tk.Label(
                content_box,
                text=step["text"],
                font=("Segoe UI", 9),
                bg="#f8f9fa",
                fg="#333",
                anchor="w",
                justify="left",
                padx=15,
                pady=10
            )
            text_label.pack(fill="x")
            
            # Separator (except last)
            if i < len(steps) - 1:
                tk.Frame(scrollable_frame, bg="#e0e0e0", height=1).pack(fill="x", padx=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom button
        bottom_frame = tk.Frame(tutorial, bg="#f0f0f0")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        close_btn = tk.Button(
            bottom_frame,
            text="Got it!",
            font=("Segoe UI", 11, "bold"),
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            cursor="hand2",
            padx=40,
            pady=10,
            command=tutorial.destroy
        )
        close_btn.pack()
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        tutorial.protocol("WM_DELETE_WINDOW", lambda: [canvas.unbind_all("<MouseWheel>"), tutorial.destroy()])
    
    def show_devtools_method(self):
        """Show the easiest method: Using Chrome DevTools Application tab"""
        devtools_window = tk.Toplevel(self.root)
        devtools_window.title("💡 Easiest Method")
        devtools_window.geometry("700x550")
        devtools_window.resizable(False, False)
        devtools_window.transient(self.root)
        
        # Center the window
        devtools_window.update_idletasks()
        x = (devtools_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (devtools_window.winfo_screenheight() // 2) - (550 // 2)
        devtools_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(devtools_window, bg="#10b981", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="💡 Easiest & Most Reliable Method",
            font=("Segoe UI", 18, "bold"),
            bg="#10b981",
            fg="white"
        ).pack(pady=25)
        
        # Content with scrollbar
        content_frame = tk.Frame(devtools_window, bg="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Introduction
        tk.Label(
            scrollable_frame,
            text="⚡ This method works 100% of the time!",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#10b981"
        ).pack(pady=(0, 20))
        
        # Steps
        steps = [
            {
                "title": "1️⃣ Open MangaPark",
                "content": "• Go to https://mangapark.io\n• Log in to your account\n• Navigate to your follows: https://mangapark.io/my/follows",
                "color": "#667eea"
            },
            {
                "title": "2️⃣ Open DevTools",
                "content": "• Press F12 (or Right-click anywhere → Inspect)\n• This opens Chrome Developer Tools",
                "color": "#667eea"
            },
            {
                "title": "3️⃣ Go to Application Tab",
                "content": "• Click 'Application' at the top of DevTools\n• If you don't see it, click the >> arrow to find it",
                "color": "#667eea"
            },
            {
                "title": "4️⃣ Find Cookies",
                "content": "• In the left sidebar, expand 'Cookies'\n• Click on 'https://mangapark.io'",
                "color": "#667eea"
            },
            {
                "title": "5️⃣ Copy Each Cookie",
                "content": "You need to copy 4 cookies:\n\n"
                        "📋 skey - Long token starting with 'eyJ...'\n"
                        "📋 tfv - Numbers like '1763850143381'\n"
                        "📋 theme - Text like 'coffee' or 'dark'\n"
                        "📋 wd - Dimensions like '876x932'\n\n"
                        "For each cookie:\n"
                        "• Find it in the list by Name\n"
                        "• Double-click the Value column\n"
                        "• Press Ctrl+C to copy\n"
                        "• Paste into the corresponding field above",
                "color": "#10b981"
            }
        ]
        
        for step in steps:
            step_frame = tk.Frame(scrollable_frame, bg="white")
            step_frame.pack(fill="x", pady=10)
            
            tk.Label(
                step_frame,
                text=step["title"],
                font=("Segoe UI", 11, "bold"),
                bg="white",
                fg=step["color"],
                anchor="w"
            ).pack(fill="x", pady=(0, 8))
            
            content_box = tk.Frame(step_frame, bg="#f8f9fa", relief="solid", borderwidth=1)
            content_box.pack(fill="x", padx=15)
            
            tk.Label(
                content_box,
                text=step["content"],
                font=("Segoe UI", 9),
                bg="#f8f9fa",
                fg="#333",
                anchor="w",
                justify="left",
                padx=15,
                pady=12
            ).pack(fill="x")
        
        # Important note
        note_frame = tk.Frame(scrollable_frame, bg="#fef3c7", relief="solid", borderwidth=2)
        note_frame.pack(fill="x", pady=20)
        
        tk.Label(
            note_frame,
            text="⚠️ Important Notes",
            font=("Segoe UI", 10, "bold"),
            bg="#fef3c7",
            fg="#92400e"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        tk.Label(
            note_frame,
            text="• Cookies expire after some time - you may need to get them again\n"
                 "• Keep Chrome logged into MangaPark while using this tool\n"
                 "• Never share your cookies (they give access to your account)",
            font=("Segoe UI", 9),
            bg="#fef3c7",
            fg="#92400e",
            anchor="w",
            justify="left",
            padx=15,
            pady=(0, 10)
        ).pack(fill="x")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom button
        bottom_frame = tk.Frame(devtools_window, bg="#f0f0f0")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        close_btn = tk.Button(
            bottom_frame,
            text="Got it!",
            font=("Segoe UI", 11, "bold"),
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            cursor="hand2",
            padx=40,
            pady=10,
            command=devtools_window.destroy
        )
        close_btn.pack()
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        devtools_window.protocol("WM_DELETE_WINDOW", lambda: [canvas.unbind_all("<MouseWheel>"), devtools_window.destroy()])
    
    def show_bookmarklet_method(self):
        """Old console method - kept for reference but not recommended"""
        bookmarklet_window = tk.Toplevel(self.root)
        bookmarklet_window.title("📋 Easy Cookie Method")
        bookmarklet_window.geometry("700x550")
        bookmarklet_window.resizable(False, False)
        bookmarklet_window.transient(self.root)
        
        # Center the window
        bookmarklet_window.update_idletasks()
        x = (bookmarklet_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (bookmarklet_window.winfo_screenheight() // 2) - (550 // 2)
        bookmarklet_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(bookmarklet_window, bg="#10b981", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="✨ Easiest Method - Copy from Browser",
            font=("Segoe UI", 18, "bold"),
            bg="#10b981",
            fg="white"
        ).pack(pady=25)
        
        # Content
        content_frame = tk.Frame(bookmarklet_window, bg="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Instructions
        tk.Label(
            content_frame,
            text="⚡ This is the FASTEST and MOST RELIABLE way!",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#10b981"
        ).pack(pady=(0, 15))
        
        # Step 1
        step1_frame = tk.LabelFrame(
            content_frame,
            text="Step 1: Open MangaPark",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#667eea",
            padx=15,
            pady=10
        )
        step1_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            step1_frame,
            text="• Go to https://mangapark.io in your browser\n• Make sure you are LOGGED IN (check top-right corner)\n• Go to your follows page: https://mangapark.io/my/follows",
            font=("Segoe UI", 9),
            bg="white",
            fg="#333",
            justify="left",
            anchor="w"
        ).pack(fill="x")
        
        # Step 2
        step2_frame = tk.LabelFrame(
            content_frame,
            text="Step 2: Open Console",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#667eea",
            padx=15,
            pady=10
        )
        step2_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            step2_frame,
            text="• Press F12 (or Right-click → Inspect)\n• Click on 'Console' tab",
            font=("Segoe UI", 9),
            bg="white",
            fg="#333",
            justify="left",
            anchor="w"
        ).pack(fill="x")
        
        # Step 3
        step3_frame = tk.LabelFrame(
            content_frame,
            text="Step 3: Copy & Run JavaScript Code",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#667eea",
            padx=15,
            pady=10
        )
        step3_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            step3_frame,
            text="Click the button below to copy the code, then paste it in the console:",
            font=("Segoe UI", 9),
            bg="white",
            fg="#333",
            justify="left",
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        # JavaScript code
        js_code = """(() => {
  console.log('=== ALL COOKIES ON THIS PAGE ===');
  console.log(document.cookie);
  console.log('\\n=== PARSING COOKIES ===');
  const cookies = {};
  document.cookie.split('; ').forEach(c => {
    const [key, val] = c.split('=');
    cookies[key] = val;
    console.log(key + ':', val.substring(0, 50) + (val.length > 50 ? '...' : ''));
  });
  console.log('\\n=== MANGAPARK SPECIFIC COOKIES ===');
  console.log('skey:', cookies.skey || 'NOT FOUND');
  console.log('tfv:', cookies.tfv || 'NOT FOUND');
  console.log('theme:', cookies.theme || 'NOT FOUND');
  console.log('wd:', cookies.wd || 'NOT FOUND');
  console.log('\\n⚠️ If all show NOT FOUND:');
  console.log('1. Make sure you are on mangapark.io (not .org or other)');
  console.log('2. Make sure you are logged in');
  console.log('3. Try refreshing the page (F5) and run this again');
  return cookies;
})()"""
        
        code_frame = tk.Frame(step3_frame, bg="#1e1e1e", relief="solid", borderwidth=1)
        code_frame.pack(fill="x", pady=(0, 10))
        
        code_text = tk.Text(
            code_frame,
            height=8,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            wrap="word",
            padx=10,
            pady=10
        )
        code_text.insert("1.0", js_code)
        code_text.config(state="disabled")
        code_text.pack(fill="x")
        
        copy_btn = tk.Button(
            step3_frame,
            text="📋 Copy Code to Clipboard",
            font=("Segoe UI", 10, "bold"),
            bg="#667eea",
            fg="white",
            activebackground="#5568d3",
            activeforeground="white",
            cursor="hand2",
            padx=20,
            pady=8,
            command=lambda: self.copy_to_clipboard(js_code, "Code copied! Now paste it in the console.")
        )
        copy_btn.pack()
        
        # Step 4
        step4_frame = tk.LabelFrame(
            content_frame,
            text="Step 4: Copy Results",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#667eea",
            padx=15,
            pady=10
        )
        step4_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            step4_frame,
            text="• First, check 'ALL COOKIES' section to see if ANY cookies exist\n• If you see cookies but NOT the specific ones (skey, tfv, etc):\n  → They might be HttpOnly (use manual method instead)\n• Copy each value that appears and paste into the fields above",
            font=("Segoe UI", 9),
            bg="white",
            fg="#333",
            justify="left",
            anchor="w"
        ).pack(fill="x")
        
        # Bottom button
        bottom_frame = tk.Frame(bookmarklet_window, bg="#f0f0f0")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        close_btn = tk.Button(
            bottom_frame,
            text="Got it!",
            font=("Segoe UI", 11, "bold"),
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            cursor="hand2",
            padx=40,
            pady=10,
            command=bookmarklet_window.destroy
        )
        close_btn.pack()
    
    def copy_to_clipboard(self, text, success_message):
        """Copy text to clipboard and show confirmation"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Copied!", success_message)
    
    def install_browser_cookie3(self):
        """Install browser_cookie3 with progress dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Installing Dependency")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (150 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(
            dialog,
            text="Installing browser_cookie3...",
            font=("Segoe UI", 11),
            pady=20
        ).pack()
        
        progress = ttk.Progressbar(
            dialog,
            mode='indeterminate',
            length=300
        )
        progress.pack(pady=10)
        progress.start()
        
        status_label = tk.Label(
            dialog,
            text="Please wait...",
            font=("Segoe UI", 9),
            fg="#666"
        )
        status_label.pack()
        
        def install():
            try:
                import subprocess
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "browser-cookie3"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                dialog.after(0, lambda: status_label.config(text="✓ Installed successfully!", fg="#10b981"))
                dialog.after(1000, dialog.destroy)
                dialog.after(1500, lambda: messagebox.showinfo("Success", "browser_cookie3 installed!\n\nYou can now use Auto-Fetch."))
            except Exception as e:
                dialog.after(0, lambda: status_label.config(text=f"✗ Installation failed: {e}", fg="#ef4444"))
                dialog.after(2000, dialog.destroy)
        
        threading.Thread(target=install, daemon=True).start()
    
    def start_export(self):
        """Start the export process in a separate thread"""
        if self.running:
            messagebox.showwarning("Already Running", "Export is already in progress!")
            return
        
        if not SELENIUM_AVAILABLE:
            messagebox.showerror(
                "Selenium Required",
                "Selenium is not installed!\n\nInstall with: pip install selenium"
            )
            return
        
        # Reset UI
        self.log_text.delete(1.0, "end")
        self.progress_var.set(0)
        for i in range(4):
            self.update_step(i, 'pending')
        self.update_stats()
        
        self.start_button.config(state="disabled", text="⏳ Running...", bg="#6b7280")
        self.open_html_button.config(state="disabled")
        self.open_folder_button.config(state="disabled")
        
        self.running = True
        
        # Start export in background thread
        thread = threading.Thread(target=self.export_worker, daemon=True)
        thread.start()
    
    def export_worker(self):
        """Worker thread for export process"""
        try:
            # Get configuration
            mode = self.scraping_mode.get()
            
            if mode == "authenticated":
                cookies = {
                    "skey": self.skey_entry.get().strip(),
                    "tfv": self.tfv_entry.get().strip(),
                    "theme": self.theme_entry.get().strip(),
                    "wd": self.wd_entry.get().strip()
                }
            else:
                cookies = None  # Public scraping mode
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Step 1: Scrape
            self.update_step(0, 'running')
            self.log("="*60, "#667eea")
            self.log("STEP 1/4: Scraping MangaPark Follows", "#667eea")
            self.log("="*60, "#667eea")
            self.log("⏳ Initializing browser and loading page...", "#667eea")
            self.log("⏳ This process can take up to a few minutes, please be patient.", "#667eea")
            self.manga_list = self.scrape_mangapark(cookies)
            
            if not self.manga_list:
                raise Exception("No manga found! Check your cookies.")
            
            self.update_step(0, 'done')
            self.progress_var.set(25)
            
            # Step 2: Enrich
            self.update_step(1, 'running')
            self.log("\n" + "="*60, "#667eea")
            self.log("STEP 2/4: Finding MAL IDs", "#667eea")
            self.log("="*60, "#667eea")
            self.enriched_list = self.enrich_with_mal_ids(self.manga_list)
            self.update_step(1, 'done')
            self.progress_var.set(50)
            
            # Step 3: Generate XML
            self.update_step(2, 'running')
            self.log("\n" + "="*60, "#667eea")
            self.log("STEP 3/4: Generating MAL XML", "#667eea")
            self.log("="*60, "#667eea")
            xml_path = os.path.join(self.output_dir, "mangapark_to_mal.xml")
            self.generate_mal_xml(self.enriched_list, xml_path)
            self.update_step(2, 'done')
            self.progress_var.set(75)
            
            # Step 4: Generate HTML
            self.update_step(3, 'running')
            self.log("\n" + "="*60, "#667eea")
            self.log("STEP 4/4: Generating HTML Page", "#667eea")
            self.log("="*60, "#667eea")
            html_path = os.path.join(self.output_dir, "manga_list.html")
            self.generate_html(self.enriched_list, html_path)
            self.update_step(3, 'done')
            self.progress_var.set(100)
            
            # Success
            self.log("\n" + "="*60, "#10b981")
            self.log("✓ EXPORT COMPLETE!", "#10b981")
            self.log("="*60, "#10b981")
            self.log(f"Files saved in: {os.path.abspath(self.output_dir)}", "#10b981")
            
            self.root.after(0, self.on_export_complete)
            
        except Exception as e:
            self.log(f"\n❌ ERROR: {str(e)}", "#ef4444")
            for i in range(4):
                if self.step_icons[i].cget("text") == "⚙️":
                    self.update_step(i, 'error')
            self.root.after(0, self.on_export_error, str(e))
        finally:
            self.running = False
    
    def scrape_mangapark(self, cookies):
        """Scrape MangaPark follows"""
        self.log("[DEBUG] Starting scrape_mangapark with cookies: True" if cookies else "[DEBUG] Starting scrape_mangapark with cookies: False")
        print(f"[DEBUG] Starting scrape_mangapark with cookies: {cookies is not None}")
        
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
        
        self.log("[DEBUG] Creating Chrome WebDriver...")
        print("[DEBUG] Creating Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            if cookies:
                self.log("[DEBUG] Authenticated mode - using cookies")
                print("[DEBUG] Authenticated mode - using cookies")
                # Authenticated mode - scrape /my/follows
                driver.get("https://mangapark.io/my/follows")
                self.log("[DEBUG] Navigated to mangapark.io/my/follows")
                print("[DEBUG] Navigated to mangapark.io/my/follows")
                
                for name, value in cookies.items():
                    if value:
                        self.log(f"[DEBUG] Adding cookie: {name} = {value[:20]}...")
                        print(f"[DEBUG] Adding cookie: {name} = {value[:20]}...")
                        driver.add_cookie({
                            "name": name,
                            "value": value,
                            "domain": ".mangapark.io"
                        })
                
                self.log("[DEBUG] Refreshing page with cookies...")
                print("[DEBUG] Refreshing page with cookies...")
                driver.refresh()
                time.sleep(2)
                
                results = []
                seen = set()
                page = 1
                
                while True:
                    self.log(f"  Scraping page {page}...")
                    self.progress_label.config(text=f"Scraping page {page} - Please wait, this is not stuck...")
                    self.log(f"[DEBUG] Scraping page {page}...")
                    print(f"[DEBUG] Scraping page {page}...")
                    
                    url = f"https://mangapark.io/my/follows?page={page}"
                    driver.get(url)
                    self.log(f"[DEBUG] Loaded URL: {url}")
                    print(f"[DEBUG] Loaded URL: {url}")
                    
                    try:
                        # Attente dynamique : spinner ou manga cards
                        self.log("  ⏳ Waiting for page to load (max 30s)...", "#667eea")
                        self.log("[DEBUG] Waiting for page to fully load (max 30s)...")
                        print("[DEBUG] Waiting for page to fully load (max 30s)...")
                        try:
                            WebDriverWait(driver, 30).until(
                                lambda d: d.find_elements(By.CSS_SELECTOR, "a[href*='/title/']") or not d.find_elements(By.CLASS_NAME, "loading-spinner")
                            )
                        except Exception as e:
                            self.log(f"[DEBUG] Timeout or error during wait: {e}")
                            print(f"[DEBUG] Timeout or error during wait: {e}")
                        
                        self.log("[DEBUG] Checking for loading spinner...")
                        print("[DEBUG] Checking for loading spinner...")
                        # Try to wait for spinner to disappear (but don't fail if it's already gone)
                        spinner_gone = False
                        try:
                            WebDriverWait(driver, 5).until_not(
                                EC.presence_of_element_located((By.CLASS_NAME, "loading-spinner"))
                            )
                            self.log("[DEBUG] Spinner disappeared")
                            print("[DEBUG] Spinner disappeared")
                            spinner_gone = True
                        except:
                            self.log("[DEBUG] No spinner found or already gone")
                            print("[DEBUG] No spinner found or already gone")
                            spinner_gone = True
                        
                        # Additional wait after spinner (only if spinner was there)
                        if spinner_gone:
                            self.log("  ⏳ Waiting for content to render (5 seconds)...", "#667eea")
                            self.log("[DEBUG] Waiting additional 5 seconds for content to render...")
                            print("[DEBUG] Waiting additional 5 seconds for content to render...")
                            time.sleep(5)
                        
                        self.log("[DEBUG] Looking for manga cards...")
                        print("[DEBUG] Looking for manga cards...")
                        # Check if manga cards appeared
                        soup_check = BeautifulSoup(driver.page_source, "html.parser")
                        links_check = soup_check.select("a[href*='/title/']")
                        self.log(f"[DEBUG] Found {len(links_check)} potential manga links after waiting")
                        print(f"[DEBUG] Found {len(links_check)} potential manga links after waiting")
                        
                        if len(links_check) == 0:
                            self.log("  ⏳ Content still loading, waiting up to 30s for manga cards...", "#667eea")
                            self.log("[DEBUG] Still no manga cards found, waiting up to 30s...")
                            print("[DEBUG] Still no manga cards found, waiting up to 30s...")
                            try:
                                WebDriverWait(driver, 30).until(
                                    lambda d: d.find_elements(By.CSS_SELECTOR, "a[href*='/title/']")
                                )
                            except Exception as e:
                                self.log(f"[DEBUG] Timeout or error during wait for manga cards: {e}")
                                print(f"[DEBUG] Timeout or error during wait for manga cards: {e}")
                    except Exception as e:
                        self.log(f"[DEBUG] Exception during wait: {e}")
                        print(f"[DEBUG] Exception during wait: {e}")
                        self.log("  ⏳ Finalizing page load (15 seconds)...", "#667eea")
                        self.log("[DEBUG] Continuing anyway...")
                        print("[DEBUG] Continuing anyway...")
                        time.sleep(15)
                    
                    # Save page source for debugging
                    if page == 1:
                        page_source = driver.page_source
                        self.log(f"[DEBUG] Page source length: {len(page_source)}")
                        print(f"[DEBUG] Page source length: {len(page_source)}")
                        with open("debug_scrape_page1.html", "w", encoding="utf-8") as f:
                            f.write(page_source)
                        self.log("[DEBUG] Saved page source to debug_scrape_page1.html")
                        print("[DEBUG] Saved page source to debug_scrape_page1.html")
                    
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    links = soup.select("a[href*='/title/']")
                    self.log(f"[DEBUG] Found {len(links)} links with '/title/'")
                    print(f"[DEBUG] Found {len(links)} links with '/title/'")
                    
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
                            if count <= 5:  # Show first 5 for debugging
                                print(f"[DEBUG] Found manga: {title}")
                    
                    self.log(f"  Found {count} titles on page {page}")
                    self.log(f"[DEBUG] Total unique manga so far: {len(results)}")
                    print(f"[DEBUG] Total unique manga so far: {len(results)}")
                    
                    if count == 0 or page > 100:
                        self.log(f"[DEBUG] Stopping: count={count}, page={page}")
                        print(f"[DEBUG] Stopping: count={count}, page={page}")
                        break
                    
                    page += 1
            else:
                print("[DEBUG] Public mode - scraping latest")
                # Public mode - scrape trending/popular manga
                self.log("  Scraping public manga list (trending/popular)...")
                self.progress_label.config(text="Scraping public manga...")
                
                driver.get("https://mangapark.io/latest")
                print("[DEBUG] Loaded latest page")
                time.sleep(3)
                
                results = []
                seen = set()
                
                # Scroll to load more content
                for i in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print(f"[DEBUG] Scroll {i+1}/5")
                    time.sleep(2)
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                links = soup.select("a[href*='/title/']")
                print(f"[DEBUG] Found {len(links)} links")
                
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
                
                self.log(f"  Found {len(results)} manga")
                print(f"[DEBUG] Total public manga: {len(results)}")
            
            self.log(f"\n✓ Total manga found: {len(results)}", "#10b981")
            self.log(f"[DEBUG] Scraping complete: {len(results)} manga")
            print(f"[DEBUG] Scraping complete: {len(results)} manga")
            return results
            
        except Exception as e:
            self.log(f"[DEBUG] Exception in scrape_mangapark: {e}", "#ef4444")
            print(f"[ERROR] Exception in scrape_mangapark: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.log("[DEBUG] Closing WebDriver")
            print("[DEBUG] Closing WebDriver")
            driver.quit()
    
    def enrich_with_mal_ids(self, manga_list):
        """Enrich with MAL IDs"""
        total = len(manga_list)
        found_count = 0
        enriched = []
        
        self.log(f"  Processing {total} manga (1 req/sec)...")
        
        for idx, manga in enumerate(manga_list, 1):
            title = manga["title"]
            
            # Skip chapter titles
            if title.lower().startswith(("chapter", "ch.", "vol.")):
                self.log(f"  [{idx}/{total}] ⏭️  Skipping: {title[:50]}")
                enriched.append({**manga, "mal_id": "0", "confidence": 0})
                continue
            
            self.progress_label.config(text=f"Finding MAL IDs: {idx}/{total}")
            self.log(f"  [{idx}/{total}] 🔍 {title[:50]}{'...' if len(title) > 50 else ''}")
            
            mal_id, mal_title, score = self.search_mal_id(title)
            
            if mal_id:
                found_count += 1
                conf = "High" if score >= 0.9 else "Med" if score >= 0.7 else "Low"
                self.log(f"            ✓ MAL ID {mal_id} ({conf}: {score:.0%})", "#10b981")
                enriched.append({**manga, "mal_id": str(mal_id), "mal_title": mal_title, "confidence": score})
            else:
                self.log(f"            ✗ Not found", "#ef4444")
                enriched.append({**manga, "mal_id": "0", "confidence": 0})
            
            # Update stats in real-time
            self.update_stats(idx, found_count, idx - found_count)
            
            time.sleep(1)
        
        self.log(f"\n✓ Found {found_count}/{total} ({found_count/total*100:.1f}%)", "#10b981")
        return enriched
    
    def search_mal_id(self, title):
        """Search MAL via Jikan API"""
        try:
            url = "https://api.jikan.moe/v4/manga"
            params = {"q": title, "limit": 5}
            
            resp = requests.get(url, params=params, timeout=10)
            
            if resp.status_code == 429:
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
                
                score = max(
                    SequenceMatcher(None, title.lower(), mal_title.lower()).ratio(),
                    SequenceMatcher(None, title.lower(), mal_title_english.lower()).ratio() if mal_title_english else 0
                )
                
                if score > best_score:
                    best_score = score
                    best_match = (mal_id, mal_title, score)
            
            if best_match and best_score > 0.6:
                return best_match
            
            return None, None, 0
            
        except:
            return None, None, 0
    
    def generate_mal_xml(self, manga_list, output_path):
        """Generate MAL XML"""
        root = ET.Element("myanimelist")
        
        myinfo = ET.SubElement(root, "myinfo")
        ET.SubElement(myinfo, "user_name").text = "mangapark_export"
        ET.SubElement(myinfo, "user_export_type").text = "2"
        ET.SubElement(myinfo, "user_total_manga").text = str(len(manga_list))
        
        for m in manga_list:
            entry = ET.SubElement(root, "manga")
            ET.SubElement(entry, "manga_mangadb_id").text = m["mal_id"]
            ET.SubElement(entry, "manga_title").text = m["title"]
            ET.SubElement(entry, "my_status").text = "Plan to Read"
            ET.SubElement(entry, "manga_mangapark_url").text = m["url"]
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        self.log(f"✓ XML saved: {output_path}", "#10b981")
    
    def generate_html(self, manga_list, output_path):
        """Generate HTML page"""
        manga_list.sort(key=lambda x: (x["mal_id"] == "0", x["title"].lower()))
        
        found = sum(1 for m in manga_list if m["mal_id"] != "0")
        
        html = f"""<!DOCTYPE html>
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
.controls {{padding:20px 40px;background:#f8f9fa;display:flex;gap:15px;flex-wrap:wrap}}
.search-box {{flex:1;min-width:250px}}
.search-box input {{width:100%;padding:12px 20px;border:2px solid #e9ecef;border-radius:8px;font-size:1rem}}
.search-box input:focus {{outline:none;border-color:#667eea}}
.filter-btn {{padding:10px 20px;border:2px solid #e9ecef;background:white;border-radius:8px;cursor:pointer}}
.filter-btn:hover {{border-color:#667eea;color:#667eea}}
.filter-btn.active {{background:#667eea;color:white;border-color:#667eea}}
.manga-list {{padding:40px;max-height:800px;overflow-y:auto}}
.manga-item {{display:flex;align-items:center;padding:20px;border-bottom:1px solid #e9ecef}}
.manga-item:hover {{background:#f8f9fa}}
.manga-status {{width:12px;height:12px;border-radius:50%;margin-right:20px;flex-shrink:0}}
.status-found {{background:#10b981;box-shadow:0 0 10px rgba(16,185,129,0.5)}}
.status-not-found {{background:#ef4444;box-shadow:0 0 10px rgba(239,68,68,0.5)}}
.manga-content {{flex:1}}
.manga-title {{font-size:1.1rem;font-weight:500;margin-bottom:5px}}
.manga-info {{font-size:0.85rem;color:#6b7280}}
.manga-links {{display:flex;gap:10px}}
.manga-link {{padding:8px 16px;border-radius:6px;text-decoration:none;font-size:0.85rem;font-weight:500}}
.mal-link {{background:#2e51a2;color:white}}
.mal-link:hover {{background:#1e3a8a}}
.mangapark-link {{background:#667eea;color:white}}
.mangapark-link:hover {{background:#5568d3}}
.mal-link.disabled {{background:#d1d5db;color:#9ca3af;pointer-events:none}}
.badge {{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-left:8px}}
.badge-high {{background:#d1fae5;color:#065f46}}
.badge-med {{background:#fef3c7;color:#92400e}}
.badge-low {{background:#fee2e2;color:#991b1b}}
</style></head><body>
<div class="container">
<header><h1>📚 MangaPark Export</h1>
<div class="stats">
<div class="stat"><div class="stat-value">{len(manga_list)}</div><div class="stat-label">Total</div></div>
<div class="stat"><div class="stat-value">{found}</div><div class="stat-label">Found</div></div>
<div class="stat"><div class="stat-value">{len(manga_list)-found}</div><div class="stat-label">Not Found</div></div>
<div class="stat"><div class="stat-value">{found/len(manga_list)*100:.1f}%</div><div class="stat-label">Success</div></div>
</div></header>
<div class="controls">
<div class="search-box"><input type="text" id="search" placeholder="🔍 Search..."></div>
<button class="filter-btn active" data-filter="all">All</button>
<button class="filter-btn" data-filter="found">✓ Found</button>
<button class="filter-btn" data-filter="not-found">✗ Not Found</button>
</div>
<div class="manga-list" id="list">"""
        
        for m in manga_list:
            has_id = m["mal_id"] != "0"
            status_class = "status-found" if has_id else "status-not-found"
            
            if has_id:
                conf = m.get("confidence", 0)
                badge_class = "badge-high" if conf >= 0.9 else "badge-med" if conf >= 0.7 else "badge-low"
                badge_text = "High" if conf >= 0.9 else "Med" if conf >= 0.7 else "Low"
                info = f'MAL ID: {m["mal_id"]}<span class="badge {badge_class}">{badge_text}</span>'
                mal_url = f'https://myanimelist.net/manga/{m["mal_id"]}'
                disabled = ""
            else:
                info = "Not found on MAL"
                mal_url = "#"
                disabled = "disabled"
            
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
</div></div>'''
        
        html += """</div></div>
<script>
const search=document.getElementById('search');
const items=document.querySelectorAll('.manga-item');
const btns=document.querySelectorAll('.filter-btn');
let filter='all';
function update(){
let v=search.value.toLowerCase();
items.forEach(i=>{
let t=i.querySelector('.manga-title').textContent.toLowerCase();
let s=i.dataset.status;
i.style.display=(t.includes(v)&&(filter==='all'||s===filter))?'flex':'none';
});
}
search.addEventListener('input',update);
btns.forEach(b=>b.addEventListener('click',()=>{
btns.forEach(x=>x.classList.remove('active'));
b.classList.add('active');
filter=b.dataset.filter;
update();
}));
</script></body></html>"""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        self.log(f"✓ HTML saved: {output_path}", "#10b981")
    
    def on_export_complete(self):
        """Called when export completes successfully"""
        self.start_button.config(state="normal", text="▶️ Start Export", bg="#10b981")
        self.open_html_button.config(state="normal")
        self.open_folder_button.config(state="normal")
        self.progress_label.config(text="Export complete!")
        
        messagebox.showinfo(
            "Success!",
            f"Export completed successfully!\n\n"
            f"Total: {len(self.enriched_list)}\n"
            f"Found on MAL: {sum(1 for m in self.enriched_list if m['mal_id'] != '0')}\n\n"
            f"Files saved in: {os.path.abspath(self.output_dir)}"
        )
    
    def on_export_error(self, error_msg):
        """Called when export fails"""
        self.start_button.config(state="normal", text="▶️ Start Export", bg="#10b981")
        self.progress_label.config(text="Export failed!")
        
        messagebox.showerror("Error", f"Export failed:\n\n{error_msg}")
    
    def open_html(self):
        """Open generated HTML in browser"""
        html_path = os.path.join(self.output_dir, "manga_list.html")
        if os.path.exists(html_path):
            webbrowser.open(f"file://{os.path.abspath(html_path)}")
        else:
            messagebox.showwarning("Not Found", "HTML file not found!")
    
    def open_folder(self):
        """Open output folder"""
        if os.path.exists(self.output_dir):
            os.startfile(os.path.abspath(self.output_dir))
        else:
            messagebox.showwarning("Not Found", "Output folder not found!")


def main():
    root = tk.Tk()
    app = MangaParkExporterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
