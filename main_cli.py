import sys
import os
import re
import warnings
import subprocess
import shutil
import yt_dlp

# Suppress SyntaxWarning for escape sequences
warnings.filterwarnings("ignore", category=SyntaxWarning)

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

BANNER = f"""{CYAN}
  /\\_/\\
 ( o.o )
  > ^ <
   ___   _  _____ __      _____ _____
  / __| /_\\|_   _\\ \\    / /_ _|__  /
 | (__ / _ \\ | |   \\ \\/\\/ / | |  / /
  \\___/_/ \\_\\|_|    \\_/\\_/ |___|/___|
{RESET}"""

class QuietLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def print_green(message):
    print(f"{GREEN}{message}{RESET}")

def is_valid_yt_url(url):
    pattern = r'^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?|playlist\?|shorts/)|youtu\.be/)[^\s]+$'
    return re.match(pattern, url) is not None

def get_validated_url():
    while True:
        url = input(f"\n{YELLOW}Enter YouTube URL (or enter 0 to cancel):{RESET} ").strip()
        if url == '0':
            print_green("Operation cancelled.")
            sys.exit(0)
        if is_valid_yt_url(url):
            return url
        print_green("please provide a yt link")

def fetch_playlist_entries(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if not info:
                return []
            if 'entries' in info:
                return [entry['url'] for entry in info['entries'] if entry]
            return [url]
        except Exception:
            return []

def process_thumbnail_only(item_url, is_playlist, index, total, save_path):
    ydl_info_opts = {
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
        try:
            info = ydl.extract_info(item_url, download=False)
            if not info:
                print_green("video doesnt exist, probably private or smth")
                return
        except Exception:
            print_green("video doesnt exist, probably private or smth")
            return

    print("\nImage found")
    
    title = info.get('title', 'thumbnail')
    channel = info.get('uploader') or info.get('channel') or "Unknown Channel"
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    
    print(f"Title: {title}")
    print(f"Creator: {channel}")
    print("Fetching Thumbnail")

    thumb_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writethumbnail': True,
        'outtmpl': safe_title,
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(thumb_opts) as ydl:
        try:
            ydl.download([item_url])
        except Exception:
            pass

    downloaded_thumb = None
    for ext in ['.webp', '.jpg', '.png']:
        if os.path.exists(f"{safe_title}{ext}"):
            downloaded_thumb = f"{safe_title}{ext}"
            break

    png_path = f"{save_path}/{safe_title}.png"
    os.makedirs(save_path, exist_ok=True)

    if downloaded_thumb and os.path.exists(downloaded_thumb):
        subprocess.run(
            ['ffmpeg', '-y', '-i', downloaded_thumb, png_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if os.path.exists(downloaded_thumb) and downloaded_thumb != png_path:
            os.remove(downloaded_thumb)

    print("Thumbnail downloaded")
    print_green(f"Saving to {save_path}")
    print(f"File #{index}/{total} saved")

def process_single_item(item_url, mode, is_playlist, index, total, save_path):
    media_label = "Song" if mode == '1' else "Video"
    
    ydl_info_opts = {
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
        try:
            info = ydl.extract_info(item_url, download=False)
            if not info:
                print_green("video doesnt exist, probably private or smth")
                return
        except Exception:
            print_green("video doesnt exist, probably private or smth")
            return

    print(f"\n{media_label} found")
    
    title = info.get('title', 'media')
    artist_or_creator = info.get('artist') or info.get('uploader') or info.get('channel') or "Unknown"
    
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    png_path = f"{safe_title}.png"

    print(f"Title: {title}")
    if mode == '1':
        print(f"Artist: {artist_or_creator}")
    else:
        print(f"Creator: {artist_or_creator}")

    print("Fetching Thumbnail")
    thumb_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writethumbnail': True,
        'outtmpl': safe_title,
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(thumb_opts) as ydl:
        try:
            ydl.download([item_url])
        except Exception:
            pass

    downloaded_thumb = None
    for ext in ['.webp', '.jpg', '.png']:
        if os.path.exists(f"{safe_title}{ext}"):
            downloaded_thumb = f"{safe_title}{ext}"
            break

    if downloaded_thumb and os.path.exists(downloaded_thumb):
        if mode == '1':
            ffmpeg_cmd = ['ffmpeg', '-y', '-i', downloaded_thumb, '-vf', 'crop=ih:ih', png_path]
        else:
            ffmpeg_cmd = ['ffmpeg', '-y', '-i', downloaded_thumb, png_path]
            
        subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if os.path.exists(downloaded_thumb) and downloaded_thumb != png_path:
            os.remove(downloaded_thumb)

    print("Thumbnail downloaded")

    print_green("Starting download")
    
    os.makedirs(save_path, exist_ok=True)
    temp_media = f"temp_{safe_title}.{'mp3' if mode == '1' else 'mp4'}"
    final_output = f"{save_path}/{safe_title}.{'mp3' if mode == '1' else 'mp4'}"

    if mode == '1':
        dl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'temp_{safe_title}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
        }
    else:
        dl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': temp_media,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
        }

    with yt_dlp.YoutubeDL(dl_opts) as ydl:
        ydl.download([item_url])

    print("Finished download")

    print_green(f"Saving to {save_path}")
    
    if os.path.exists(temp_media):
        if mode == '1' and os.path.exists(png_path):
            cmd = [
                'ffmpeg', '-y', '-i', temp_media, '-i', png_path,
                '-map', '0:0', '-map', '1:0', '-c', 'copy',
                '-id3v2_version', '3',
                '-metadata:s:v', 'title="Album cover"',
                '-metadata:s:v', 'comment="Cover (front)"',
                final_output
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(temp_media)
            os.remove(png_path)
        elif mode == '2' and os.path.exists(png_path):
            cmd = [
                'ffmpeg', '-y', '-i', temp_media, '-i', png_path,
                '-map', '0', '-map', '1',
                '-c', 'copy',
                '-disposition:v:1', 'attached_pic',
                final_output
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(temp_media)
            os.remove(png_path)
        else:
            shutil.move(temp_media, final_output)

    print(f"File #{index}/{total} saved")

def main():
    print(BANNER)
    print(f"{CYAN}======================================{RESET}")
    print(" -1. Settings")
    print("  1. Audio (.mp3)")
    print("  2. Video (.mp4)")
    print("  3. Extract Thumbnail (.png)")
    print("  0. Exit")
    print(f"{CYAN}--------------------------------------{RESET}")
    mode = input(f"{YELLOW}Select option [-1/1/2/3/0]:{RESET} ").strip()

    if mode == '0':
        sys.exit(0)
    elif mode == '-1':
        print_green("\nSettings menu is currently empty.")
        sys.exit(0)
    elif mode not in ('1', '2', '3'):
        print_green("Invalid option selected.")
        sys.exit(1)

    print(f"\n{CYAN}--------------------------------------{RESET}")
    print("  1. Single Item")
    print("  2. Full Playlist")
    print("  0. Cancel")
    print(f"{CYAN}--------------------------------------{RESET}")
    type_choice = input(f"{YELLOW}Select type [1/2/0]:{RESET} ").strip()

    if type_choice == '0':
        print_green("Operation cancelled.")
        sys.exit(0)
    elif type_choice not in ('1', '2'):
        print_green("Invalid option selected.")
        sys.exit(1)

    is_playlist = (type_choice == '2')
    url = get_validated_url()

    if mode == '1':
        save_path = "/sdcard/Download/Music"
    elif mode == '2':
        save_path = "/sdcard/Download"
    else:
        save_path = "/sdcard/Download/Thumbnails"

    if is_playlist:
        items = fetch_playlist_entries(url)
        if not items:
            print_green("video doesnt exist, probably private or smth")
            sys.exit(1)
        total = len(items)
        for idx, item in enumerate(items, 1):
            if mode == '3':
                process_thumbnail_only(item, True, idx, total, save_path)
            else:
                process_single_item(item, mode, True, idx, total, save_path)
    else:
        if mode == '3':
            process_thumbnail_only(url, False, 1, 1, save_path)
        else:
            process_single_item(url, mode, False, 1, 1, save_path)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
