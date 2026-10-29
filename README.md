# CATWIZ-ytdl

A simple terminal menu for downloading YouTube audio, video, and thumbnails, built on [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Features

- Audio (.mp3, 128 to 320 kbps), video (.mp4, pick your resolution), or thumbnail (.png)
- Single links or full playlists
- Works with `youtube.com`, `music.youtube.com`, `youtu.be`, Shorts, and playlist links
- Link check with title, artist/channel, and duration, plus a confirmation before anything downloads
- Progress bar while downloading
- Keeps metadata, cover art, and chapters in your files

## Install

Copy the command for your system and paste it into your terminal. It installs everything it needs (git, Python, ffmpeg, yt-dlp), downloads the project, and starts it.

### Termux

Run `termux-setup-storage` first and allow storage access, then:

```bash
pkg update -y&&command -v git &>/dev/null||pkg install git -y&&[ -d "$HOME/CATWIZ-ytdl" ]||git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME/CATWIZ-ytdl"&&bash "$HOME/CATWIZ-ytdl/preq.sh"&&echo -e "#!/data/data/com.termux/files/usr/bin/bash\npython \"$HOME/CATWIZ-ytdl/main_cli.py\"" > $PREFIX/bin/ytdl&&chmod +x $PREFIX/bin/ytdl&&ytdl
```

### Debian/Ubuntu

```bash
sudo apt update -y&&sudo apt install -y git python3 python3-pip python3-venv ffmpeg&&if [ -d "$HOME/CATWIZ-ytdl" ];then git -C "$HOME/CATWIZ-ytdl" pull;else git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME/CATWIZ-ytdl";fi&&python3 -m venv "$HOME/CATWIZ-ytdl/.venv"&&"$HOME/CATWIZ-ytdl/.venv/bin/pip" install -U yt-dlp&&printf '#!/usr/bin/env bash\nexec "%s/CATWIZ-ytdl/.venv/bin/python" "%s/CATWIZ-ytdl/main_cli.py" "$@"\n' "$HOME" "$HOME"|sudo tee /usr/local/bin/ytdl >/dev/null&&sudo chmod +x /usr/local/bin/ytdl&&ytdl
```

### macOS

```bash
command -v brew &>/dev/null||/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)";for b in /opt/homebrew/bin/brew /usr/local/bin/brew;do [ -x "$b" ]&&eval "$("$b" shellenv)";done;brew install git python ffmpeg&&if [ -d "$HOME/CATWIZ-ytdl" ];then git -C "$HOME/CATWIZ-ytdl" pull;else git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME/CATWIZ-ytdl";fi&&python3 -m venv "$HOME/CATWIZ-ytdl/.venv"&&"$HOME/CATWIZ-ytdl/.venv/bin/pip" install -U yt-dlp&&sudo mkdir -p /usr/local/bin&&printf '#!/usr/bin/env bash\nexec "%s/CATWIZ-ytdl/.venv/bin/python" "%s/CATWIZ-ytdl/main_cli.py" "$@"\n' "$HOME" "$HOME"|sudo tee /usr/local/bin/ytdl >/dev/null&&sudo chmod +x /usr/local/bin/ytdl&&ytdl
```

### Windows PowerShell

```powershell
$need=@{git='Git.Git';py='Python.Python.3.12';ffmpeg='Gyan.FFmpeg'};foreach($k in $need.Keys){if(-not(Get-Command $k -ErrorAction SilentlyContinue)){winget install -e --id $need[$k] --accept-package-agreements --accept-source-agreements}};$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User');if(-not(Test-Path "$HOME\CATWIZ-ytdl")){git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME\CATWIZ-ytdl"}else{git -C "$HOME\CATWIZ-ytdl" pull};cd "$HOME\CATWIZ-ytdl";py -m pip install -U yt-dlp;py main_cli.py
```

## Usage

On Termux, Debian/Ubuntu, and macOS, type `ytdl` to start.

On Windows, there is no `ytdl` shortcut. Run:

```powershell
cd "$HOME\CATWIZ-ytdl"; py main_cli.py
```

## Where files are saved

| System | Folder |
| --- | --- |
| Termux | `/sdcard/Download` (audio in `Music`, thumbnails in `Thumbnails`) |
| Windows, macOS, Linux | Your `Downloads` folder (audio in `Music`, thumbnails in `Thumbnails`) |

## Updating

On Debian/Ubuntu, macOS, and Windows, run the install command again and it will pull the latest version. On Termux:

```bash
cd ~/CATWIZ-ytdl && git pull
```

If downloads stop working, update yt-dlp (`pip install -U yt-dlp`, or inside `~/CATWIZ-ytdl/.venv` on Debian/Ubuntu and macOS).

## Disclaimer

Only download content you have the right to download, and follow YouTube's terms of service.
