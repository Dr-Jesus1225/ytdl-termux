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
    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        url = input(f"\n{YELLOW}Enter YouTube URL (or enter 0 to cancel):{RESET} ").strip()
        if url == '0':
            print_green("Operation cancelled.")
            sys.exit(0)
        if is_valid_yt_url(url):
            return url
        attempts += 1
        if attempts < max_attempts:
            print_green("please provide a yt link")
        else:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)

def fetch_info(url):
    ydl_info_opts = {
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
        try:
            return ydl.extract_info(url, download=False)
        except Exception:
            return None

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

def select_video_quality(info, is_playlist):
    if is_playlist:
        options = [
            ("360p", "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]"),
            ("480p", "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"),
            ("720p", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"),
            ("1080p", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"),
            ("Best Quality", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best")
        ]
    else:
        heights = set()
        if info and 'formats' in info:
            for f in info['formats']:
                h = f.get('height')
                if h and isinstance(h, int) and h >= 144:
                    heights.add(h)
        sorted_h = sorted(list(heights))
        if not sorted_h:
            sorted_h = [360, 480, 720, 1080]
        options = [(f"{h}p", f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}]") for h in sorted_h]
        options.append(("Best Quality", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"))

    print(f"\n{CYAN}--------------------------------------{RESET}")
    print(" Select Video Quality:")
    for idx, (label, _) in enumerate(options, 1):
        print(f"  {idx}. {label}")
    print("  0. Cancel")
    print(f"{CYAN}--------------------------------------{RESET}")

    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        choice = input(f"{YELLOW}Select option [1-{len(options)}/0]:{RESET} ").strip()
        if choice == '0':
            print_green("Operation cancelled.")
            sys.exit(0)
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1][1]
        attempts += 1
        if attempts < max_attempts:
            print_green("Invalid selection.")
        else:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)

def select_audio_quality(info, is_playlist):
    options = [
        ("128 kbps", "128"),
        ("192 kbps", "192"),
        ("256 kbps", "256"),
        ("320 kbps (Best)", "320")
    ]
    print(f"\n{CYAN}--------------------------------------{RESET}")
    print(" Select Audio Quality:")
    for idx, (label, _) in enumerate(options, 1):
        print(f"  {idx}. {label}")
    print("  0. Cancel")
    print(f"{CYAN}--------------------------------------{RESET}")

    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        choice = input(f"{YELLOW}Select option [1-{len(options)}/0]:{RESET} ").strip()
        if choice == '0':
            print_green("Operation cancelled.")
            sys.exit(0)
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1][1]
        attempts += 1
        if attempts < max_attempts:
            print_green("Invalid selection.")
        else:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)

def select_photo_quality(info, is_playlist):
    if is_playlist or not info or 'thumbnails' not in info or not info['thumbnails']:
        options = [
            ("Standard Quality", "standard"),
            ("High Quality", "hq"),
            ("Best Available", "best")
        ]
    else:
        dims = []
        for t in info['thumbnails']:
            w = t.get('width')
            h = t.get('height')
            if w and h:
                dims.append((w, h, t.get('url')))
        
        dims = sorted(list(set(dims)), key=lambda x: x[0] * x[1])
        
        if not dims:
            options = [
                ("Standard Quality", "standard"),
                ("High Quality", "hq"),
                ("Best Available", "best")
            ]
        else:
            options = [(f"{w}x{h}", url) for w, h, url in dims]
            options.append(("Best Available", "best"))

    print(f"\n{CYAN}--------------------------------------{RESET}")
    print(" Select Photo Resolution (LxB):")
    for idx, (label, _) in enumerate(options, 1):
        print(f"  {idx}. {label}")
    print("  0. Cancel")
    print(f"{CYAN}--------------------------------------{RESET}")

    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        choice = input(f"{YELLOW}Select option [1-{len(options)}/0]:{RESET} ").strip()
        if choice == '0':
            print_green("Operation cancelled.")
            sys.exit(0)
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1][1]
        attempts += 1
        if attempts < max_attempts:
            print_green("Invalid selection.")
        else:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)

