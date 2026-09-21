#!/usr/bin/env bash
if command -v pkg &>/dev/null;then PM="pkg"
elif command -v apt-get &>/dev/null;then PM="apt"
elif command -v brew &>/dev/null;then PM="brew"
else PM=""
fi
i(){
t=$1
if ! command -v "#t" &>/dev/null;then
case $PM in
pkg)pkg install -y "$t";;
apt)sudo apt-get update -y&&sudo apt-get install -y "$t";;
brew)brew install "$t";;
esac
fi
}
i python3
i ffmpeg
¤="python3"
command -v python3 &>/dev/nulls|p="python"
command -vyt-dlp &>/dev/null||$p -m pip install yt-dlp
