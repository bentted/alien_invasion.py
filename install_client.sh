#!/bin/bash

# Automatic installation script for Alien Invasion client

echo "Starting installation of Alien Invasion client..."

# Check for Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed. Please install Python3 and try again."
    exit 1
fi

# Check for pip installation
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
if ! pip3 install -r requirements.txt; then
    echo "Error: Failed to install required Python packages."
    exit 1
fi

# Build the executable using PyInstaller
echo "Building the client executable..."
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller is not installed. Installing it now..."
    if ! pip3 install pyinstaller; then
        echo "Error: Failed to install PyInstaller."
        exit 1
    fi
fi

if ! pyinstaller --onefile --noconsole --name Alien_Invasion_Client alien_invasion/Alien_Invasion.py; then
    echo "Error: Failed to build the client executable."
    exit 1
fi

# Move the executable to a convenient location
if [ -f "dist/Alien_Invasion_Client" ]; then
    echo "Moving the executable to the current directory..."
    mv dist/Alien_Invasion_Client ./Alien_Invasion_Client.exe
    echo "Client executable created: Alien_Invasion_Client.exe"
else
    echo "Error: Failed to create the executable."
    exit 1
fi

# Clean up build files
echo "Cleaning up temporary build files..."
rm -rf build dist __pycache__ Alien_Invasion.spec

echo "Installation complete! You can now run the game using ./Alien_Invasion_Client.exe"
