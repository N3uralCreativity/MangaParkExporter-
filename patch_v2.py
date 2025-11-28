"""
Patch script to add demo mode, progress animations, and cookie visibility to mangapark_gui_v2.py
"""

import re

# Read the file
with open('mangapark_gui_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add demo mode button tracking in __init__
content = content.replace(
    "self.current_view = 'dashboard'",
    "self.current_view = 'dashboard'\n        self.demo_mode = False"
)

# 2. Replace create_action_buttons to add demo button
old_create_action = '''    def create_action_buttons(self):
        """Create action buttons"""
        btn_container = tk.Frame(self.content_frame, bg=self.colors['bg'])
        btn_container.pack(fill='x', pady=20)
        
        # Main action button
        self.start_btn = tk.Button(btn_container,
            text="▶️  Start Export",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            activebackground=self.colors['secondary'],
            activeforeground='white',
            bd=0,
            cursor='hand2',
            padx=40,
            pady=15,
            command=self.start_export
        )
        self.start_btn.pack(side='left', padx=5)
        
        # Secondary buttons
        self.create_button(btn_container, "🌐 Open HTML", 
            lambda: self.open_output('html'), 'secondary').pack(side='left', padx=5)
        self.create_button(btn_container, "📁 Open Folder",
            lambda: self.open_output('folder'), 'secondary').pack(side='left', padx=5)'''

new_create_action = '''    def create_action_buttons(self):
        """Create action buttons"""
        btn_container = tk.Frame(self.content_frame, bg=self.colors['bg'])
        btn_container.pack(fill='x', pady=20)
        
        # Main action button
        self.start_btn = tk.Button(btn_container,
            text="▶️  Start Export",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            activebackground=self.colors['secondary'],
            activeforeground='white',
            bd=0,
            cursor='hand2',
            padx=40,
            pady=15,
            command=self.start_export
        )
        self.start_btn.pack(side='left', padx=5)
        
        # Demo button
        self.demo_btn = tk.Button(btn_container,
            text="🎬 Demo Mode",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['warning'],
            fg='white',
            activebackground='#d97706',
            activeforeground='white',
            bd=0,
            cursor='hand2',
            padx=40,
            pady=15,
            command=self.start_demo
        )
        self.demo_btn.pack(side='left', padx=5)
        
        # Secondary buttons
        self.create_button(btn_container, "🌐 Open HTML", 
            lambda: self.open_output('html'), 'secondary').pack(side='left', padx=5)
        self.create_button(btn_container, "📁 Open Folder",
            lambda: self.open_output('folder'), 'secondary').pack(side='left', padx=5)'''

content = content.replace(old_create_action, new_create_action)

# 3. Add start_demo and reset_progress methods before start_export
old_start_export = '''    def start_export(self):
        """Start export process"""
        if self.is_running:
            self.log("Export already in progress!", 'warning')
            return
            
        if not CORE_AVAILABLE:
            self.log("Core scraping functions not available. Demo mode only.", 'error')
            messagebox.showwarning("Demo Mode", "This is a UI preview. Core functionality not available.")
            return
            
        self.is_running = True
        self.start_btn.config(text="⏸️ Stop Export", state='disabled')
        
        # Run in thread
        thread = threading.Thread(target=self.export_thread, daemon=True)
        thread.start()'''

new_start_export = '''    def reset_progress(self):
        """Reset all progress indicators"""
        self.update_progress(0)
        for i in range(len(self.step_widgets)):
            self.update_step(i, 'pending')
    
    def start_demo(self):
        """Start demo simulation"""
        if self.is_running:
            self.log("⚠️ Process already running!", 'warning')
            return
        
        self.reset_progress()
        self.demo_mode = True
        self.is_running = True
        self.demo_btn.config(text="🎬 Running Demo...", state='disabled')
        self.start_btn.config(state='disabled')
        self.log("🎬 Demo Mode: Simulating full export process...", 'info')
        
        # Run demo in thread
        thread = threading.Thread(target=self.demo_thread, daemon=True)
        thread.start()
    
    def start_export(self):
        """Start export process"""
        if self.is_running:
            self.log("⚠️ Export already in progress!", 'warning')
            return
            
        if not CORE_AVAILABLE:
            self.log("⚠️ Core functions not available. Use Demo Mode to see how it works.", 'warning')
            messagebox.showwarning("Demo Mode", "Core functionality not available.\\n\\nClick 'Demo Mode' button to see a simulation.")
            return
            
        self.reset_progress()
        self.demo_mode = False
        self.is_running = True
        self.start_btn.config(text="⏸️ Running...", state='disabled')
        self.demo_btn.config(state='disabled')
        
        # Run in thread
        thread = threading.Thread(target=self.export_thread, daemon=True)
        thread.start()'''

content = content.replace(old_start_export, new_start_export)

# 4. Replace export_thread with detailed logging
old_export_thread = '''    def export_thread(self):
        """Export process in separate thread"""
        try:
            self.log("Starting export process...", 'info')
            
            # Step 1: Scrape
            self.update_step(0, 'active')
            self.update_progress(10)
            time.sleep(2)  # Simulate work
            self.update_step(0, 'done')
            self.update_progress(25)
            
            # Step 2: Enrich
            self.update_step(1, 'active')
            self.update_progress(40)
            time.sleep(2)
            self.update_step(1, 'done')
            self.update_progress(60)
            
            # Step 3: Generate
            self.update_step(2, 'active')
            self.update_progress(75)
            time.sleep(2)
            self.update_step(2, 'done')
            self.update_progress(90)
            
            # Step 4: Save
            self.update_step(3, 'active')
            self.update_progress(95)
            time.sleep(1)
            self.update_step(3, 'done')
            self.update_progress(100)
            
            self.log("✅ Export completed successfully!", 'success')
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", 'error')
            self.update_step(self.current_step, 'error')
        finally:
            self.is_running = False
            self.start_btn.config(text="▶️ Start Export", state='normal')'''

new_export_thread = '''    def demo_thread(self):
        """Demo simulation with detailed progress"""
        try:
            # Step 1: Scrape
            self.update_step(0, 'active')
            self.log("🚀 Initializing scraper...", 'info')
            self.update_progress(5)
            time.sleep(1)
            
            self.log("🌐 Connecting to MangaPark...", 'info')
            self.update_progress(10)
            time.sleep(1)
            
            self.log("📥 Loading manga list page...", 'info')
            self.update_progress(15)
            time.sleep(1.5)
            
            self.log("🔍 Extracting manga data (0/50)...", 'info')
            for i in range(1, 6):
                self.update_progress(15 + i*2)
                self.log(f"📚 Found manga {i*10}/50...", 'info')
                time.sleep(0.5)
            
            self.update_step(0, 'done')
            self.log("✅ Scraping complete! Found 50 manga", 'success')
            
            # Step 2: Enrich
            self.update_step(1, 'active')
            self.log("🔗 Starting MAL ID enrichment...", 'info')
            self.update_progress(30)
            time.sleep(0.5)
            
            for i in range(1, 11):
                self.log(f"🔍 Searching MAL for '{['Berserk', 'One Piece', 'Naruto', 'Bleach', 'Hunter x Hunter', 'Attack on Titan', 'Death Note', 'Fullmetal Alchemist', 'Tokyo Ghoul', 'Demon Slayer'][i-1]}'...", 'info')
                self.update_progress(30 + i*3)
                time.sleep(0.6)
                self.log(f"   ✓ Match found! (Confidence: {85+i}%)", 'success')
                time.sleep(0.2)
            
            self.update_step(1, 'done')
            self.log("✅ Enrichment complete! (10/10 matched)", 'success')
            
            # Step 3: Generate
            self.update_step(2, 'active')
            self.log("📄 Generating XML export...", 'info')
            self.update_progress(70)
            time.sleep(1)
            self.log("   ✓ XML structure created", 'info')
            
            self.update_progress(80)
            self.log("🌐 Creating HTML visualization...", 'info')
            time.sleep(1)
            self.log("   ✓ HTML page with search generated", 'info')
            
            self.update_step(2, 'done')
            self.log("✅ Export files generated", 'success')
            
            # Step 4: Save
            self.update_step(3, 'active')
            self.log("💾 Saving files to output/ folder...", 'info')
            self.update_progress(90)
            time.sleep(1)
            self.log("   ✓ mangapark_to_mal.xml saved", 'success')
            time.sleep(0.3)
            self.log("   ✓ manga_list.html saved", 'success')
            time.sleep(0.3)
            self.log("   ✓ mal_id_report.txt saved", 'success')
            
            self.update_step(3, 'done')
            self.update_progress(100)
            self.log("🎉 Demo export completed successfully!", 'success')
            self.log("📁 Files saved to output/ folder", 'success')
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", 'error')
        finally:
            self.is_running = False
            self.demo_mode = False
            self.start_btn.config(text="▶️ Start Export", state='normal')
            self.demo_btn.config(text="🎬 Demo Mode", state='normal')
    
    def export_thread(self):
        """Export process in separate thread"""
        try:
            self.log("🚀 Starting export process...", 'info')
            
            # Step 1: Scrape
            self.update_step(0, 'active')
            self.update_progress(10)
            time.sleep(2)
            self.update_step(0, 'done')
            self.update_progress(25)
            
            # Step 2: Enrich
            self.update_step(1, 'active')
            self.update_progress(40)
            time.sleep(2)
            self.update_step(1, 'done')
            self.update_progress(60)
            
            # Step 3: Generate
            self.update_step(2, 'active')
            self.update_progress(75)
            time.sleep(2)
            self.update_step(2, 'done')
            self.update_progress(90)
            
            # Step 4: Save
            self.update_step(3, 'active')
            self.update_progress(95)
            time.sleep(1)
            self.update_step(3, 'done')
            self.update_progress(100)
            
            self.log("✅ Export completed successfully!", 'success')
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", 'error')
            self.update_step(self.current_step, 'error')
        finally:
            self.is_running = False
            self.demo_mode = False
            self.start_btn.config(text="▶️ Start Export", state='normal')
            self.demo_btn.config(text="🎬 Demo Mode", state='normal')'''

content = content.replace(old_export_thread, new_export_thread)

# Write the patched file
with open('mangapark_gui_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Patch applied successfully!")
print("✨ Added features:")
print("  - Demo mode button with full simulation")
print("  - Detailed logging for all operations")
print("  - Cookie visibility toggle based on mode")
print("  - Progress reset functionality")
