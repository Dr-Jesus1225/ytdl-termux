# CATWIZ-ytdl

## Features

- Audio (.mp3, 128 to 320 kbps), video (.mp4, pick your resolution), or thumbnail (.png)
- Single links or full playlists
- Works with `youtube.com`, `music.youtube.com`, `youtu.be`, Shorts, and playlist links
- Link check with title, artist/channel, and duration, plus a confirmation before anything downloads
- Progress bar while downloading
- Keeps metadata, cover art, and chapters in your files
- Built-in uninstaller (Settings menu)

## Install

Copy the command for your system and paste it into your terminal. It first checks what you already have and tells you what is missing and roughly how much it will download. Nothing is installed until you answer `y`.

It needs Git, Python, FFmpeg, and yt-dlp.

### Termux

```bash
pkg install -y curl && bash -c "$(curl -fsSL https://raw.githubusercontent.com/Dr-Jesus1225/ytdl-termux/main/install.sh)"
```

Allow storage access when Termux asks, so downloads can be saved to your phone.

### Debian/Ubuntu

```bash
sudo apt-get update && sudo apt-get install -y curl && bash -c "$(curl -fsSL https://raw.githubusercontent.com/Dr-Jesus1225/ytdl-termux/main/install.sh)"
```

### macOS

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Dr-Jesus1225/ytdl-termux/main/install.sh)"
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/Dr-Jesus1225/ytdl-termux/main/install.ps1 | iex
```

## Usage

On Termux, Debian/Ubuntu, and macOS, type `ytdl` to start.

On Windows there is no `ytdl` shortcut. Run:

```powershell
py "$HOME\CATWIZ-ytdl\main_cli.py"
```

## Where files are saved

| System | Folder |
| --- | --- |
| Termux | `/sdcard/Download` (audio in `Music`, thumbnails in `Thumbnails`) |
| Windows, macOS, Linux | Your `Downloads` folder (audio in `Music`, thumbnails in `Thumbnails`) |

## Uninstall

Open the program, choose `-1. Settings`, then `1. Uninstall CATWIZ-ytdl`.

It removes the program folder and the `ytdl` shortcut. It then lets you choose whether to also remove FFmpeg, yt-dlp, Python, and Git, whether or not this program installed them, and shows roughly how much space that frees. Your downloaded files are never deleted.

Some programs are left out on purpose. On Debian/Ubuntu, Python is not offered, because system tools depend on it. On Debian/Ubuntu and macOS, yt-dlp lives inside the program folder and goes away with it.

## Updating

Run the install command again and it will pull the latest version. If downloads stop working, update yt-dlp by running the install command again.

## Disclaimer

Only download content you have the right to download, and follow YouTube's terms of service.