def process_thumbnail_only(item_url, is_playlist, index, total, save_path, photo_quality, pre_info=None):
    info = pre_info or fetch_info(item_url)
    if not info:
        print_green("video doesnt exist, probably private or smth")
        return

    print("\nImage found")
    
    title = info.get('title', 'thumbnail')
    channel = info.get('uploader') or info.get('channel') or "Unknown Channel"
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    
    print(f"Title: {title}")
    print(f"Creator: {channel}")
    print("Fetching Thumbnail")

    downloaded_thumb = None

    if photo_quality and photo_quality.startswith("http"):
        import urllib.request
        temp_img = f"{safe_title}_raw.jpg"
        try:
            urllib.request.urlretrieve(photo_quality, temp_img)
            downloaded_thumb = temp_img
        except Exception:
            pass

    if not downloaded_thumb:
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

def process_single_item(item_url, mode, is_playlist, index, total, save_path, selected_format, pre_info=None):
    media_label = "Song" if mode == '1' else "Video"
    
    info = pre_info or fetch_info(item_url)
    if not info:
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
                'preferredquality': selected_format,
            }],
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
        }
    else:
        dl_opts = {
            'format': selected_format,
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
    
    attempts = 0
    max_attempts = 3
    mode = None
    while attempts < max_attempts:
        mode = input(f"{YELLOW}Select option [-1/1/2/3/0]:{RESET} ").strip()
        if mode in ('-1', '0', '1', '2', '3'):
            break
        attempts += 1
        if attempts < max_attempts:
            print_green("Invalid option selected.")
        else:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)

    if mode == '0':
        sys.exit(0)
    elif mode == '-1':
        print_green("\nSettings menu is currently empty.")
        sys.exit(0)

    print(f"\n{CYAN}--------------------------------------{RESET}")
    print("  1. Single Item")
    print("  2. Full Playlist")
    print("  0. Cancel")
    print(f"{CYAN}--------------------------------------{RESET}")
    
    attempts = 0
    type_choice = None
    while attempts < max_attempts:
        type_choice = input(f"{YELLOW}Select type [1/2/0]:{RESET} ").strip()
        if type_choice in ('0', '1', '2'):
            break
        attempts += 1
        if attempts < max_attempts:
            print_green("Invalid option selected.")
        else:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)

    if type_choice == '0':
        print_green("Operation cancelled.")
        sys.exit(0)

    is_playlist = (type_choice == '2')
    url = get_validated_url()

    info = None
    playlist_items = None

    if is_playlist:
        print_green("Checking playlist...")
        playlist_items = fetch_playlist_entries(url)
        if not playlist_items:
            print_green("video doesnt exist, probably private or smth")
            sys.exit(1)
    else:
        print_green("Fetching video info...")
        info = fetch_info(url)
        if not info:
            print_green("video doesnt exist, probably private or smth")
            sys.exit(1)

    if mode == '1':
        selected_quality = select_audio_quality(info, is_playlist)
        save_path = "/sdcard/Download/Music"
    elif mode == '2':
        selected_quality = select_video_quality(info, is_playlist)
        save_path = "/sdcard/Download"
    else:
        selected_quality = select_photo_quality(info, is_playlist)
        save_path = "/sdcard/Download/Thumbnails"

    if is_playlist:
        total = len(playlist_items)
        for idx, item in enumerate(playlist_items, 1):
            if mode == '3':
                process_thumbnail_only(item, True, idx, total, save_path, selected_quality)
            else:
                process_single_item(item, mode, True, idx, total, save_path, selected_quality)
    else:
        if mode == '3':
            process_thumbnail_only(url, False, 1, 1, save_path, selected_quality, pre_info=info)
        else:
            process_single_item(url, mode, False, 1, 1, save_path, selected_quality, pre_info=info)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
