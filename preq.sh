#!/usr/bin/env bash

echo "Checking required dependencies..."

# Detect OS / Package Manager
if command -v pkg &> /dev/null; then
    PKG_MANAGER="pkg"
elif command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
elif command -v brew &> /dev/null; then
    PKG_MANAGER="brew"
else
    PKG_MANAGER="unknown"
fi

install_pkg() {
    TARGET=$1
    if ! command -v "$TARGET" &> /dev/null; then
        echo "Installing missing package: $TARGET"
        case $PKG_MANAGER in
            pkg)
                pkg install -y "$TARGET"
                ;;
            apt)
                sudo apt-get update -y && sudo apt-get install -y "$TARGET"
                ;;
            brew)
                brew install "$TARGET"
                ;;
            *)
                echo "Warning: Unrecognized package manager. Please install $TARGET manually."
                ;;
        esac
    else
        echo "Found: $TARGET"
    fi
}

# Check core tools
install_pkg python3
install_pkg ffmpeg

# Check Python pip / yt-dlp
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null && command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

if ! command -v yt-dlp &> /dev/null; then
    echo "Installing yt-dlp via pip..."
    $PYTHON_CMD -m pip install --break-system-packages yt-dlp 2>/dev/null || $PYTHON_CMD -m pip install yt-dlp
else
    echo "Found: yt-dlp"
fi

echo "All prerequisites checked and installed."
