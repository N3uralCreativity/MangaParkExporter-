"""
Dependency checker and installer for MangaPark Exporter
Displays a setup GUI if dependencies are missing
"""
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
import threading

REQUIRED_PACKAGES = {
    'requests': 'requests>=2.31.0',
    'bs4': 'beautifulsoup4>=4.12.0',
    'selenium': 'selenium>=4.15.0',
    'browser_cookie3': 'browser-cookie3>=0.19.0'
}

class DependencyInstallerGUI:
    def __init__(self, root, missing_packages):
        self.root = root
        self.root.title("MangaPark Exporter - Setup")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        self.missing_packages = missing_packages
        self.installing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#667eea", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="⚙️ Setup Required",
            font=("Segoe UI", 20, "bold"),
            bg="#667eea",
            fg="white"
        ).pack(pady=20)
        
        # Main content
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Message
        message = tk.Label(
            main_frame,
            text=f"Missing {len(self.missing_packages)} required package(s):",
            font=("Segoe UI", 11),
            bg="#f0f0f0",
            fg="#333"
        )
        message.pack(pady=(0, 10))
        
        # Package list
        list_frame = tk.Frame(main_frame, bg="white", relief="solid", borderwidth=1)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        for pkg in self.missing_packages:
            tk.Label(
                list_frame,
                text=f"  • {pkg}",
                font=("Segoe UI", 10),
                bg="white",
                fg="#666",
                anchor="w"
            ).pack(fill="x", padx=10, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=500
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Click Install to continue",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#666"
        )
        self.status_label.pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill="x")
        
        self.install_button = tk.Button(
            button_frame,
            text="Install Dependencies",
            font=("Segoe UI", 11, "bold"),
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.start_installation
        )
        self.install_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            font=("Segoe UI", 11, "bold"),
            bg="#6b7280",
            fg="white",
            activebackground="#4b5563",
            activeforeground="white",
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.cancel
        )
        self.cancel_button.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
    def start_installation(self):
        if self.installing:
            return
        
        self.installing = True
        self.install_button.config(state="disabled", text="Installing...", bg="#6b7280")
        self.cancel_button.config(state="disabled")
        
        # Start installation in background thread
        thread = threading.Thread(target=self.install_packages, daemon=True)
        thread.start()
        
    def install_packages(self):
        total = len(self.missing_packages)
        
        for idx, pkg_name in enumerate(self.missing_packages, 1):
            pkg_spec = REQUIRED_PACKAGES[pkg_name]
            
            # Update progress before installation
            progress_before = ((idx - 1) / total) * 100
            self.root.after(0, self.progress_var.set, progress_before)
            self.root.after(0, self.update_status, f"Installing {pkg_name}... ({idx}/{total})")
            
            try:
                # Run pip install
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", pkg_spec],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for completion
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, process.args)
                
                # Update progress after installation
                progress_after = (idx / total) * 100
                self.root.after(0, self.progress_var.set, progress_after)
                
            except subprocess.CalledProcessError:
                self.root.after(0, self.installation_failed, pkg_name)
                return
        
        self.root.after(0, self.installation_complete)
        
    def update_status(self, message):
        self.status_label.config(text=message)
        
    def installation_complete(self):
        self.status_label.config(text="✓ Installation complete!", fg="#10b981")
        self.install_button.config(
            state="normal",
            text="✓ Close and Restart Manually",
            bg="#10b981",
            command=self.close_and_restart
        )
        
    def close_and_restart(self):
        """Close the installer and let user restart the app"""
        self.root.destroy()
        # Don't exit, just close the installer window
        
    def installation_failed(self, pkg_name):
        self.status_label.config(text=f"✗ Failed to install {pkg_name}", fg="#ef4444")
        self.install_button.config(state="normal", text="Retry", bg="#ef4444")
        self.cancel_button.config(state="normal")
        self.installing = False
        
    def cancel(self):
        self.root.quit()
        sys.exit(0)
        
    def close(self):
        self.root.quit()

def check_dependencies():
    """Check which dependencies are missing"""
    missing = []
    
    for pkg_name in REQUIRED_PACKAGES.keys():
        # Skip browser_cookie3 - it's optional and causes issues in .exe
        if pkg_name == 'browser_cookie3':
            continue
            
        try:
            __import__(pkg_name)
        except ImportError:
            missing.append(pkg_name)
    
    return missing

def install_dependencies_gui(missing_packages):
    """Show GUI to install missing dependencies"""
    root = tk.Tk()
    app = DependencyInstallerGUI(root, missing_packages)
    root.mainloop()
    root.destroy()
    
    # Re-check after installation
    still_missing = check_dependencies()
    
    if len(still_missing) == 0:
        # Show success message and close
        return True
    
    return False

def ensure_dependencies():
    """Ensure all dependencies are installed, show GUI if not"""
    missing = check_dependencies()
    
    if missing:
        success = install_dependencies_gui(missing)
        if success:
            # Dependencies installed, need to restart
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showinfo(
                "Setup Complete",
                "Dependencies installed successfully!\n\n"
                "Please restart the application to continue."
            )
            root.destroy()
            return False  # Signal to exit and restart
        else:
            # Installation failed or cancelled
            return False
    
    return True  # All dependencies present
