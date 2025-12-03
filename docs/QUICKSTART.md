# 🚀 Quick Start Guide

## Installation

### Option 1: Standalone Executable (Recommended)
1. Download `MangaPark-Exporter-V3.exe` from [Releases](https://github.com/N3uralCreativity/MangaParkExporter-/releases/latest)
2. Double-click to run
3. Application opens in full-screen mode

**No installation required!** Just Chrome browser needed for scraping.

### Option 2: Run from Source
```bash
# Clone repository
git clone https://github.com/N3uralCreativity/MangaParkExporter-.git
cd MangaParkExporter-

# Install dependencies
pip install -r requirements.txt

# Run application
python src/desktop_app_v3.py

# Or use launcher
python run.py
```

## 🎯 First Export

1. **Launch Application**
   - Click the `.exe` or run from source
   - App opens maximized

2. **Navigate to Export Page**
   - Click "Export" in the left sidebar

3. **Choose Mode**
   - **Authenticated**: Your personal follows (requires cookies)
   - **Public**: Latest/trending manga (no login needed)

4. **Start Export**
   - Click "Start Export" button
   - Wait for scraping (~2-3 minutes)
   - Files saved to `output/` folder

## 📁 Output Files

After export, you'll find in `output/` folder:
- `mangapark_export_YYYYMMDD_HHMMSS.xml` - Import to MAL
- `mangapark_export_YYYYMMDD_HHMMSS.html` - Visual preview
- `mangapark_export_YYYYMMDD_HHMMSS.json` - Raw data (optional)

## ⚙️ Customization

### Themes
Settings → Appearance → Theme
- **Dark** - Default, easy on eyes
- **Light** - Bright, daytime use

### Font Size
Settings → Appearance → Font Size
- Small, Medium (default), Large

### Animation Speed
Settings → Appearance → Animation Speed
- Slow, Normal (default), Fast

### Export Formats
Settings → Export Settings → Format
- MAL XML + HTML (default)
- XML only
- HTML only
- All formats (XML + HTML + JSON)

## 🔧 Troubleshooting

### White screen on launch
- Wait 10-15 seconds on first launch
- PyQt6 needs time to initialize

### Export failed
- Check Chrome is installed
- For authenticated mode, verify cookies are correct
- Try public mode first to test

### Missing manga
- Some manga don't have MAL IDs
- Enable "Include Unmatched" in settings

### Slow export
- Normal: 2-3 minutes for authenticated
- Public mode only scrapes 1 page (faster)

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/N3uralCreativity/MangaParkExporter-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/N3uralCreativity/MangaParkExporter-/discussions)

## 📚 More Documentation

- [Full README](README.md) - Complete documentation
- [Release Notes](RELEASE_v2.0.0.md) - Version changelog
- [Project Website](https://n3uralcreativity.github.io/MangaParkExporter-/)
