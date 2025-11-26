"""
Build script for creating standalone .exe
Automatically installs dependencies and creates executable
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

def install_pyinstaller():
    """Install PyInstaller"""
    print("=" * 60)
    print("STEP 2: Installing PyInstaller...")
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
    print("STEP 3: Building executable...")
    print("=" * 60)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "MangaPark-to-MAL-Exporter",
        "--add-data", "requirements.txt;.",
        "--hidden-import", "browser_cookie3",
        "--hidden-import", "selenium",
        "--hidden-import", "bs4",
        "--hidden-import", "requests",
        "--collect-all", "browser_cookie3",
        "--noconfirm",
        "mangapark_gui.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ Executable built successfully!")
        print(f"\n{'=' * 60}")
        print("BUILD COMPLETE!")
        print('=' * 60)
        print(f"\nYour executable is located at:")
        print(f"  {os.path.abspath('dist/MangaPark-to-MAL-Exporter.exe')}")
        print(f"\nYou can distribute this .exe file without any other dependencies!")
        print("The recipient only needs Chrome installed for Selenium to work.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to build executable: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print(" " * 10 + "MangaPark Exporter - Build Script")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Install all required dependencies")
    print("  2. Install PyInstaller")
    print("  3. Build a standalone .exe file")
    print()
    
    input("Press Enter to continue...")
    print()
    
    # Step 1: Install dependencies
    if not install_dependencies():
        return
    
    # Step 2: Install PyInstaller
    if not install_pyinstaller():
        return
    
    # Step 3: Build executable
    if not build_exe():
        return
    
    print("\n✓ All steps completed successfully!")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
