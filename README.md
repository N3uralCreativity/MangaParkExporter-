# 📚 MangaPark to MAL Exporter

<<<<<<< HEAD
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/N3uralCreativity/MangaParkExporter-/releases)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

Modern desktop application to export your MangaPark collection to MyAnimeList with automatic MAL ID enrichment, beautiful themes, and multiple export formats.

![Screenshot](assets/screenshots/Screenshot%202025-11-27%20232828.png)

## ⚡ Quick Start

### Download & Run (Windows)
1. Download [MangaPark-Exporter-V2.exe](https://github.com/N3uralCreativity/MangaParkExporter-/releases/download/v2.0.0/MangaPark-Exporter-V2.exe) (222 MB)
2. Double-click to run (no installation needed!)
3. Navigate to Export page and start exporting

### Run from Source
```bash
git clone https://github.com/N3uralCreativity/MangaParkExporter-.git
cd MangaParkExporter-
pip install -r requirements.txt
python src/desktop_app_v3.py
```
=======
A small tool to rescue your manga data when a site goes down or you just want to move elsewhere.

You read your manga on a site (like MangaPark), you have a list of favorites and chapters read, and you don’t want to lose that.  
This app exports your follows + reading progress to **MyAnimeList** or to local files you can reuse later.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## ✨ What it does
>>>>>>> 60de69b12349fd7f8af64f863741e99474524de7

- 🧾 **Exports your data**
  - Favorites / follows
  - Chapters read count
  - From a manga site → to MAL or to files

<<<<<<< HEAD
- 🖥️ **Modern Desktop App** - PyQt6 with full-screen interface
- 🎨 **Beautiful Themes** - Dark & Light modes
- 📊 **Interactive Dashboard** - Real-time stats and history
- 📄 **Multiple Formats** - XML, HTML, JSON exports
- 🔗 **Smart Matching** - Fuzzy MAL ID detection
- ⚙️ **Extensive Settings** - Customizable fonts, animations, and more

## 📖 Documentation

- [Full Documentation](docs/README.md) - Complete user guide
- [Release Notes](docs/RELEASE_v2.0.0.md) - What's new in V2
- [Website](https://n3uralcreativity.github.io/MangaParkExporter-/) - Project homepage

## 🛠️ Development

### Project Structure
```
MangaParkExporter/
├── src/                    # Source code
│   ├── desktop_app_v3.py   # Main application
│   └── mangapark_gui_web.html  # UI template
├── build/                  # Build scripts
│   └── build_exe_v3.py     # PyInstaller build
├── docs/                   # Documentation
├── assets/                 # Static assets
├── legacy/                 # Old versions
└── examples/               # Example outputs
```

### Building from Source
```bash
cd build
python build_exe_v3.py
```

The executable will be in `dist/MangaPark-Exporter-V3.exe`

## 📋 Requirements

- **Python 3.11+** (for source)
- **Google Chrome** (for web scraping)
- **Windows 10/11** (for .exe)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- MangaPark for the platform
- MyAnimeList for the database
- Python community for amazing libraries

---

**Made by [N3uralCreativity](https://github.com/N3uralCreativity)**
=======
- 🔍 **Two ways to grab your list**
  - **Authenticated mode**: uses your cookies to read *your* personal follows
  - **Public mode**: scrapes public lists like trending/popular (no login needed)

- 🔗 **MAL integration**
  - Looks up MAL IDs via the Jikan API
  - Fuzzy matching and basic confidence handling

- 📄 **Exports to**
  - **MAL XML** – import directly into MyAnimeList
  - **HTML** – a simple, searchable page of your library

- 🖥️ **Simple GUI**
  - Buttons for modes and export
  - Progress bar + logs
  - Optional auto-fetch of cookies from Chrome (Currently Disabled cuz its hell to maintain bruh)

---

## 🚀 How to use (quick version – Windows)

The easiest way is to use the ready-made **.exe** file:

1. Go to the **latest release** on GitHub 👉 [Lastest Release](https://github.com/N3uralCreativity/MangaParkExporter-/releases/latest)
2. Download the `.exe` file (for example: `MangaParkExporter-X.X.X.exe`).
3. Make sure **Chrome or Edge** is installed on your PC AND you are logged into the site you wish to export data from.
4. Double-click the `.exe`:
   - Choose **Authenticated** if you want to export **your own favorites & progress**.
   - Choose **Public** if you just want a list from public/trending pages.
5. Click **Start Export** and wait until it finishes.
6. Open the generated **XML** (for MAL import) or **HTML** (to browse locally) in the `output/` folder.

No installation, no command line required unless you want it : 

```bash
git clone https://github.com/N3uralCreativity/MangaParkExporter-.git
cd MangaParkExporter-
pip install -r requirements.txt
python desktop_app_v3.py
```

---

## 🧑‍💻 Getting started from source (advanced users)

If you prefer running from source instead of using the .exe:

### Run from source

1. Install **Python 3.8+**
2. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/MangaParkExporter.git
   cd MangaParkExporter
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch:
   ```bash
   python mangapark_gui.py
   ```

### Build a standalone `.exe` (Windows)

```bash
python build_exe.py
```

- The `.exe` will appear in `dist/`
- No Python needed for end users  
- Requires Chrome/Edge installed (for Selenium)

---

## 📖 Basic usage (in the app)

### Authenticated mode (your own follows & progress)

1. Choose **🔒 Authenticated** in the app.  
2. Let the app **auto-fetch cookies** from Chrome  
   - or paste your cookies manually if you prefer.  
3. Click **▶️ Start Export**.  
4. When it finishes, open:
   - The **XML** file (for MAL import).
   - The **HTML** file (to browse your list locally).

### Public mode (no account needed)

1. Choose **🌐 Public**.  
2. Click **▶️ Start Export**.  
3. It scrapes public lists (e.g. trending/popular) and exports them the same way.

---

## 📂 Output

Everything goes into the `output/` folder:

- `mangapark_to_mal.xml` – MAL-compatible export  
- `manga_list.html` – searchable manga list in your browser  

---

## 🛠️ Under the hood (short version)

- **selenium** – drives a browser to load the manga site
- **beautifulsoup4** – parses the HTML
- **requests** – calls the Jikan API
- **browser-cookie3** – grabs cookies from Chrome (or so its supposed to but wtv)
- **tkinter** – provides the GUI

Flow:

1. Scrape your follows and chapter progress from the site.  
2. For each title, query **Jikan API v4** to find the corresponding MAL entry.  
3. Respect basic rate limits.  
4. Generate MAL XML + an HTML library view.

---

## ⚠️ Requirements (for the `.exe` version)

- Windows 10/11  
- Chrome or Edge installed  

---

## 📝 License

This project is under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

## ⚖️ Disclaimer

This tool is meant for **personal backup & migration only**.  
Please respect MangaPark’s and MyAnimeList’s Terms of Service and don’t abuse scraping.

---

## 📧 Support & roadmap

- Problems or ideas? Open an issue on GitHub.
- Planned / possible additions:
  - Support for more manga sites (e.g. MangaDex)
  - Extra export formats (CSV, JSON)
  - Better handling of very large lists
  - More options around MAL lists (custom categories, etc.)

---

Made by [@N3uralCreativity](https://github.com/N3uralCreativity)  
⭐ If this saved your list, consider starring the repo!

Also this was not supposed to be publily released at all so idk rn im motivated for it but that might change so don't expect too much of it though i would like to add features like importing into sites / Selecting which to import and eventually accounts whoever knows..
>>>>>>> 60de69b12349fd7f8af64f863741e99474524de7
