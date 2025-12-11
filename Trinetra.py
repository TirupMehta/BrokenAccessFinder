import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import queue
import re
import webbrowser

# --- CONFIGURATION ---
ctk.set_appearance_mode("System")  # Use computer's Dark/Light mode
ctk.set_default_color_theme("blue")
APP_NAME = "Trinetra (Third Eye) - Broken Access Finder"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# --- BACKEND LOGIC ---
class ScannerLogic:
    def __init__(self, start_url, max_depth, log_queue, result_queue):
        self.start_url = start_url
        self.max_depth = max_depth
        self.log_queue = log_queue
        self.result_queue = result_queue
        self.visited = set()
        self.broken_links = []
        self.sensitive_endpoints = []
        
        self.bac_keywords = ['admin', 'config', 'backup', 'user', 'profile', 'account', 'settings']
        self.id_pattern = re.compile(r'(\?|&)(id|user_id|uid|profile_id)=[0-9]+|/[0-9]+($|/)')

    def is_valid(self, url):
        return bool(urlparse(url).netloc) and bool(urlparse(url).scheme)

    def is_internal(self, url):
        return urlparse(self.start_url).netloc == urlparse(url).netloc

    def scan_url(self, url, depth):
        if depth > self.max_depth or url in self.visited:
            return

        self.visited.add(url)
        self.log_queue.put(f"[*] Crawling: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=4)
            
            if response.status_code >= 400:
                self.log_queue.put(f"!!! BROKEN LINK ({response.status_code}): {url}")
                self.broken_links.append((response.status_code, url))
                return

            # Check for BAC candidates
            if self.id_pattern.search(url) or any(k in url.lower() for k in self.bac_keywords):
                self.log_queue.put(f"--- CANDIDATE: {url}")
                self.sensitive_endpoints.append(url)

            soup = BeautifulSoup(response.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                abs_url = urljoin(url, a['href']).split('#')[0]
                if self.is_valid(abs_url) and self.is_internal(abs_url):
                    self.scan_url(abs_url, depth + 1)

        except Exception:
            pass

    def start(self):
        self.scan_url(self.start_url, 0)
        self.result_queue.put({
            "total": len(self.visited),
            "broken": self.broken_links,
            "sensitive": self.sensitive_endpoints
        })

# --- UI FRONTEND ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title(APP_NAME)
        self.geometry("1200x700") # Increased overall width slightly to accommodate bigger sidebar
        
        # Configure Grid Layout
        # Column 0 is sidebar (fixed width), Column 1 is main content (expands)
        self.grid_columnconfigure(0, weight=0) # IMPORTANT: Weight 0 keeps sidebar fixed
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Threading
        self.log_queue = queue.Queue()
        self.result_queue = queue.Queue()

        self._setup_sidebar()
        self._setup_main_area()
        self._start_monitoring()

    def _setup_sidebar(self):
        # Sidebar Frame
        # --- CHANGED: Width increased to 450 ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        # This prevents the sidebar from shrinking if widgets inside are small
        self.sidebar.grid_propagate(False) 
        
        self.sidebar.grid_columnconfigure(0, weight=1) # Ensure widgets inside sidebar stretch
        self.sidebar.grid_rowconfigure(6, weight=1) # Push copyright to bottom

        # Logo
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Domain Broken\nAccess SCANNER", 
            font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        # 1. Target URL Input
        self.url_label = ctk.CTkLabel(self.sidebar, text="Target Domain:", anchor="w")
        self.url_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.url_entry = ctk.CTkEntry(self.sidebar, placeholder_text="https://example.com")
        self.url_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.url_entry.insert(0, "http://testphp.vulnweb.com")

        # 2. Depth Input
        self.depth_label = ctk.CTkLabel(self.sidebar, text="Scan Depth:", anchor="w")
        self.depth_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.depth_entry = ctk.CTkEntry(self.sidebar, placeholder_text="2")
        self.depth_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.depth_entry.insert(0, "5")

        # 3. Action Button
        self.scan_btn = ctk.CTkButton(self.sidebar, text="START SCAN", command=self.start_scan,
            fg_color="#1f538d", hover_color="#14375e", height=50,
            font=ctk.CTkFont(size=15, weight="bold"))
        self.scan_btn.grid(row=5, column=0, padx=20, pady=30, sticky="ew")

        # 4. Copyright (Bottom)
        self.copyright_btn = ctk.CTkButton(
            self.sidebar, 
            text="© Tirup Mehta", 
            fg_color="transparent", 
            text_color=("gray60", "gray40"),
            hover_color=("gray90", "gray20"),
            font=ctk.CTkFont(size=12),
            cursor="hand2",
            command=self.open_website
        )
        self.copyright_btn.grid(row=6, column=0, padx=20, pady=20, sticky="s")

    def _setup_main_area(self):
        # Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        
        self.tab_logs = self.tabview.add("Live Logs")
        self.tab_broken = self.tabview.add("Broken Links")
        self.tab_bac = self.tabview.add("Access Control Candidates")

        # Logs
        self.tab_logs.grid_columnconfigure(0, weight=1)
        self.tab_logs.grid_rowconfigure(0, weight=1)
        self.log_box = ctk.CTkTextbox(self.tab_logs, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.log_box.configure(state="disabled")

        # Broken Links
        self.tab_broken.grid_rowconfigure(0, weight=1)
        self.tab_broken.grid_columnconfigure(0, weight=1)
        self.broken_box = ctk.CTkTextbox(self.tab_broken, text_color="#ff5555", font=ctk.CTkFont(family="Consolas", size=12))
        self.broken_box.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.broken_box.insert("0.0", "Scan to see broken links here...\n")
        self.broken_box.configure(state="disabled")

        # BAC
        self.tab_bac.grid_rowconfigure(0, weight=1)
        self.tab_bac.grid_columnconfigure(0, weight=1)
        self.bac_box = ctk.CTkTextbox(self.tab_bac, text_color="#55aaff", font=ctk.CTkFont(family="Consolas", size=12))
        self.bac_box.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.bac_box.insert("0.0", "Scan to see potential BAC/IDOR endpoints here...\n")
        self.bac_box.configure(state="disabled")

    def open_website(self):
        webbrowser.open("https://tirup.in")

    def start_scan(self):
        url = self.url_entry.get()
        try:
            depth = int(self.depth_entry.get())
        except ValueError:
            tk.messagebox.showerror("Error", "Depth must be a number (e.g. 2)")
            return

        if not url.startswith("http"):
            tk.messagebox.showerror("Error", "URL must start with http:// or https://")
            return

        # UI Updates
        self.scan_btn.configure(state="disabled", text="Scanning...")
        
        # Clear previous results
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end")
        self.log_box.configure(state="disabled")
        
        self.broken_box.configure(state="normal")
        self.broken_box.delete("0.0", "end")
        self.broken_box.configure(state="disabled")
        
        self.bac_box.configure(state="normal")
        self.bac_box.delete("0.0", "end")
        self.bac_box.configure(state="disabled")

        # Start Thread
        scanner = ScannerLogic(url, depth, self.log_queue, self.result_queue)
        threading.Thread(target=scanner.start, daemon=True).start()

    def _start_monitoring(self):
        # Log Monitor
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_box.configure(state="normal")
                self.log_box.insert("end", msg + "\n")
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
        except queue.Empty:
            pass

        # Result Monitor
        try:
            report = self.result_queue.get_nowait()
            self.scan_btn.configure(state="normal", text="START SCAN")
            
            # Populate Broken
            self.broken_box.configure(state="normal")
            if not report['broken']:
                self.broken_box.insert("end", "No broken links found!")
            for code, link in report['broken']:
                self.broken_box.insert("end", f"[{code}] {link}\n")
            self.broken_box.configure(state="disabled")

            # Populate BAC
            self.bac_box.configure(state="normal")
            if not report['sensitive']:
                self.bac_box.insert("end", "No obvious BAC candidates found.")
            for link in report['sensitive']:
                self.bac_box.insert("end", f"{link}\n")
            self.bac_box.configure(state="disabled")
            
            tk.messagebox.showinfo("Done", f"Scan finished! Checked {report['total']} URLs.")
        except queue.Empty:
            pass

        self.after(100, self._start_monitoring)

if __name__ == "__main__":
    app = App()
    app.mainloop()