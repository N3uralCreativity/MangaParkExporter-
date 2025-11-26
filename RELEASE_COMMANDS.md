# Commands for GitHub Release

## 1. Clean the repository
```powershell
# Remove debug files and cache
Remove-Item -Path "__pycache__", "*.html", "debug_*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "output\*" -Recurse -Force -ErrorAction SilentlyContinue
```

## 2. Build the executable
```powershell
# Install PyInstaller if not already installed
pip install pyinstaller

# Build the .exe
python build_exe.py
```

The .exe will be in the `dist` folder: `dist/MangaParkExporter.exe`

## 3. Initialize Git repository (if not done yet)
```powershell
git init
git add .
git commit -m "Initial commit: MangaPark to MAL XML Exporter"
```

## 4. Connect to GitHub
```powershell
# Replace with your GitHub repository URL
git remote add origin https://github.com/YOUR_USERNAME/MangaParkExporter.git
git branch -M main
git push -u origin main
```

## 5. Create a GitHub Release
1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `MangaPark to MAL XML Exporter v1.0.0`
5. Description:
```markdown
## MangaPark to MAL XML Exporter v1.0.0

Export your MangaPark follows to MyAnimeList XML format.

### Features
- ✅ GUI with visual progress tracking
- ✅ Automatic MAL ID enrichment via Jikan API
- ✅ Cookie-based authentication
- ✅ Auto-dependency installer
- ✅ Comprehensive error handling

### Download
Download `MangaParkExporter.exe` and run it. No installation needed!

### Requirements
- Windows 10/11
- Chrome browser installed

### Usage
1. Run `MangaParkExporter.exe`
2. Enter your MangaPark cookies (see tutorial button)
3. Click "Start"
4. Find your XML in the `output` folder
```
6. Upload `dist/MangaParkExporter.exe` as an asset
7. Publish release

## 6. Update repository after fixes
```powershell
git add .
git commit -m "Description of changes"
git push
```

## Notes
- Make sure `.gitignore` excludes: `__pycache__/`, `*.pyc`, `debug_*.html`, `dist/`, `build/`, `*.spec`, `output/`
- Test the .exe before releasing
- The .exe will be ~20-30 MB due to embedded Python and dependencies
