import sys
import re
import yt_dlp

# ANSI Color Escape Sequences
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# ASCII Header Banner
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

def check_video_availability(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger(),
        'extract_flat': 'in_playlist',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info is not None
        except Exception:
            return False

def fetch_single_video_qualities(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger(),
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            heights = sorted(list(set(
                f.get('height') for f in formats
                if f.get('height') is not None and f.get('vcodec') != 'none'
            )))
            return heights
        except Exception:
            return None

def get_validated_url():
    while True:
        url = input(f"\n{YELLOW}Enter YouTube URL:{RESET} ").strip()
        if is_valid_yt_url(url):
            return url
        print_green("please provide a yt link")

def main():
    print(BANNER)
    print(f"{CYAN}======================================{RESET}")
    print("  1. Audio (.mp3)")
    print("  2. Video (.mp4)")
    print(f"{CYAN}--------------------------------------{RESET}")
    mode = input(f"{YELLOW}Select format [1/2]:{RESET} ").strip()

    if mode not in ('1', '2'):
        print_green("Invalid format selected.")
        sys.exit(1)

    print(f"\n{CYAN}--------------------------------------{RESET}")
    print("  1. Single Item")
    print("  2. Full Playlist")
    print(f"{CYAN}--------------------------------------{RESET}")
    type_choice = input(f"{YELLOW}Select type [1/2]:{RESET} ").strip()
    if type_choice not in ('1', '2'):
        print_green("Invalid option selected.")
        sys.exit(1)
        
    is_playlist = (type_choice == '2')

    url = get_validated_url()

    if not check_video_availability(url):
        print_green("video doesnt exist, probably private or smth")
        sys.exit(1)

    save_path = "/sdcard/Download/Music" if mode == '1' else "/sdcard/Download"
    media_type = "Song" if mode == '1' else "Video"

    print(f"\n{media_type} found")
    print("Fetching Thumbnail")
    print("Thumbnail downloaded")

    if mode == '1':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{save_path}/%(title)s.%(ext)s',
            'writethumbnails': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
            'noplaylist': not is_playlist,
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
        }
    else:
        target_height = None
        if is_playlist:
            standards = [144, 240, 360, 480, 720, 1080]
            print(f"\n{CYAN}--- Standard Playlist Resolutions ---{RESET}")
            for i, q in enumerate(standards):
                print(f"  {i + 1}. {q}p")
            try:
                choice = int(input(f"\n{YELLOW}Choice:{RESET} ").strip())
                target_height = standards[choice - 1]
            except (ValueError, IndexError):
                target_height = 720
        else:
            print("\nFetching resolutions...")
            qualities = fetch_single_video_qualities(url)
            if not qualities:
                print_green("video doesnt exist, probably private or smth")
                sys.exit(1)
            else:
                print(f"\n{CYAN}--- Available Resolutions ---{RESET}")
                for i, q in enumerate(qualities):
                    print(f"  {i + 1}. {q}p")
                try:
                    choice = int(input(f"\n{YELLOW}Choice:{RESET} ").strip())
                    target_height = qualities[choice - 1]
                except (ValueError, IndexError):
                    target_height = qualities[-1]

        if target_height:
            fmt = f"bestvideo[height<={target_height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={target_height}]+bestaudio/best"
        else:
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

        ydl_opts = {
            'format': fmt,
            'merge_output_format': 'mp4',
            'outtmpl': f'{save_path}/%(title)s.%(ext)s',
            'writethumbnails': True,
            'postprocessors': [
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
            'noplaylist': not is_playlist,
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
        }

    def custom_hook(d):
        if d['status'] == 'finished':
            idx = d.get('playlist_index', 1)
            total = d.get('playlist_autonumber', 1) if is_playlist else 1
            if is_playlist and 'info_dict' in d:
                total = d['info_dict'].get('playlist_count', total)
            print(f"File #{idx}/{total} saved")

    ydl_opts['progress_hooks'] = [custom_hook]

    try:
        print_green("Starting download")
        print_green(f"Saving to {save_path}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception:
        print_green("video doesnt exist, probably private or smth")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
