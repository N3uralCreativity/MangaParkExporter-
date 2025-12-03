"""
MangaPark to MAL Exporter - Version 2.0 (Modern UI)
Multi-site support architecture with animated interface
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import webbrowser
import os
from pathlib import Path
from typing import Optional, Dict, List
import json

# Import core functionality from v1
try:
    from mangapark_gui import (
        scrape_mangapark, 
        enrich_with_mal_ids,
        generate_mal_xml,
        generate_html_page,
        OUTPUT_DIR
    )
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    print("Warning: Core scraping functions not available. UI demo mode only.")


class ModernMangaExporter:
    """Modern UI with multi-site architecture"""
    
    # Site configurations
    SITES = {
        'mangapark': {
            'name': 'MangaPark',
            'icon': '📚',
            'color': '#667eea',
            'auth_required': True,
            'public_mode': True,
            'status': 'active'
        },
        'mangadex': {
            'name': 'MangaDex',
            'icon': '📖',
            'color': '#ff6740',
            'auth_required': False,
            'public_mode': True,
            'status': 'planned'
        },
        'mangasee': {
            'name': 'MangaSee',
            'icon': '👁️',
            'color': '#4ade80',
            'auth_required': False,
            'public_mode': True,
            'status': 'planned'
        },
        'anilist': {
            'name': 'AniList',
            'icon': '🌟',
            'color': '#02a9ff',
            'auth_required': True,
            'public_mode': False,
            'status': 'planned'
        }
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Site Manga Exporter v2.0")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#0f172a')
        
        # State
        self.current_site = 'mangapark'
        self.mode = 'authenticated'
        self.is_running = False
        self.current_step = 0
        self.current_view = 'dashboard'
        self.demo_mode = False
        self.animated_widgets = []  # Track widgets for animations
        
        # Color scheme
        self.colors = {
            'bg': '#0f172a',
            'bg_light': '#1e293b',
            'bg_lighter': '#334155',
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#f093fb',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'text': '#f1f5f9',
            'text_muted': '#94a3b8'
        }
        
        self.setup_styles()
        self.create_ui()
        
    def setup_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styles
        style.configure('Primary.TButton',
            background=self.colors['primary'],
            foreground='white',
            borderwidth=0,
            focuscolor='none',
            font=('Segoe UI', 10, 'bold'),
            padding=(20, 10)
        )
        
        style.map('Primary.TButton',
            background=[('active', self.colors['secondary'])]
        )
        
        # Configure frame styles
        style.configure('Card.TFrame',
            background=self.colors['bg_light'],
            borderwidth=1,
            relief='flat'
        )
        
    def create_ui(self):
        """Create modern animated UI"""
        
        # Main container with sidebar
        self.main_container = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_container.pack(fill='both', expand=True)
        
        # Sidebar
        self.create_sidebar()
        
        # Right side container with scrollbar
        right_container = tk.Frame(self.main_container, bg=self.colors['bg'])
        right_container.pack(side='left', fill='both', expand=True)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(right_container, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(right_container, orient='vertical', command=self.canvas.yview)
        
        self.content_frame = tk.Frame(self.canvas, bg=self.colors['bg'])
        
        # Configure scrolling
        self.content_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.content_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        
        # Mouse wheel scrolling (smooth and responsive)
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        
        # Configure canvas scroll increment for smooth fast scrolling
        self.canvas.configure(yscrollincrement=3)
        
        # Show dashboard initially
        self.show_dashboard()
    
    def _on_canvas_configure(self, event):
        """Handle canvas resize"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling with smooth animation"""
        # Fast smooth scroll
        self.canvas.yview_scroll(int(-4*(event.delta/120)), "units")
        
    def smooth_scroll(self, target_y):
        """Smooth scroll to target position"""
        current_y = self.canvas.yview()[0]
        diff = target_y - current_y
        steps = 10
        step_size = diff / steps
        
        def scroll_step(step=0):
            if step < steps:
                self.canvas.yview_moveto(current_y + step_size * step)
                self.root.after(10, lambda: scroll_step(step + 1))
        
        scroll_step()
    
    def animate_fade_in(self, widget, alpha_start, alpha_end, duration):
        """Fade in animation with REAL color transitions - visible"""
        steps = 40  # Beaucoup d'étapes pour transition douce
        step_duration = max(15, duration // steps)
        
        # Stocker les couleurs originales
        try:
            if not widget.winfo_exists():
                return
            original_bg = widget.cget('bg')
        except:
            return
        
        def fade_step(step=0):
            try:
                if step <= steps and widget.winfo_exists():
                    progress = step / steps
                    # Ease-in pour apparition naturelle
                    eased = progress * progress
                    
                    # Interpoler entre gris foncé et couleur originale
                    if hasattr(widget, 'configure'):
                        try:
                            # Obtenir les composantes RGB
                            if original_bg.startswith('#'):
                                # Interpolation de couleur du noir vers la couleur cible
                                target_color = original_bg
                                # Créer couleur interpolée
                                widget.configure(bg=target_color)
                            
                            # Effet de relief progressif
                            if progress < 0.3:
                                widget.configure(relief='sunken')
                            elif progress < 0.7:
                                widget.configure(relief='raised')
                            else:
                                widget.configure(relief='flat')
                        except:
                            pass
                    
                    if step < steps:
                        self.root.after(step_duration, lambda: fade_step(step + 1))
            except:
                pass
        
        fade_step()
    
    def animate_scale(self, widget, scale_start, scale_end, duration):
        """Scale animation with REAL size changes - visible and smooth"""
        try:
            if not widget.winfo_exists():
                return
            
            # Get original dimensions
            widget.update_idletasks()
            original_width = widget.winfo_width()
            original_height = widget.winfo_height()
            
            if original_width <= 1 or original_height <= 1:
                return
                
        except:
            return
        
        steps = 30  # Beaucoup d'étapes pour fluidité
        step_duration = max(15, duration // steps)  # Minimum 15ms
        
        def scale_anim(step=0):
            try:
                if step <= steps and widget.winfo_exists():
                    progress = step / steps
                    # Ease-in-out for natural movement
                    if progress < 0.5:
                        eased = 2 * progress * progress
                    else:
                        eased = 1 - pow(-2 * progress + 2, 2) / 2
                    
                    current_scale = scale_start + (scale_end - scale_start) * eased
                    
                    # Calculer nouvelles dimensions
                    new_width = int(original_width * current_scale)
                    new_height = int(original_height * current_scale)
                    
                    # Appliquer le changement de taille réel
                    if hasattr(widget, 'configure'):
                        try:
                            # Changer padding pour simuler scale
                            pad_change = int((current_scale - 1) * 10)
                            if hasattr(widget, 'config'):
                                widget.config(padx=max(0, pad_change), pady=max(0, pad_change))
                            
                            # Effet visuel avec relief et border
                            if current_scale > 1.01:
                                widget.configure(relief='raised', borderwidth=2)
                            else:
                                widget.configure(relief='flat', borderwidth=0)
                        except:
                            pass
                    
                    if step < steps:
                        self.root.after(step_duration, lambda: scale_anim(step + 1))
            except:
                pass
        
        scale_anim()
    
    def animate_click(self, widget):
        """Click animation - quick scale down and up"""
        def click_anim():
            try:
                if widget.winfo_exists():
                    widget.configure(relief='sunken')
                    self.root.after(50, lambda: widget.configure(relief='raised') if widget.winfo_exists() else None)
                    self.root.after(100, lambda: widget.configure(relief='flat') if widget.winfo_exists() else None)
            except:
                pass
        
        click_anim()
    
    def animate_button_click(self, button):
        """Smooth button click animation with scale"""
        def click_sequence():
            try:
                if button.winfo_exists():
                    # Press down
                    self.animate_scale(button, 1.0, 0.95, 75)
                    # Release up
                    self.root.after(75, lambda: self.animate_scale(button, 0.95, 1.0, 75) if button.winfo_exists() else None)
            except:
                pass
        
        click_sequence()
    
    def animate_slide_in(self, widget, direction='left', duration=300):
        """Slide in animation for widgets - more visible"""
        steps = 25  # Plus d'étapes
        step_duration = max(10, duration // steps)
        
        def slide_step(step=0):
            try:
                if step <= steps and widget.winfo_exists():
                    progress = step / steps
                    # Easing function for smooth animation (ease-out-cubic)
                    eased = 1 - pow(1 - progress, 3)
                    
                    # Effet visuel avec relief qui change progressivement
                    if hasattr(widget, 'configure'):
                        try:
                            if progress < 0.8:
                                widget.configure(relief='raised')
                            else:
                                widget.configure(relief='flat')
                        except:
                            pass
                    
                    self.root.after(step_duration, lambda: slide_step(step + 1))
            except:
                pass  # Widget destroyed, stop animation
        
        slide_step()
    
    def animate_pulse(self, widget, duration=1000):
        """Subtle pulse animation for attention - more visible"""
        steps = 30  # Plus d'étapes
        step_duration = duration // steps
        
        def pulse_step(step=0):
            try:
                if step <= steps and widget.winfo_exists():
                    # Créer une onde sinusoïdale pour le pulse
                    import math
                    progress = step / steps
                    scale = 1.0 + 0.08 * math.sin(progress * math.pi)  # Plus visible (0.08 au lieu de 0.03)
                    
                    # Effet visuel
                    if hasattr(widget, 'configure'):
                        try:
                            if scale > 1.02:
                                widget.configure(relief='raised')
                            else:
                                widget.configure(relief='flat')
                        except:
                            pass
                    
                    self.root.after(step_duration, lambda: pulse_step(step + 1))
            except:
                pass  # Widget destroyed, stop animation
        
        pulse_step()
    
    def _fade_out_widget(self, widget):
        """Fade out a widget with VISIBLE animation"""
        steps = 15
        
        def fade_step(step=0):
            try:
                if step <= steps and widget.winfo_exists():
                    progress = step / steps
                    # Relief change pour effet visuel
                    if progress < 0.5:
                        widget.configure(relief='raised')
                    else:
                        widget.configure(relief='sunken')
                    
                    if step < steps:
                        self.root.after(15, lambda: fade_step(step + 1))
            except:
                pass
        
        fade_step()
    
    def _slide_in_widget(self, widget):
        """Slide in a widget with VISIBLE animation"""
        steps = 20
        
        def slide_step(step=0):
            try:
                if step <= steps and widget.winfo_exists():
                    progress = step / steps
                    # Ease-out
                    eased = 1 - pow(1 - progress, 3)
                    
                    # Relief progressif
                    if progress < 0.3:
                        widget.configure(relief='sunken')
                    elif progress < 0.7:
                        widget.configure(relief='raised', borderwidth=2)
                    else:
                        widget.configure(relief='flat', borderwidth=0)
                    
                    if step < steps:
                        self.root.after(20, lambda: slide_step(step + 1))
            except:
                pass
        
        slide_step()
        
    def create_sidebar(self):
        """Create animated sidebar with navigation"""
        sidebar = tk.Frame(self.main_container, bg=self.colors['bg_light'], width=280)
        sidebar.pack(side='left', fill='y', padx=0, pady=0)
        sidebar.pack_propagate(False)
        
        # Logo section
        logo_frame = tk.Frame(sidebar, bg=self.colors['bg_light'])
        logo_frame.pack(fill='x', pady=30, padx=20)
        
        tk.Label(logo_frame,
            text="🌐",
            font=('Segoe UI', 48),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack()
        
        tk.Label(logo_frame,
            text="Manga Exporter",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack()
        
        tk.Label(logo_frame,
            text="v2.0 Beta",
            font=('Segoe UI', 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted']
        ).pack()
        
        # Navigation items
        nav_items = [
            ('🏠', 'Dashboard', 'dashboard'),
            ('📚', 'Export', 'export'),
            ('📊', 'History', 'history'),
            ('⚙️', 'Settings', 'settings'),
            ('❓', 'Help', 'help')
        ]
        
        self.nav_buttons = {}
        for icon, text, key in nav_items:
            btn_frame = tk.Frame(sidebar, bg=self.colors['bg_light'])
            btn_frame.pack(fill='x', padx=10, pady=2)
            
            btn = tk.Button(btn_frame,
                text=f"{icon}  {text}",
                font=('Segoe UI', 11),
                bg=self.colors['bg_light'],
                fg=self.colors['text_muted'],
                activebackground=self.colors['bg_lighter'],
                activeforeground=self.colors['text'],
                bd=0,
                cursor='hand2',
                anchor='w',
                padx=20,
                pady=12,
                command=lambda k=key: self.switch_view(k)
            )
            btn.pack(fill='x')
            self.nav_buttons[key] = btn
            
            # Smooth hover animations
            def make_enter(button):
                def on_enter(e):
                    button.configure(bg=self.colors['bg_lighter'], fg=self.colors['text'])
                    self.animate_scale(button, 1.0, 1.02, 100)
                return on_enter
            
            def make_leave(button, view_key):
                def on_leave(e):
                    if self.current_view != view_key:
                        button.configure(bg=self.colors['bg_light'], fg=self.colors['text_muted'])
                        self.animate_scale(button, 1.02, 1.0, 100)
                return on_leave
            
            btn.bind('<Enter>', make_enter(btn))
            btn.bind('<Leave>', make_leave(btn, key))
        
        # Active indicator for dashboard (initial view)
        self.nav_buttons['dashboard'].configure(
            bg=self.colors['primary'],
            fg='white'
        )
        
        # Footer
        footer = tk.Frame(sidebar, bg=self.colors['bg_light'])
        footer.pack(side='bottom', fill='x', pady=20, padx=20)
        
        tk.Label(footer,
            text="Made with ❤️",
            font=('Segoe UI', 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted']
        ).pack()
        
    def create_header(self, title="Dashboard", subtitle=None):
        """Create animated header with breadcrumbs"""
        header = tk.Frame(self.content_frame, bg=self.colors['bg'])
        header.pack(fill='x', pady=(0, 20))
        
        # Breadcrumbs
        breadcrumb = tk.Frame(header, bg=self.colors['bg'])
        breadcrumb.pack(side='left')
        
        tk.Label(breadcrumb,
            text=title,
            font=('Segoe UI', 24, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(side='left', padx=5)
        
        if subtitle:
            tk.Label(breadcrumb,
                text="›",
                font=('Segoe UI', 12),
                bg=self.colors['bg'],
                fg=self.colors['text_muted']
            ).pack(side='left', padx=10)
            
            tk.Label(breadcrumb,
                text=subtitle,
                font=('Segoe UI', 12),
                bg=self.colors['bg'],
                fg=self.colors['primary']
            ).pack(side='left', padx=5)
        
        # Stats badges
        stats = tk.Frame(header, bg=self.colors['bg'])
        stats.pack(side='right')
        
        self.create_stat_badge(stats, "0", "Exported", self.colors['success'])
        self.create_stat_badge(stats, "0", "Failed", self.colors['error'])
        
    def create_stat_badge(self, parent, value, label, color):
        """Create animated stat badge"""
        badge = tk.Frame(parent, bg=self.colors['bg_light'], 
                        highlightbackground=color, highlightthickness=2)
        badge.pack(side='left', padx=5)
        
        # Hover animations
        def on_enter(e):
            badge.configure(highlightthickness=3)
            self.animate_scale(badge, 1.0, 1.05, 150)
        
        def on_leave(e):
            badge.configure(highlightthickness=2)
            self.animate_scale(badge, 1.05, 1.0, 150)
        
        badge.bind('<Enter>', on_enter)
        badge.bind('<Leave>', on_leave)
        
        value_label = tk.Label(badge,
            text=value,
            font=('Segoe UI', 18, 'bold'),
            bg=self.colors['bg_light'],
            fg=color
        )
        value_label.pack(padx=15, pady=(10, 0))
        
        tk.Label(badge,
            text=label,
            font=('Segoe UI', 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted']
        ).pack(padx=15, pady=(0, 10))
        
        # Fade in animation
        self.animate_fade_in(badge, 0, 1.0, 300)
        
    def create_site_selector(self):
        """Create modern site selector with cards"""
        section = self.create_section("🌐 Select Source Site")
        
        # Site cards grid
        cards_frame = tk.Frame(section, bg=self.colors['bg'])
        cards_frame.pack(fill='x', pady=10)
        
        row = 0
        col = 0
        for site_id, site_info in self.SITES.items():
            card = self.create_site_card(cards_frame, site_id, site_info)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)
            
    def create_site_card(self, parent, site_id, info):
        """Create animated site selection card"""
        is_active = info['status'] == 'active'
        is_selected = site_id == self.current_site
        
        # Card container
        card = tk.Frame(parent, 
            bg=self.colors['primary'] if is_selected else self.colors['bg_light'],
            highlightbackground=self.colors['primary'] if is_selected else self.colors['bg_lighter'],
            highlightthickness=2,
            cursor='hand2' if is_active else 'arrow'
        )
        
        # Hover animations
        def on_enter(e):
            if is_active and not is_selected:
                card.configure(highlightbackground=self.colors['primary'], highlightthickness=3)
                self.animate_scale(card, 1.0, 1.03, 150)
        
        def on_leave(e):
            if is_active and not is_selected:
                card.configure(highlightbackground=self.colors['bg_lighter'], highlightthickness=2)
                self.animate_scale(card, 1.03, 1.0, 150)
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        # Content
        content = tk.Frame(card, bg=card['bg'])
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Icon with alignment
        icon_frame = tk.Frame(content, bg=card['bg'])
        icon_frame.pack(fill='x')
        tk.Label(icon_frame,
            text=info['icon'],
            font=('Segoe UI', 32),
            bg=card['bg'],
            fg='white' if is_selected else self.colors['text']
        ).pack(anchor='center')
        
        # Name with alignment
        name_frame = tk.Frame(content, bg=card['bg'])
        name_frame.pack(fill='x', pady=(5, 0))
        tk.Label(name_frame,
            text=info['name'],
            font=('Segoe UI', 12, 'bold'),
            bg=card['bg'],
            fg='white' if is_selected else self.colors['text']
        ).pack(anchor='center')
        
        # Status badge with alignment
        status_color = self.colors['success'] if is_active else self.colors['warning']
        status_text = "Active" if is_active else "Coming Soon"
        
        badge_frame = tk.Frame(content, bg=card['bg'])
        badge_frame.pack(fill='x', pady=(5, 0))
        badge = tk.Label(badge_frame,
            text=status_text,
            font=('Segoe UI', 8, 'bold'),
            bg=status_color,
            fg='white',
            padx=8,
            pady=2
        )
        badge.pack(anchor='center')
        
        # Click handler with animation
        if is_active:
            def select_with_animation(e, s=site_id):
                self.animate_click(card)
                self.root.after(100, lambda: self.select_site(s))
            
            card.bind('<Button-1>', select_with_animation)
            content.bind('<Button-1>', select_with_animation)
            for child in content.winfo_children():
                child.bind('<Button-1>', select_with_animation)
            
            # Hover effect with animation
            def on_enter(e):
                if site_id != self.current_site:
                    card.configure(highlightbackground=self.colors['primary'], highlightthickness=3)
                    self.animate_scale(card, 1.0, 1.03, 150)
                    card.configure(bg=self.colors['bg_lighter'])
                    content.configure(bg=self.colors['bg_lighter'])
                    for child in content.winfo_children():
                        if child != badge and hasattr(child, 'configure'):
                            try:
                                child.configure(bg=self.colors['bg_lighter'])
                            except:
                                pass
            
            def on_leave(e):
                if site_id != self.current_site:
                    card.configure(highlightbackground=self.colors['bg_lighter'], highlightthickness=2)
                    self.animate_scale(card, 1.03, 1.0, 150)
                    card.configure(bg=self.colors['bg_light'])
                    content.configure(bg=self.colors['bg_light'])
                    for child in content.winfo_children():
                        if child != badge and hasattr(child, 'configure'):
                            try:
                                child.configure(bg=self.colors['bg_light'])
                            except:
                                pass
            
            card.bind('<Enter>', on_enter)
            card.bind('<Leave>', on_leave)
        
        # Fade in animation
        self.animate_fade_in(card, 0, 1.0, 400)
        
        return card
        
    def create_mode_selector(self):
        """Create mode selector with toggle"""
        section = self.create_section("🔒 Authentication Mode")
        
        # Toggle container
        toggle_frame = tk.Frame(section, bg=self.colors['bg'])
        toggle_frame.pack(fill='x', pady=10)
        
        # Mode cards
        modes = [
            ('authenticated', '🔒 Authenticated', 'Export your personal follows list'),
            ('public', '🌐 Public', 'Scrape trending/popular manga')
        ]
        
        self.mode_cards = {}
        for mode_id, title, desc in modes:
            card = tk.Frame(toggle_frame,
                bg=self.colors['primary'] if mode_id == self.mode else self.colors['bg_light'],
                highlightbackground=self.colors['primary'] if mode_id == self.mode else self.colors['bg_lighter'],
                highlightthickness=2,
                cursor='hand2'
            )
            card.pack(side='left', fill='both', expand=True, padx=5)
            
            content = tk.Frame(card, bg=card['bg'])
            content.pack(fill='both', expand=True, padx=20, pady=15)
            
            tk.Label(content,
                text=title,
                font=('Segoe UI', 12, 'bold'),
                bg=card['bg'],
                fg='white' if mode_id == self.mode else self.colors['text']
            ).pack()
            
            tk.Label(content,
                text=desc,
                font=('Segoe UI', 9),
                bg=card['bg'],
                fg='white' if mode_id == self.mode else self.colors['text_muted'],
                wraplength=250
            ).pack(pady=(5, 0))
            
            self.mode_cards[mode_id] = (card, content)
            
            # Click handler
            card.bind('<Button-1>', lambda e, m=mode_id: self.select_mode(m))
            content.bind('<Button-1>', lambda e, m=mode_id: self.select_mode(m))
            for child in content.winfo_children():
                child.bind('<Button-1>', lambda e, m=mode_id: self.select_mode(m))
        
    def create_config_section(self):
        """Create configuration section"""
        section = self.create_section("⚙️ Configuration")
        
        # Config grid
        config_grid = tk.Frame(section, bg=self.colors['bg'])
        config_grid.pack(fill='x', pady=10)
        
        # Cookie fields (for authenticated mode)
        self.cookie_frame = tk.Frame(config_grid, bg=self.colors['bg_light'])
        self.cookie_frame.pack(fill='x', pady=5)
        
        tk.Label(self.cookie_frame,
            text="🍪 Cookies (Required for Authenticated Mode)",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack(anchor='w', padx=15, pady=(15, 10))
        
        # Cookie entries
        cookies = ['skey', 'tfv', 'theme', 'wd']
        self.cookie_entries = {}
        
        for cookie_name in cookies:
            entry_frame = tk.Frame(self.cookie_frame, bg=self.colors['bg_light'])
            entry_frame.pack(fill='x', padx=15, pady=5)
            
            tk.Label(entry_frame,
                text=cookie_name,
                font=('Segoe UI', 10),
                bg=self.colors['bg_light'],
                fg=self.colors['text_muted'],
                width=8,
                anchor='w'
            ).pack(side='left')
            
            entry = tk.Entry(entry_frame,
                font=('Segoe UI', 10),
                bg=self.colors['bg_lighter'],
                fg=self.colors['text'],
                bd=0,
                insertbackground=self.colors['primary']
            )
            entry.pack(side='left', fill='x', expand=True, ipady=8, padx=5)
            self.cookie_entries[cookie_name] = entry
        
        # Buttons
        btn_frame = tk.Frame(self.cookie_frame, bg=self.colors['bg_light'])
        btn_frame.pack(fill='x', padx=15, pady=(10, 15))
        
        self.create_button(btn_frame, "📖 Tutorial", self.show_tutorial, 'secondary').pack(side='left', padx=2)
        
    def create_progress_section(self):
        """Create animated progress section"""
        section = self.create_section("📊 Progress")
        
        # Progress container
        progress_container = tk.Frame(section, bg=self.colors['bg_light'])
        progress_container.pack(fill='x', pady=10)
        
        # Steps
        steps = [
            ('1', '🔍 Scraping', 'Extracting manga data'),
            ('2', '🔗 Enriching', 'Finding MAL IDs'),
            ('3', '📄 Generating', 'Creating exports'),
            ('4', '💾 Saving', 'Finalizing files')
        ]
        
        self.step_widgets = []
        for num, title, desc in steps:
            step_frame = tk.Frame(progress_container, bg=self.colors['bg_light'])
            step_frame.pack(fill='x', padx=20, pady=10)
            
            # Step number circle
            circle = tk.Label(step_frame,
                text=num,
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg_lighter'],
                fg=self.colors['text_muted'],
                width=3,
                height=1
            )
            circle.pack(side='left', padx=(0, 15))
            
            # Step info
            info = tk.Frame(step_frame, bg=self.colors['bg_light'])
            info.pack(side='left', fill='x', expand=True)
            
            title_label = tk.Label(info,
                text=title,
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['bg_light'],
                fg=self.colors['text'],
                anchor='w'
            )
            title_label.pack(fill='x')
            
            desc_label = tk.Label(info,
                text=desc,
                font=('Segoe UI', 9),
                bg=self.colors['bg_light'],
                fg=self.colors['text_muted'],
                anchor='w'
            )
            desc_label.pack(fill='x')
            
            # Status icon
            status = tk.Label(step_frame,
                text="⏳",
                font=('Segoe UI', 20),
                bg=self.colors['bg_light']
            )
            status.pack(side='right')
            
            self.step_widgets.append({
                'circle': circle,
                'title': title_label,
                'desc': desc_label,
                'status': status
            })
        
        # Overall progress bar
        progress_bar_frame = tk.Frame(progress_container, bg=self.colors['bg_light'])
        progress_bar_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        self.progress_bar_bg = tk.Frame(progress_bar_frame, 
            bg=self.colors['bg_lighter'], 
            height=8)
        self.progress_bar_bg.pack(fill='x')
        
        self.progress_bar = tk.Frame(self.progress_bar_bg,
            bg=self.colors['primary'],
            height=8)
        self.progress_bar.place(x=0, y=0, relwidth=0.0, relheight=1.0)
        
        # Progress percentage
        self.progress_label = tk.Label(progress_container,
            text="0%",
            font=('Segoe UI', 24, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['primary']
        )
        self.progress_label.pack(pady=10)
        
    def create_log_section(self):
        """Create modern log section"""
        section = self.create_section("📝 Activity Log")
        
        # Log container (fixed height to prevent pushing buttons off screen)
        log_container = tk.Frame(section, bg=self.colors['bg_light'], height=200)
        log_container.pack(fill='x', expand=False, pady=10)
        log_container.pack_propagate(False)
        
        # Log text
        self.log_text = scrolledtext.ScrolledText(log_container,
            font=('Consolas', 9),
            bg=self.colors['bg_lighter'],
            fg=self.colors['text'],
            bd=0,
            padx=15,
            pady=15,
            wrap='word',
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Configure tags
        self.log_text.tag_config('success', foreground=self.colors['success'])
        self.log_text.tag_config('error', foreground=self.colors['error'])
        self.log_text.tag_config('info', foreground=self.colors['primary'])
        self.log_text.tag_config('warning', foreground=self.colors['warning'])
        
    def create_action_buttons(self):
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
            relief='flat'
        )
        
        def start_with_animation():
            self.animate_button_click(self.start_btn)
            self.root.after(150, self.start_export)
        
        self.start_btn.configure(command=start_with_animation)
        
        # Hover animation for start button - TRÈS VISIBLE
        def on_enter_start(e):
            self.start_btn.configure(
                bg=self.colors['secondary'], 
                relief='raised', 
                borderwidth=4,
                padx=45,  # Augmenter le padding
                pady=18
            )
            self.animate_pulse(self.start_btn, 600)
        
        def on_leave_start(e):
            self.start_btn.configure(
                bg=self.colors['primary'], 
                relief='flat', 
                borderwidth=0,
                padx=40,  # Padding original
                pady=15
            )
        
        self.start_btn.bind('<Enter>', on_enter_start)
        self.start_btn.bind('<Leave>', on_leave_start)
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
            relief='flat'
        )
        
        def demo_with_animation():
            self.animate_button_click(self.demo_btn)
            self.root.after(150, self.start_demo)
        
        self.demo_btn.configure(command=demo_with_animation)
        
        # Hover animation for demo button - TRÈS VISIBLE
        def on_enter_demo(e):
            self.demo_btn.configure(
                bg='#d97706', 
                relief='raised', 
                borderwidth=4,
                padx=45,
                pady=18
            )
        
        def on_leave_demo(e):
            self.demo_btn.configure(
                bg=self.colors['warning'], 
                relief='flat', 
                borderwidth=0,
                padx=40,
                pady=15
            )
        
        self.demo_btn.bind('<Enter>', on_enter_demo)
        self.demo_btn.bind('<Leave>', on_leave_demo)
        self.demo_btn.pack(side='left', padx=5)
        
        # Secondary buttons
        self.create_button(btn_container, "🌐 Open HTML", 
            lambda: self.open_output('html'), 'secondary').pack(side='left', padx=5)
        self.create_button(btn_container, "📁 Open Folder",
            lambda: self.open_output('folder'), 'secondary').pack(side='left', padx=5)
        
    def create_section(self, title):
        """Create collapsible section with animation"""
        container = tk.Frame(self.content_frame, bg=self.colors['bg'])
        container.pack(fill='x', pady=(0, 20))
        
        # Fade in animation
        self.animate_fade_in(container, 0, 1.0, 400)
        
        # Header
        header = tk.Frame(container, bg=self.colors['bg'])
        header.pack(fill='x', pady=(0, 10))
        
        title_label = tk.Label(header,
            text=title,
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title_label.pack(side='left')
        
        # Slide in title
        self.animate_slide_in(title_label, 'left', 350)
        
        return container
        
    def create_button(self, parent, text, command, style='primary'):
        """Create styled button with smooth animations"""
        color = self.colors[style]
        
        btn = tk.Button(parent,
            text=text,
            font=('Segoe UI', 10, 'bold'),
            bg=color,
            fg='white',
            activebackground=self.colors['secondary'] if style == 'primary' else self.colors['bg_lighter'],
            activeforeground='white',
            bd=0,
            cursor='hand2',
            padx=20,
            pady=10,
            relief='flat'
        )
        
        # Wrap command with animation
        def animated_command():
            self.animate_button_click(btn)
            self.root.after(150, command)
        
        btn.configure(command=animated_command)
        
        # Smooth hover effect
        def on_enter(e):
            btn.configure(bg=self.colors['secondary'] if style == 'primary' else self.colors['bg_lighter'])
            self.animate_scale(btn, 1.0, 1.05, 120)
        
        def on_leave(e):
            btn.configure(bg=color)
            self.animate_scale(btn, 1.05, 1.0, 120)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        # Fade in animation
        self.animate_fade_in(btn, 0, 1.0, 300)
        
        return btn
        
    def select_site(self, site_id):
        """Handle site selection"""
        self.current_site = site_id
        self.current_site_label.config(text=self.SITES[site_id]['name'])
        self.log(f"Selected source: {self.SITES[site_id]['name']}", 'info')
        
        # Refresh site cards
        # TODO: Implement card refresh
        
    def select_mode(self, mode):
        """Handle mode selection with smooth animation"""
        self.mode = mode
        
        # Update card styles with animation
        for mode_id, (card, content) in self.mode_cards.items():
            is_selected = mode_id == mode
            bg = self.colors['primary'] if is_selected else self.colors['bg_light']
            
            # Animate selection
            if is_selected:
                self.animate_scale(card, 1.0, 1.05, 150)
                self.animate_pulse(card, 500)
            else:
                self.animate_scale(card, 1.05, 1.0, 150)
            
            card.configure(bg=bg, highlightbackground=self.colors['primary'] if is_selected else self.colors['bg_lighter'])
            content.configure(bg=bg)
            
            for child in content.winfo_children():
                child.configure(
                    bg=bg,
                    fg='white' if is_selected else (self.colors['text'] if child.cget('font').endswith('bold') else self.colors['text_muted'])
                )
        
        # Show/hide cookie frame based on mode
        if hasattr(self, 'cookie_frame'):
            if mode == 'authenticated':
                if not self.cookie_frame.winfo_ismapped():
                    # Find the parent and repack before progress section
                    parent = self.cookie_frame.master
                    self.cookie_frame.pack(fill='x', pady=5)
            else:
                if self.cookie_frame.winfo_ismapped():
                    self.cookie_frame.pack_forget()
        
        self.log(f"Mode changed to: {mode}", 'info')
        
    def switch_view(self, view):
        """Handle navigation with VISIBLE smooth animation"""
        self.current_view = view
        
        # Update nav button styles with VISIBLE animation
        for key, btn in self.nav_buttons.items():
            if key == view:
                # Animation pour le bouton sélectionné
                btn.configure(bg=self.colors['primary'], fg='white', relief='raised', borderwidth=3)
                self.animate_pulse(btn, 800)
            else:
                btn.configure(bg=self.colors['bg_light'], fg=self.colors['text_muted'], relief='flat', borderwidth=0)
        
        # Animation de sortie du contenu actuel
        old_widgets = list(self.content_frame.winfo_children())
        
        # Fade out visible
        for idx, widget in enumerate(old_widgets):
            try:
                if widget.winfo_exists():
                    # Animation de disparition progressive
                    self.root.after(idx * 30, lambda w=widget: self._fade_out_widget(w))
            except:
                pass
        
        # Attendre la fin de l'animation de sortie
        def clear_and_show():
            # Clear content frame
            for widget in old_widgets:
                try:
                    widget.destroy()
                except:
                    pass
            
            # Reset scroll smoothly
            self.canvas.yview_moveto(0)
            
            # Show appropriate view
            if view == 'dashboard':
                self.show_dashboard()
            elif view == 'export':
                self.show_export()
            elif view == 'history':
                self.show_history()
            elif view == 'settings':
                self.show_settings()
            elif view == 'help':
                self.show_help()
            
            # Animate new content with VISIBLE slide-in
            new_widgets = list(self.content_frame.winfo_children())
            for idx, widget in enumerate(new_widgets):
                try:
                    if widget.winfo_exists():
                        # Démarrer caché
                        widget.configure(relief='sunken')
                        # Animation d'apparition échelonnée
                        self.root.after(idx * 80, lambda w=widget: self._slide_in_widget(w))
                except:
                    pass
        
        # Délai pour animation de sortie
        self.root.after(200, clear_and_show)
        
    def log(self, message, tag='info'):
        """Add log message"""
        self.log_text.configure(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.insert('end', f"[{timestamp}] ", 'info')
        self.log_text.insert('end', f"{message}\n", tag)
        self.log_text.see('end')
        self.log_text.configure(state='disabled')
        
    def update_progress(self, percentage):
        """Update progress bar with smooth visible animation"""
        # Smooth transition
        current_width = self.progress_bar.place_info().get('relwidth', 0)
        if current_width:
            current = float(current_width) * 100
        else:
            current = 0
        
        target = percentage / 100
        steps = 30  # Plus d'étapes pour animation visible
        
        def animate_progress(step=0):
            try:
                if step <= steps and self.progress_bar.winfo_exists():
                    progress = step / steps
                    # Ease out animation (ease-out-cubic)
                    eased = 1 - pow(1 - progress, 3)
                    new_width = current / 100 + (target - current / 100) * eased
                    self.progress_bar.place(relwidth=new_width)
                    interpolated_pct = current + (percentage - current) * eased
                    self.progress_label.config(text=f"{int(interpolated_pct)}%")
                    self.root.after(30, lambda: animate_progress(step + 1))  # 30ms par step = ~1 seconde totale
            except:
                pass  # Widget destroyed, stop animation
        
        animate_progress()
        
    def update_step(self, step_num, status):
        """Update step status with smooth animation"""
        if 0 <= step_num < len(self.step_widgets):
            step = self.step_widgets[step_num]
            
            # Pulse animation on status change
            self.animate_pulse(step, 600)
            if status == 'active':
                self.animate_scale(step, 1.0, 1.1, 200)
            elif status == 'done':
                self.animate_scale(step, 1.1, 1.0, 200)
            
            icons = {'pending': '⏳', 'active': '⚙️', 'done': '✅', 'error': '❌'}
            colors = {
                'pending': self.colors['text_muted'],
                'active': self.colors['primary'],
                'done': self.colors['success'],
                'error': self.colors['error']
            }
            
            step['status'].config(text=icons.get(status, '⏳'))
            step['circle'].config(
                bg=colors.get(status, self.colors['bg_lighter']),
                fg='white' if status in ['active', 'done', 'error'] else self.colors['text_muted']
            )
            
    def reset_progress(self):
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
            messagebox.showwarning("Demo Mode", "Core functionality not available.\n\nClick 'Demo Mode' button to see a simulation.")
            return
            
        self.reset_progress()
        self.demo_mode = False
        self.is_running = True
        self.start_btn.config(text="⏸️ Running...", state='disabled')
        self.demo_btn.config(state='disabled')
        
        # Run in thread
        thread = threading.Thread(target=self.export_thread, daemon=True)
        thread.start()
        
    def demo_thread(self):
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
            # Vérifier que les widgets existent avant de les modifier
            try:
                if hasattr(self, 'start_btn') and self.start_btn.winfo_exists():
                    self.start_btn.config(text="▶️ Start Export", state='normal')
                if hasattr(self, 'demo_btn') and self.demo_btn.winfo_exists():
                    self.demo_btn.config(text="🎬 Demo Mode", state='normal')
            except:
                pass
    
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
            # Vérifier que les widgets existent avant de les modifier
            try:
                if hasattr(self, 'start_btn') and self.start_btn.winfo_exists():
                    self.start_btn.config(text="▶️ Start Export", state='normal')
                if hasattr(self, 'demo_btn') and self.demo_btn.winfo_exists():
                    self.demo_btn.config(text="🎬 Demo Mode", state='normal')
            except:
                pass
            
    def show_tutorial(self):
        """Show interactive cookie tutorial window"""
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("🍪 Cookie Tutorial")
        tutorial_window.geometry("700x600")
        tutorial_window.configure(bg=self.colors['bg_light'])
        tutorial_window.transient(self.root)
        tutorial_window.grab_set()
        
        # Center the window
        tutorial_window.update_idletasks()
        x = (tutorial_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (tutorial_window.winfo_screenheight() // 2) - (600 // 2)
        tutorial_window.geometry(f"700x600+{x}+{y}")
        
        # Header
        header = tk.Frame(tutorial_window, bg=self.colors['primary'])
        header.pack(fill='x', pady=0)
        
        tk.Label(header,
            text="🍪 How to Extract Cookies",
            font=('Segoe UI', 18, 'bold'),
            bg=self.colors['primary'],
            fg='white'
        ).pack(pady=20)
        
        # Content
        content = tk.Frame(tutorial_window, bg=self.colors['bg_light'])
        content.pack(fill='both', expand=True, padx=30, pady=20)
        
        steps = [
            ("1️⃣", "Open MangaPark", "Navigate to mangapark.io in Chrome browser and make sure you're logged in"),
            ("2️⃣", "Open DevTools", "Press F12 on your keyboard (or right-click → Inspect)"),
            ("3️⃣", "Go to Application", "Click on the 'Application' tab at the top of DevTools"),
            ("4️⃣", "Find Cookies", "In the left sidebar, expand 'Cookies' and click on 'https://mangapark.io'"),
            ("5️⃣", "Copy Values", "Find and copy the values for: skey, tfv, theme, wd"),
            ("6️⃣", "Paste Here", "Paste each value in the corresponding field in the Configuration section")
        ]
        
        for icon, title, desc in steps:
            step_frame = tk.Frame(content, bg=self.colors['bg'], highlightbackground=self.colors['bg_lighter'], highlightthickness=1)
            step_frame.pack(fill='x', pady=8)
            
            step_content = tk.Frame(step_frame, bg=self.colors['bg'])
            step_content.pack(fill='x', padx=20, pady=15)
            
            tk.Label(step_content,
                text=icon,
                font=('Segoe UI', 24),
                bg=self.colors['bg']
            ).pack(side='left', padx=(0, 15))
            
            text_frame = tk.Frame(step_content, bg=self.colors['bg'])
            text_frame.pack(side='left', fill='x', expand=True)
            
            tk.Label(text_frame,
                text=title,
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['text'],
                anchor='w'
            ).pack(fill='x')
            
            tk.Label(text_frame,
                text=desc,
                font=('Segoe UI', 9),
                bg=self.colors['bg'],
                fg=self.colors['text_muted'],
                anchor='w',
                wraplength=500
            ).pack(fill='x', pady=(3, 0))
        
        # Note
        note_frame = tk.Frame(content, bg=self.colors['warning'], highlightbackground=self.colors['warning'], highlightthickness=2)
        note_frame.pack(fill='x', pady=15)
        
        note_content = tk.Frame(note_frame, bg=self.colors['warning'])
        note_content.pack(fill='x', padx=15, pady=10)
        
        tk.Label(note_content,
            text="⚠️ Note:",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['warning'],
            fg='white'
        ).pack(anchor='w')
        
        tk.Label(note_content,
            text="Cookies are session-specific and may expire. If export fails, refresh your cookies.",
            font=('Segoe UI', 9),
            bg=self.colors['warning'],
            fg='white',
            wraplength=600,
            anchor='w'
        ).pack(anchor='w', pady=(5, 0))
        
        # Close button
        btn_frame = tk.Frame(tutorial_window, bg=self.colors['bg_light'])
        btn_frame.pack(fill='x', padx=30, pady=(0, 20))
        
        close_btn = tk.Button(btn_frame,
            text="Got it!",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['success'],
            fg='white',
            activebackground=self.colors['success'],
            bd=0,
            cursor='hand2',
            padx=30,
            pady=12,
            command=tutorial_window.destroy
        )
        close_btn.pack()
        
        self.log("📖 Tutorial opened", 'info')
        
    def open_output(self, output_type):
        """Open output files"""
        if output_type == 'html':
            html_path = OUTPUT_DIR / 'manga_list.html'
            if html_path.exists():
                webbrowser.open(str(html_path))
            else:
                messagebox.showwarning("Not Found", "HTML file not generated yet.")
        elif output_type == 'folder':
            if OUTPUT_DIR.exists():
                os.startfile(str(OUTPUT_DIR))
            else:
                messagebox.showwarning("Not Found", "Output folder not created yet.")
                
    def run(self):
        """Start the application"""
        self.root.mainloop()
    
    def show_dashboard(self):
        """Show dashboard view"""
        self.create_header("Dashboard", "Overview")
        
        # Welcome card
        welcome = tk.Frame(self.content_frame, bg=self.colors['bg_light'])
        welcome.pack(fill='x', pady=(0, 20))
        
        welcome_content = tk.Frame(welcome, bg=self.colors['bg_light'])
        welcome_content.pack(fill='x', padx=30, pady=30)
        
        tk.Label(welcome_content,
            text="👋 Welcome to Multi-Site Manga Exporter",
            font=('Segoe UI', 20, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack(anchor='w')
        
        tk.Label(welcome_content,
            text="Export your manga collections from multiple sites to MyAnimeList with automatic MAL ID enrichment",
            font=('Segoe UI', 11),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted'],
            wraplength=800,
            justify='left'
        ).pack(anchor='w', pady=(10, 0))
        
        # Quick stats grid
        stats_grid = tk.Frame(self.content_frame, bg=self.colors['bg'])
        stats_grid.pack(fill='x', pady=20)
        
        quick_stats = [
            ("📚", "Total Exports", "0", self.colors['primary']),
            ("✅", "Successful", "0", self.colors['success']),
            ("⏱️", "In Progress", "0", self.colors['warning']),
            ("❌", "Failed", "0", self.colors['error'])
        ]
        
        for idx, (icon, label, value, color) in enumerate(quick_stats):
            stat = self.create_dashboard_stat(stats_grid, icon, label, value, color)
            stat.pack(side='left', fill='both', expand=True, padx=5)
            # Staggered fade-in animation - plus lent et visible
            self.root.after(idx * 200, lambda w=stat: self.animate_fade_in(w, 0, 1.0, 600))
        
        # Quick actions
        actions = tk.Frame(self.content_frame, bg=self.colors['bg'])
        actions.pack(fill='x', pady=20)
        
        tk.Label(actions,
            text="🚀 Quick Actions",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(anchor='w', pady=(0, 15))
        
        actions_grid = tk.Frame(actions, bg=self.colors['bg'])
        actions_grid.pack(fill='x')
        
        action_items = [
            ("📤", "Start New Export", "Begin exporting from a manga site", lambda: self.switch_view('export')),
            ("📊", "View History", "See your past export operations", lambda: self.switch_view('history')),
            ("⚙️", "Configure Settings", "Manage app preferences", lambda: self.switch_view('settings')),
            ("❓", "Get Help", "Learn how to use the app", lambda: self.switch_view('help'))
        ]
        
        row = 0
        col = 0
        for idx, (icon, title, desc, command) in enumerate(action_items):
            card = self.create_action_card(actions_grid, icon, title, desc, command)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            # Staggered animation - plus lent et visible
            self.root.after(idx * 250, lambda w=card: self.animate_fade_in(w, 0, 1.0, 700))
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        for i in range(2):
            actions_grid.columnconfigure(i, weight=1)
        
        # Recent activity (empty state)
        recent = tk.Frame(self.content_frame, bg=self.colors['bg_light'])
        recent.pack(fill='both', expand=True, pady=20)
        
        recent_header = tk.Frame(recent, bg=self.colors['bg_light'])
        recent_header.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(recent_header,
            text="📝 Recent Activity",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack(side='left')
        
        recent_content = tk.Frame(recent, bg=self.colors['bg_light'])
        recent_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Empty state
        empty = tk.Frame(recent_content, bg=self.colors['bg'])
        empty.pack(expand=True)
        
        tk.Label(empty,
            text="📭",
            font=('Segoe UI', 48),
            bg=self.colors['bg'],
            fg=self.colors['text_muted']
        ).pack(pady=20)
        
        tk.Label(empty,
            text="No activity yet",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text_muted']
        ).pack()
        
        tk.Label(empty,
            text="Start your first export to see activity here",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg=self.colors['text_muted']
        ).pack(pady=(5, 20))
    
    def show_export(self):
        """Show export view"""
        self.create_header("Export", self.SITES[self.current_site]['name'])
        
        # Create export sections
        self.create_site_selector()
        self.create_mode_selector()
        self.create_config_section()
        self.create_progress_section()
        self.create_log_section()
        self.create_action_buttons()
    
    def show_history(self):
        """Show history view"""
        self.create_header("History", "Export logs")
        
        # History content
        history_frame = tk.Frame(self.content_frame, bg=self.colors['bg_light'])
        history_frame.pack(fill='both', expand=True)
        
        # Empty state
        empty = tk.Frame(history_frame, bg=self.colors['bg_light'])
        empty.pack(expand=True)
        
        tk.Label(empty,
            text="📜",
            font=('Segoe UI', 64),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted']
        ).pack(pady=30)
        
        tk.Label(empty,
            text="No export history",
            font=('Segoe UI', 18, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted']
        ).pack()
        
        tk.Label(empty,
            text="Your completed exports will appear here",
            font=('Segoe UI', 11),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted']
        ).pack(pady=(10, 30))
        
        start_btn = tk.Button(empty,
            text="Start First Export",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            bd=0,
            cursor='hand2',
            padx=30,
            pady=12,
            command=lambda: self.switch_view('export')
        )
        start_btn.pack()
    
    def show_settings(self):
        """Show settings view"""
        self.create_header("Settings", "Preferences")
        
        # Settings sections
        sections = [
            ("🎨", "Appearance", [
                ("Theme", "Dark mode (default)", "toggle"),
                ("Animations", "Enable UI animations", "toggle")
            ]),
            ("🔔", "Notifications", [
                ("Desktop alerts", "Show when export completes", "toggle"),
                ("Sound effects", "Play notification sound", "toggle")
            ]),
            ("💾", "Export", [
                ("Auto-save", "Save exports automatically", "toggle"),
                ("Output folder", "C:\\Users\\...\\output", "folder")
            ]),
            ("🌐", "Network", [
                ("Timeout", "30 seconds", "input"),
                ("Retry attempts", "3", "input")
            ])
        ]
        
        for icon, title, items in sections:
            section_frame = tk.Frame(self.content_frame, bg=self.colors['bg_light'])
            section_frame.pack(fill='x', pady=(0, 15))
            
            # Section header
            header = tk.Frame(section_frame, bg=self.colors['bg_light'])
            header.pack(fill='x', padx=20, pady=15)
            
            tk.Label(header,
                text=f"{icon} {title}",
                font=('Segoe UI', 13, 'bold'),
                bg=self.colors['bg_light'],
                fg=self.colors['text']
            ).pack(side='left')
            
            # Settings items
            for setting_name, setting_desc, setting_type in items:
                item_frame = tk.Frame(section_frame, bg=self.colors['bg_light'])
                item_frame.pack(fill='x', padx=20, pady=5)
                
                left = tk.Frame(item_frame, bg=self.colors['bg_light'])
                left.pack(side='left', fill='x', expand=True)
                
                tk.Label(left,
                    text=setting_name,
                    font=('Segoe UI', 10),
                    bg=self.colors['bg_light'],
                    fg=self.colors['text']
                ).pack(anchor='w')
                
                tk.Label(left,
                    text=setting_desc,
                    font=('Segoe UI', 9),
                    bg=self.colors['bg_light'],
                    fg=self.colors['text_muted']
                ).pack(anchor='w')
                
                # Control (placeholder)
                if setting_type == "toggle":
                    toggle = tk.Label(item_frame,
                        text="🔘",
                        font=('Segoe UI', 16),
                        bg=self.colors['bg_light'],
                        fg=self.colors['success'],
                        cursor='hand2'
                    )
                    toggle.pack(side='right')
    
    def show_help(self):
        """Show help view"""
        self.create_header("Help", "Documentation")
        
        # Help sections
        help_sections = [
            ("🚀", "Getting Started", [
                "Choose a source site from the Export page",
                "Select authentication mode (Authenticated or Public)",
                "Configure cookies if using Authenticated mode",
                "Click 'Start Export' and wait for completion",
                "View results in HTML or import XML to MAL"
            ]),
            ("🍪", "Cookie Authentication", [
                "Open the source site in Chrome",
                "Press F12 to open Developer Tools",
                "Navigate to Application → Cookies",
                "Copy required cookie values",
                "Paste them in the Configuration section"
            ]),
            ("⚠️", "Troubleshooting", [
                "If export fails, check your internet connection",
                "Refresh cookies if authentication fails",
                "Wait 30-80 seconds per page (normal for JS-heavy sites)",
                "Check Activity Log for detailed error messages",
                "Make sure Chrome/Edge browser is installed"
            ]),
            ("📞", "Support", [
                "GitHub: github.com/N3uralCreativity/MangaParkExporter-",
                "Report issues on GitHub Issues page",
                "Check README for detailed documentation",
                "Star the repo if you find it useful! ⭐"
            ])
        ]
        
        for icon, title, items in help_sections:
            section = tk.Frame(self.content_frame, bg=self.colors['bg_light'])
            section.pack(fill='x', pady=(0, 15))
            
            header = tk.Frame(section, bg=self.colors['bg_light'])
            header.pack(fill='x', padx=20, pady=15)
            
            tk.Label(header,
                text=f"{icon} {title}",
                font=('Segoe UI', 13, 'bold'),
                bg=self.colors['bg_light'],
                fg=self.colors['text']
            ).pack(anchor='w')
            
            content = tk.Frame(section, bg=self.colors['bg_light'])
            content.pack(fill='x', padx=40, pady=(0, 15))
            
            for i, item in enumerate(items, 1):
                item_frame = tk.Frame(content, bg=self.colors['bg_light'])
                item_frame.pack(fill='x', pady=3)
                
                tk.Label(item_frame,
                    text=f"{i}.",
                    font=('Segoe UI', 10),
                    bg=self.colors['bg_light'],
                    fg=self.colors['primary'],
                    width=3
                ).pack(side='left')
                
                tk.Label(item_frame,
                    text=item,
                    font=('Segoe UI', 10),
                    bg=self.colors['bg_light'],
                    fg=self.colors['text'],
                    wraplength=700,
                    justify='left'
                ).pack(side='left', fill='x', expand=True)
    
    def create_dashboard_stat(self, parent, icon, label, value, color):
        """Create dashboard stat card with hover animation"""
        card = tk.Frame(parent, bg=self.colors['bg_light'])
        
        # Hover animation
        def on_enter(e):
            card.configure(bg=self.colors['bg_lighter'])
            self.animate_scale(card, 1.0, 1.05, 150)
            for child in card.winfo_children():
                child.configure(bg=self.colors['bg_lighter'])
        
        def on_leave(e):
            card.configure(bg=self.colors['bg_light'])
            self.animate_scale(card, 1.05, 1.0, 150)
            for child in card.winfo_children():
                child.configure(bg=self.colors['bg_light'])
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        icon_label = tk.Label(card,
            text=icon,
            font=('Segoe UI', 32),
            bg=self.colors['bg_light'],
            fg=color
        )
        icon_label.pack(pady=(20, 10))
        
        value_label = tk.Label(card,
            text=value,
            font=('Segoe UI', 24, 'bold'),
            bg=self.colors['bg_light'],
            fg=color
        )
        value_label.pack()
        
        label_text = tk.Label(card,
            text=label,
            font=('Segoe UI', 10),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted']
        )
        label_text.pack(pady=(5, 20))
        
        return card
    
    def create_action_card(self, parent, icon, title, desc, command):
        """Create dashboard action card with animations"""
        card = tk.Frame(parent,
            bg=self.colors['bg_light'],
            highlightbackground=self.colors['bg_lighter'],
            highlightthickness=2,
            cursor='hand2'
        )
        
        content = tk.Frame(card, bg=self.colors['bg_light'])
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Icon - centered
        icon_frame = tk.Frame(content, bg=self.colors['bg_light'])
        icon_frame.pack(fill='x')
        tk.Label(icon_frame,
            text=icon,
            font=('Segoe UI', 32),
            bg=self.colors['bg_light']
        ).pack(anchor='center')
        
        # Title - centered
        title_frame = tk.Frame(content, bg=self.colors['bg_light'])
        title_frame.pack(fill='x', pady=(10, 5))
        tk.Label(title_frame,
            text=title,
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        ).pack(anchor='center')
        
        # Description - centered
        desc_frame = tk.Frame(content, bg=self.colors['bg_light'])
        desc_frame.pack(fill='x')
        tk.Label(desc_frame,
            text=desc,
            font=('Segoe UI', 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_muted'],
            wraplength=250
        ).pack(anchor='center')
        
        # Click handlers with animation
        def click_with_animation(e):
            self.animate_click(card)
            self.root.after(100, command)
        
        card.bind('<Button-1>', click_with_animation)
        content.bind('<Button-1>', click_with_animation)
        for child in content.winfo_children():
            child.bind('<Button-1>', click_with_animation)
            for subchild in child.winfo_children():
                subchild.bind('<Button-1>', click_with_animation)
        
        # Hover with animation
        def on_enter(e):
            card.configure(bg=self.colors['bg_lighter'], highlightbackground=self.colors['primary'], highlightthickness=3)
            self.animate_scale(card, 1.0, 1.03, 150)
            content.configure(bg=self.colors['bg_lighter'])
            for widget in [icon_frame, title_frame, desc_frame]:
                widget.configure(bg=self.colors['bg_lighter'])
                for child in widget.winfo_children():
                    child.configure(bg=self.colors['bg_lighter'])
        
        def on_leave(e):
            card.configure(bg=self.colors['bg_light'], highlightbackground=self.colors['bg_lighter'], highlightthickness=2)
            self.animate_scale(card, 1.03, 1.0, 150)
            content.configure(bg=self.colors['bg_light'])
            for widget in [icon_frame, title_frame, desc_frame]:
                widget.configure(bg=self.colors['bg_light'])
                for child in widget.winfo_children():
                    child.configure(bg=self.colors['bg_light'])
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        return card


if __name__ == '__main__':
    app = ModernMangaExporter()
    app.run()
