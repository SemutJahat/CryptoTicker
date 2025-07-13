#!/usr/bin/env python3
"""
Setup script untuk CryptoTicker
"""

import subprocess
import sys
import os

def install_requirements():
    """Install dependensi yang diperlukan"""
    try:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def check_macos():
    """Check jika running di macOS"""
    if sys.platform != "darwin":
        print("Warning: This application is designed for macOS only!")
        return False
    return True

def main():
    print("=== CryptoTicker Setup ===")
    
    # Check macOS
    if not check_macos():
        print("This app requires macOS to run properly.")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("Failed to install requirements. Please check your Python environment.")
        sys.exit(1)
    
    print("\n=== Setup Complete ===")
    print("To run the application:")
    print("python3 main.py")
    print("\nOr to run in background:")
    print("python3 main.py &")
    print("\nThe app will appear in your macOS status bar.")
    print("Right-click on the ticker to access the menu.")

if __name__ == "__main__":
    main() 