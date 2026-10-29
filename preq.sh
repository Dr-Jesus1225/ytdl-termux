#!/usr/bin/env bash
if command -v pkg &>/dev/null;then PM="pkg"
elif command -v apt-get &>/dev/null;then PM="apt"
elif command -v brew &>/dev/null;then PM="brew"
else PM=""
fi

# i <command> <termux pkg> <apt pkg> <brew pkg>
i(){
cmd=$1
case $PM in
pkg)name=$2;;
apt)name=$3;;
brew)name=$4;;
esac
if ! command -v "$cmd" &>/dev/null;then
case $PM in
pkg)pkg install -y "$name";;
apt)sudo apt-get update -y&&sudo apt-get install -y "$name";;
brew)brew install "$name";;
esac
fi
}

i python3 python python3 python
i ffmpeg ffmpeg ffmpeg ffmpeg
[ "$PM" = "apt" ]&&i pip3 python3-pip python3-pip python3-pip

p="python3"
command -v python3 &>/dev/null||p="python"
command -v yt-dlp &>/dev/null||$p -m pip install yt-dlp||$p -m pip install --break-system-packages yt-dlp
