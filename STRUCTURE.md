# MangaPark to MAL Exporter - Project Structure

## Main Application
- `mangapark_gui.py` - Main GUI application (run this!)
- `build_exe.py` - Script to build standalone .exe

## Configuration
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules
- `LICENSE` - MIT License
- `README.md` - Full documentation

## Folders
- `output/` - Generated files (XML, HTML) - created automatically
- `legacy/` - Old command-line scripts (kept for reference)
- `examples/` - Example output files

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python mangapark_gui.py
   ```

3. **Build .exe:**
   ```bash
   python build_exe.py
   ```

## For GitHub Publication

Files to commit:
- ✅ `mangapark_gui.py`
- ✅ `build_exe.py`
- ✅ `requirements.txt`
- ✅ `README.md`
- ✅ `LICENSE`
- ✅ `.gitignore`
- ✅ `STRUCTURE.md` (this file)

Files to ignore (already in .gitignore):
- ❌ `output/` folder
- ❌ `examples/` folder (optional, can include for demo)
- ❌ `legacy/` folder (optional, can include for reference)
- ❌ `.vscode/`, `__pycache__/`, etc.

## Git Commands

```bash
# Initialize git (if not already)
git init

# Add files
git add mangapark_gui.py build_exe.py requirements.txt README.md LICENSE .gitignore

# Commit
git commit -m "Initial commit: MangaPark to MAL Exporter v1.0"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/MangaParkExporter.git

# Push
git push -u origin main
```

## Version History

### v1.0.0 (2025-11-26)
- Initial release
- GUI application with dual scraping modes
- MAL ID enrichment via Jikan API
- XML and HTML export
- Standalone .exe builder
- Auto-fetch cookies from Chrome
