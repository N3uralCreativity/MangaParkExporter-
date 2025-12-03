# 🎉 MangaPark to MAL Exporter v1.0.0 - Initial Release

**Release Date:** November 26, 2025  
**Download:** [MangaPark-to-MAL-Exporter.exe](https://github.com/N3uralCreativity/MangaParkExporter-/releases/download/v1.0.0/MangaPark-to-MAL-Exporter.exe) (21 MB)

---

## 🚀 What's New

This is the **first stable release** of MangaPark to MAL Exporter! A complete desktop application that makes exporting your MangaPark manga collection to MyAnimeList effortless.

### 🌟 Key Features

#### 🔍 **Dual Scraping Modes**
- **🔒 Authenticated Mode**: Export your personal follows list (requires MangaPark cookies)
- **🌐 Public Mode**: Scrape trending/popular manga without login

#### 🔗 **Automatic MAL ID Enrichment**
- Smart title matching using Jikan API v4
- Fuzzy string matching with 60% confidence threshold
- Real-time progress tracking with success rates
- Handles alternative titles and romanizations

#### 📄 **Multiple Export Formats**
- **XML Format**: Direct import to MyAnimeList (`mangapark_to_mal.xml`)
- **HTML Format**: Beautiful, responsive webpage with search & filters (`manga_list.html`)

#### 🎨 **Modern GUI Experience**
- Visual 4-step progress indicators (⏳ → ⚙️ → ✅)
- Real-time statistics dashboard
- Color-coded logging console (success, info, errors, debug)
- Animated progress bars

#### 🍪 **Easy Cookie Management**
- ~~Auto-fetch cookies from Chrome browser~~ *(Disabled in .exe version due to Windows security)*
- Manual cookie entry with step-by-step tutorial
- Clear instructions with DevTools method (100% reliable)

---

## 📥 Download & Installation

### Option 1: Standalone Executable (Recommended)

**Windows 10/11 Users:**

1. **Download** the `.exe` file from the release assets below
2. **Double-click** `MangaPark-to-MAL-Exporter.exe` to run
3. **Done!** No Python installation required

**Requirements:**
- Chrome or Edge browser installed (for Selenium)
- Windows 10 or Windows 11

### Option 2: Run from Source

**All Platforms (Windows/Mac/Linux):**

```bash
# Clone the repository
git clone https://github.com/N3uralCreativity/MangaParkExporter-.git
cd MangaParkExporter-

# Install dependencies
pip install -r requirements.txt

# Run the application
python mangapark_gui.py
```

**Requirements:**
- Python 3.8 or higher
- Chrome or Edge browser

---

## 📖 Quick Start Guide

### For Authenticated Mode (Personal Follows)

1. **Launch** the application
2. **Select** "🔒 Authenticated" mode
2. **Get cookies**:
   - Click the '?' button next to cookie fields
   - Follow the tutorial to copy cookies from Chrome DevTools
   - Required cookies: `skey`, `tfv`, `theme`, `wd`
   - *(Note: Auto-fetch is disabled in .exe version)*
4. **Click** "▶️ Start Export"
5. **Wait** for completion (30-80 seconds per page)
6. **View results**:
   - Click "🌐 Open HTML" to browse in your browser
   - Click "📁 Open Folder" to access XML files

### For Public Mode (No Login)

1. **Launch** the application
2. **Select** "🌐 Public" mode
3. **Click** "▶️ Start Export"
4. **Done!** Results saved to `output/` folder

---

## 📂 Output Files

All generated files are saved in the `output/` folder:

| File | Description | Use Case |
|------|-------------|----------|
| `mangapark_to_mal.xml` | MAL-compatible XML | Import to MyAnimeList via [MAL Import](https://myanimelist.net/import.php) |
| `manga_list.html` | Interactive webpage | Browse, search, filter your collection offline |
| `mal_id_report.txt` | Enrichment report | See which manga matched/failed |

---

## 🔧 Technical Highlights

### Architecture
- **Frontend**: tkinter with custom fullscreen GUI
- **Scraping**: Selenium 4.38.0 (headless Chrome with anti-detection)
- **Parsing**: BeautifulSoup4 for HTML processing
- **API**: Jikan v4 for MAL data (1 req/sec rate limit)
- **Packaging**: PyInstaller for standalone .exe

### Dynamic Content Handling
- **Smart Wait Logic**: 30-80 second wait times for JavaScript-heavy pages
- **Qwik Framework Support**: Handles MangaPark's modern JS framework
- **Spinner Detection**: WebDriverWait for loading spinner disappearance
- **Fallback Mechanisms**: Multiple retry strategies

### Cookie Authentication
- **Manual Entry Only (in .exe)**: DevTools tutorial with clear instructions
- **Auto-Fetch Available (source only)**: browser_cookie3 when running from Python
- **Security Note**: .exe version has auto-fetch disabled due to Windows permission requirements

---

## 🐛 Known Issues & Limitations

### ⏳ **Long Wait Times**
- **Issue**: Scraping takes 30-80 seconds per page
- **Reason**: MangaPark uses Qwik framework with heavy JavaScript rendering
- **Workaround**: Progress messages keep you informed (⏳ indicators)

### 🍪 **Auto-Fetch Not Available in .exe**
- **Issue**: "Auto-Fetch Cookies" button shows error in .exe version
- **Reason**: Windows security restrictions prevent COM access in packaged executables
- **Workaround**: Use manual DevTools method (click '?' button for tutorial) - equally fast and 100% reliable
- **Alternative**: Run from Python source to enable auto-fetch feature

### 🌐 **Browser Requirement**
- **Issue**: Requires Chrome/Edge installed
- **Reason**: Selenium uses ChromeDriver for headless browsing
- **Workaround**: Install Chrome (free) from [google.com/chrome](https://google.com/chrome)

---

## 📊 Performance Stats

- **Scraping Speed**: ~1 minute per page (30-80 manga per page)
- **MAL API**: 1 request/second (respects rate limits)
- **Success Rate**: ~85-95% MAL ID match rate
- **Memory Usage**: ~100-150 MB during execution
- **Executable Size**: 21 MB (optimized, no unnecessary dependencies)

---

## 🙏 Acknowledgments

- **MangaPark**: For providing the manga reading platform
- **MyAnimeList**: For the extensive manga database
- **Jikan API**: For the unofficial MAL API
- **Contributors**: All testers and early users

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **Repository**: https://github.com/N3uralCreativity/MangaParkExporter-
- **Issues**: https://github.com/N3uralCreativity/MangaParkExporter-/issues
- **Documentation**: [README.md](https://github.com/N3uralCreativity/MangaParkExporter-#readme)

---

## 💬 Support

- **Found a bug?** Open an issue on GitHub
- **Have a question?** Check the README or open a discussion
- **Want to contribute?** Fork the repo and submit a PR!

---

## 🎯 Roadmap for Future Releases

- [ ] Add support for Firefox (Selenium)
- [ ] Batch processing for multiple users
- [ ] CSV export format
- [ ] AniList integration
- [ ] Reading status synchronization
- [ ] Automatic updates checker

---

## 📸 Screenshots

### Main Interface
![GUI Overview](examples/screenshot_main.png)
*Fullscreen GUI with 4-step progress tracking*

### Cookie Management
![Cookie Tutorial](examples/screenshot_cookies.png)
*Auto-fetch and manual cookie entry options*

### HTML Output
![HTML Export](examples/screenshot_html.png)
*Beautiful, searchable manga collection viewer*

---

**Thank you for using MangaPark to MAL Exporter! 🎉**

If you find this tool useful, please consider ⭐ starring the repository!
