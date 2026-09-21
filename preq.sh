#!/data/data/com.termux/files/usr/bin/bash
echo "Checking required dependencies..."
REQUIRED_PKGS=("python" "ffmpeg")
for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! command -v "$pkg" &> /dev/null; then
        echo "Installing missing package: $pkg"
        pkg install -y "$pkg"
    else
        echo "Found: $pkg"
    fi
done
if ! command -v yt-dlp &> /dev/null; then
    echo "Installing missing Python package: yt-dlp"
    pip install yt-dlp
else
    echo "Found: yt-dlp"
fi
echo "All prerequisites are installed."
