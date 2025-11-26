# 📚 MangaPark to MAL Exporter

A powerful desktop application to export your MangaPark follows to MyAnimeList (MAL) with automatic MAL ID enrichment and beautiful HTML visualization.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

- 🔍 **Dual Scraping Modes**
  - 🔒 Authenticated: Export your personal follows list (requires cookies)
  - 🌐 Public: Scrape trending/popular manga (no login needed)

- 🔗 **MAL ID Enrichment**
  - Automatically finds MAL IDs using the Jikan API
  - Smart title matching with confidence scoring
  - Real-time progress tracking

- 📄 **Export Formats**
  - MAL-compatible XML for direct import
  - Beautiful HTML page with search & filters

- 🎨 **Modern GUI**
  - Visual progress indicators
  - Real-time statistics
  - Colored logging console
  - Auto-fetch cookies from Chrome

## 🚀 Quick Start

### Option 1: Run from Source

1. **Install Python 3.8+** (if not already installed)

2. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/MangaParkExporter.git
   cd MangaParkExporter
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python mangapark_gui.py
   ```

### Option 2: Build Standalone .exe

1. **Run the build script**
   ```bash
   python build_exe.py
   ```

2. **Find your .exe in the `dist/` folder**
   - The executable is completely standalone
   - No Python installation required for end users
   - Only Chrome/Edge browser needed (for Selenium)

## 📖 Usage Guide

### Authenticated Mode (Personal Follows)

1. **Select "🔒 Authenticated" mode**

2. **Get your cookies** (choose one):
   - Click "🔄 Auto-Fetch Cookies from Chrome"
   - OR manually enter cookies:
     - Open MangaPark in Chrome
     - Press F12 → Application → Cookies
     - Copy: `skey`, `tfv`, `theme`, `wd`

3. **Click "▶️ Start Export"**

4. **Wait for completion** (progress shown in real-time)

5. **View results**:
   - Click "🌐 Open HTML" to view in browser
   - Click "📁 Open Folder" to access XML files

### Public Mode (No Login)

1. **Select "🌐 Public" mode**

2. **Click "▶️ Start Export"**

3. **Done!** - Scrapes trending/popular manga

## 📂 Output Files

All files are saved in the `output/` folder:

- **mangapark_to_mal.xml** - Import this to MyAnimeList
- **manga_list.html** - Browse your collection in the browser

## 🛠️ Technical Details

### Dependencies

- **selenium** - Browser automation for scraping
- **beautifulsoup4** - HTML parsing
- **requests** - HTTP requests for Jikan API
- **browser-cookie3** - Auto-fetch cookies from Chrome
- **tkinter** - GUI (included with Python)

### How It Works

1. **Scraping**: Uses Selenium with headless Chrome to render JavaScript-heavy pages
2. **MAL Matching**: Queries Jikan API v4 with fuzzy string matching (60% threshold)
3. **Rate Limiting**: Respects 1 request/second limit
4. **Export**: Generates MAL-compatible XML and responsive HTML

### API Usage

- **Jikan API v4** (unofficial MAL API)
  - No authentication required
  - Rate limit: 1 request/second
  - Endpoint: `https://api.jikan.moe/v4/manga`

## 🔧 Building the .exe

The `build_exe.py` script automates everything:

```bash
python build_exe.py
```

This will:
1. ✅ Install all dependencies from `requirements.txt`
2. ✅ Install PyInstaller
3. ✅ Build a single standalone `.exe` file
4. ✅ Include all necessary packages

The resulting `.exe` can be distributed to anyone without requiring Python installation!

## ⚠️ Requirements for .exe Users

- **Chrome or Edge browser** must be installed (Selenium uses it)
- **Windows 10/11** (for .exe version)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Jikan API](https://jikan.moe/) - Unofficial MAL API
- [MangaPark](https://mangapark.io/) - Manga reading platform
- [MyAnimeList](https://myanimelist.net/) - Anime and manga database

## ⚖️ Disclaimer

This tool is for personal use only. Please respect MangaPark's and MyAnimeList's Terms of Service. Use responsibly and don't abuse the scraping functionality.

## 📧 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check existing issues for solutions

## 🗺️ Roadmap

- [ ] Support for other manga sites (MangaDex, etc.)
- [ ] Batch processing for large lists
- [ ] Custom MAL list categories
- [ ] Export to other formats (CSV, JSON)
- [ ] Dark mode toggle

---

Made with ❤️ by [@N3uralCreativity](https://github.com/yourusername)

⭐ Star this repo if you find it helpful!
