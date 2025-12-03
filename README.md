# 📚 MangaPark to MAL Exporter

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

## ✨ Features

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
