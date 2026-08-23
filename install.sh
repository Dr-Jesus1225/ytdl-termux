#!/bin/sh
echo "Installing dependencies..."
pkg update && pkg upgrade -y
pkg install python ffmpeg quickjs -y
pip install --upgrade yt-dlp

echo "Setting up ytdl executable..."
mkdir -p $PREFIX/bin
cp ytdl $PREFIX/bin/ytdl
chmod +x $PREFIX/bin/ytdl

termux-setup-storage

echo "Setup complete! Type 'ytdl' to run."
