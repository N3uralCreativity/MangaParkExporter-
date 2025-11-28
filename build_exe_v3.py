"""
Build script for creating standalone .exe for Desktop App V3
Automatically installs dependencies and creates executable with embedded HTML
"""
import subprocess
import sys
import os

def install_dependencies():
    """Install required packages"""
    print("=" * 60)
    print("STEP 1: Installing dependencies...")
    print("=" * 60)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Dependencies installed successfully!\n")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    
    return True

def install_pyqt6():
    """Install PyQt6 and WebEngine"""
    print("=" * 60)
    print("STEP 2: Installing PyQt6 and WebEngine...")
    print("=" * 60)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "PyQt6", "PyQt6-WebEngine"
        ])
        print("✓ PyQt6 installed successfully!\n")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install PyQt6: {e}")
        return False
    
    return True

def install_pyinstaller():
    """Install PyInstaller"""
    print("=" * 60)
    print("STEP 3: Installing PyInstaller...")
    print("=" * 60)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "pyinstaller"
        ])
        print("✓ PyInstaller installed successfully!\n")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install PyInstaller: {e}")
        return False
    
    return True

def build_exe():
    """Build the executable"""
    print("=" * 60)
    print("STEP 4: Building executable...")
    print("=" * 60)
    
    # Check if HTML file exists
    if not os.path.exists("mangapark_gui_web.html"):
        print("✗ Error: mangapark_gui_web.html not found!")
        return False
    
    # PyInstaller command for V3
    # Include the HTML file as data, and all necessary PyQt6 components
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "MangaPark-Exporter-V3",
        "--add-data", "mangapark_gui_web.html;.",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.QtWebEngineWidgets",
        "--hidden-import", "PyQt6.QtWebChannel",
        "--hidden-import", "PyQt6.QtWebEngineCore",
        "--hidden-import", "selenium",
        "--hidden-import", "selenium.webdriver",
        "--hidden-import", "selenium.webdriver.chrome",
        "--hidden-import", "selenium.webdriver.chrome.options",
        "--hidden-import", "bs4",
        "--hidden-import", "requests",
        "--hidden-import", "xml.etree.ElementTree",
        "--hidden-import", "difflib",
        "--collect-submodules", "PyQt6",
        "--collect-submodules", "selenium",
        "--noconfirm",
        "--icon", "NONE",
        "desktop_app_v3.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ Executable built successfully!")
        print(f"\n{'=' * 60}")
        print("BUILD COMPLETE!")
        print('=' * 60)
        print(f"\nYour executable is located at:")
        print(f"  {os.path.abspath('dist/MangaPark-Exporter-V3.exe')}")
        print(f"\nThe .exe includes:")
        print(f"  ✓ Complete frontend (HTML/CSS/JS)")
        print(f"  ✓ Complete backend (Python/PyQt6)")
        print(f"  ✓ All dependencies bundled")
        print(f"\nYou can distribute this .exe file without any other dependencies!")
        print("The recipient only needs Chrome installed for Selenium to work.")
        print(f"\nNote: First launch may take 10-15 seconds as PyQt6 initializes.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to build executable: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print(" " * 8 + "MangaPark Exporter V3 - Build Script")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Install all required dependencies")
    print("  2. Install PyQt6 and WebEngine")
    print("  3. Install PyInstaller")
    print("  4. Build a standalone .exe file with embedded HTML")
    print()
    
    input("Press Enter to continue...")
    print()
    
    # Step 1: Install dependencies
    if not install_dependencies():
        input("\nPress Enter to exit...")
        return
    
    # Step 2: Install PyQt6
    if not install_pyqt6():
        input("\nPress Enter to exit...")
        return
    
    # Step 3: Install PyInstaller
    if not install_pyinstaller():
        input("\nPress Enter to exit...")
        return
    
    # Step 4: Build executable
    if not build_exe():
        input("\nPress Enter to exit...")
        return
    
    print("\n✓ All steps completed successfully!")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
