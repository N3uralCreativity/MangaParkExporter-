# 📚 MangaPark to MAL Exporter

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/N3uralCreativity/MangaParkExporter-/releases)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

A small tool to rescue your manga data when a site goes down or you just want to move elsewhere.

You read your manga on a site (like MangaPark), you have a list of favorites and chapters read, and you don't want to lose that.  
This app exports your follows + reading progress to **MyAnimeList** or to local files you can reuse later.

![Screenshot](assets/screenshots/Screenshot%202025-11-27%20232828.png)

---

## ✨ What it does

- 🧾 **Exports your data**
  - Favorites / follows
  - Chapters read count
  - From a manga site → to MAL or to files

- 🔍 **Two ways to grab your list**
  - **Authenticated mode**: uses your cookies to read *your* personal follows
  - **Public mode**: scrapes public lists like trending/popular (no login needed)

- 🔗 **MAL integration**
  - Looks up MAL IDs via the Jikan API
  - Fuzzy matching and basic confidence handling

- 📄 **Exports to**
  - **MAL XML** – import directly into MyAnimeList
  - **HTML** – a simple, searchable page of your library
  - **JSON** – raw data for developers

- 🖥️ **Modern Desktop App**
  - PyQt6 with full-screen interface
  - Dark & Light themes
  - Interactive dashboard with stats
  - Real-time progress tracking

---

## 🚀 Quick Start

### Option 1: Download Executable (Windows)

1. Go to **[Latest Release](https://github.com/N3uralCreativity/MangaParkExporter-/releases/latest)**
2. Download `MangaPark-Exporter-Vxxx.exe` (222 MB)
3. Make sure **Chrome** is installed
4. Double-click to run (no installation needed!)
5. Navigate to Export page and start exporting

### Option 2: Run from Source

```bash
git clone https://github.com/N3uralCreativity/MangaParkExporter-.git
cd MangaParkExporter-
pip install -r requirements.txt
python src/desktop_app_v3.py
```

Or use the quick launcher:
```bash
python run.py
```

---

## 📖 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Full Documentation](docs/README.md)** - Complete user guide
- **[Release Notes](docs/RELEASE_v2.0.0.md)** - What's new in V2.0.0
- **[Project Website](https://n3uralcreativity.github.io/MangaParkExporter-/)** - Homepage

---

## 🛠️ Project Structure

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

---

## 📋 Features

- 🖥️ **Modern Desktop App** - PyQt6 with embedded web UI
- 🎨 **2 Beautiful Themes** - Dark & Light modes
- 📊 **Interactive Dashboard** - Real-time stats and history
- 📄 **Multiple Formats** - XML, HTML, JSON exports
- 🔗 **Smart MAL Matching** - Fuzzy title matching with confidence scores
- ⚙️ **Extensive Settings** - Customizable fonts, animations, export options
- 📈 **Export History** - Track all your exports with search
- 🚀 **Step-by-Step Progress** - Visual indicators for each phase

---

## 💻 Building from Source

```bash
# Navigate to build directory
cd build

# Run build script
python build_exe_v3.py

# Executable will be in dist/
# dist/MangaPark-Exporter-V3.exe
```

---

## 📝 Requirements

### For Executable (.exe)
- Windows 10/11 (64-bit)
- Google Chrome
- No Python needed!

### For Source Code
- Python 3.11+
- Google Chrome
- Dependencies from requirements.txt

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## ⚠️ Disclaimer

This tool is for **personal backup & migration only**.  
Please respect MangaPark's and MyAnimeList's Terms of Service.

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/N3uralCreativity/MangaParkExporter-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/N3uralCreativity/MangaParkExporter-/discussions)

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- MangaPark for the manga reading platform
- MyAnimeList for the database
- Python community for amazing libraries (PyQt6, Selenium, BeautifulSoup4, Requests)

---

**Made by [@N3uralCreativity](https://github.com/N3uralCreativity)**

⭐ If this saved your manga list, consider starring the repo!
