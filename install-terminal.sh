#!/bin/sh
echo "Installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip ffmpeg -y
pip install --upgrade yt-dlp --break-system-packages

echo "Setting up ytdl executable..."
sudo mkdir -p /usr/local/bin
sudo cp ytdl /usr/local/bin/ytdl
sudo chmod +x /usr/local/bin/ytdl

echo "Setup complete! Type 'ytdl' to run."
