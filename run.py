"""
Quick launcher for MangaPark Exporter V2
Run this from project root to start the application
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run
from src.desktop_app_v3 import main

if __name__ == '__main__':
    main()
