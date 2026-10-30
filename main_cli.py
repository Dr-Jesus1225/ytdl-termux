import sys
import os
import re
import warnings
import subprocess
import shutil
import tempfile
import importlib.util
import glob
from datetime import datetime
import yt_dlp

if os.name == 'nt':
    os.system('')  # enables ANSI colors in Windows terminals
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Suppress SyntaxWarning for escape sequences
warnings.filterwarnings("ignore", category=SyntaxWarning)

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
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

def get_download_dir():
    if os.path.isdir('/sdcard/Download'):
        return '/sdcard/Download'
    return os.path.join(os.path.expanduser('~'), 'Downloads')

def check_ffmpeg():
    if shutil.which('ffmpeg') is None:
        print(f"{RED}ffmpeg was not found.{RESET}")
        print("Install it, then reopen this terminal:")
        print("  Windows: winget install Gyan.FFmpeg")
        print("  Termux:  pkg install ffmpeg")
        print("  Debian:  sudo apt install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        sys.exit(1)

def clean_filename(title):
    name = re.sub(r'[\\/*?:"<>|]', "", title).strip(' .')[:150].strip(' .')
    return name or 'media'

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
ERROR_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'errors.log')

def log_error(context, detail):
    """Append a line to errors.log so problems can be reported later."""
    try:
        with open(ERROR_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {context}: {detail}\n")
    except OSError:
        pass

def short_reason(err, limit=140):
    text = ANSI_RE.sub('', str(err)).strip()
    text = re.sub(r'^(ERROR:\s*)+', '', text)
    line = text.splitlines()[0] if text else 'unknown error'
    return line[:limit]

def run_ffmpeg(cmd):
    """Run ffmpeg and return (ok, reason). The reason is the last line ffmpeg printed on failure."""
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           text=True, errors='replace')
    except FileNotFoundError:
        return False, 'ffmpeg not found'
    except OSError as e:
        return False, short_reason(e)
    if r.returncode == 0:
        return True, ''
    lines = [l.strip() for l in (r.stderr or '').splitlines() if l.strip()]
    return False, (lines[-1][:140] if lines else f'exit code {r.returncode}')

def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        print(f"{RED}Can't write to {path} ({short_reason(e)}){RESET}")
        if os.path.isdir('/data/data/com.termux'):
            print("On Termux, run termux-setup-storage and allow storage access.")
        log_error('save folder', f"{path}: {e}")
        return False

def safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass

def cleanup_partials(safe_title, png_path):
    for p in glob.glob(glob.escape(f"temp_{safe_title}") + ".*"):
        safe_remove(p)
    safe_remove(png_path)
    for ext in ('.webp', '.jpg', '.png'):
        safe_remove(f"{safe_title}{ext}")

def item_failed(index, total, why, context):
    print(f"{RED}File #{index}/{total} failed: {why}{RESET}")
    log_error(context, why)
    return False

def download_thumbnail_file(item_url, safe_title):
    thumb_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writethumbnail': True,
        'outtmpl': safe_title.replace('%', '%%'),
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(thumb_opts) as ydl:
        try:
            ydl.download([item_url])
        except Exception as e:
            log_error(item_url, f"thumbnail download failed: {e}")
    for ext in ['.webp', '.jpg', '.png']:
        if os.path.exists(f"{safe_title}{ext}"):
            return f"{safe_title}{ext}"
    return None

def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        if not total:
            return
        pct = d.get('downloaded_bytes', 0) / total
        filled = int(pct * 20)
        bar = '█' * filled + '░' * (20 - filled)
        speed = d.get('speed')
        sp = f"{speed / 1048576:.1f} MB/s" if speed else "--"
        eta = d.get('eta')
        eta_s = f"{eta}s" if eta is not None else "--"
        print(f"\r{GREEN}[{bar}] {pct * 100:5.1f}%{RESET} {sp} ETA {eta_s}   ", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\r{GREEN}[{'█' * 20}] 100.0%{RESET}" + " " * 25)

def is_valid_yt_url(url):
    pattern = r'^(https?://)?((www|m|music)\.)?(youtube\.com/(watch\?|playlist\?|shorts/|live/|embed/)|youtu\.be/)[^\s]+$'
    return re.match(pattern, url) is not None

def format_duration(sec):
    if not sec:
        return "Unknown"
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, sc = divmod(rem, 60)
    return f"{h}:{m:02d}:{sc:02d}" if h else f"{m}:{sc:02d}"

def ask_proceed():
    while True:
        ans = input(f"\n{YELLOW}Proceed? [y/n]:{RESET} ").strip().lower()
        if ans in ('y', 'n'):
            return ans == 'y'

def fetch_playlist_info(url):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'logger': QuietLogger(),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception:
            return None
    if not info:
        return None
    name = info.get('title') or 'Unknown'
    creator = info.get('uploader') or info.get('channel')
    if 'entries' in info:
        items = [e['url'] for e in info['entries'] if e and e.get('url')]
    else:
        items = [url]
    return name, creator, items

def get_validated_url(is_playlist, mode):
    attempts = 0
    max_attempts = 3
    while True:
        url = input(f"\n{YELLOW}Enter YouTube URL (or enter 0 to cancel):{RESET} ").strip()
        if url == '0':
            print_green("Operation cancelled.")
            sys.exit(0)
        print("\nChecking link...")
        result = None
        if not is_valid_yt_url(url):
            print(f"{RED}Not a valid YouTube link{RESET}")
            print("  Expected: youtube.com, music.youtube.com, youtu.be, shorts, or playlist")
        else:
            if not url.startswith('http'):
                url = 'https://' + url
            print_green("Valid YouTube link")
            if is_playlist:
                data = fetch_playlist_info(url)
                if data and data[2]:
                    name, creator, items = data
                    print_green("Playlist found")
                    print(f"  Name:    {name}")
                    if creator:
                        print(f"  Creator: {creator}")
                    print(f"  Items:   {len(items)}")
                    result = (url, None, items)
            else:
                info = fetch_info(url)
                if info:
                    print_green("Video found")
                    print(f"  Title:    {info.get('title', 'Unknown')}")
                    who = info.get('artist') or info.get('uploader') or info.get('channel') or 'Unknown'
                    print(f"  {'Artist' if mode == '1' else 'Channel'}:".ljust(11) + f" {who}")
                    if mode != '3':
                        print(f"  Duration: {format_duration(info.get('duration'))}")
                    result = (url, info, None)
            if result is None:
                print(f"{RED}Video not available (private, deleted, or region-locked){RESET}")
        if result:
            attempts = 0
            if ask_proceed():
                return result
            continue
        attempts += 1
        if attempts >= max_attempts:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)
        print(f"Attempt {attempts}/{max_attempts}")

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
        return item_failed(index, total, 'video not available (private, deleted, or region-locked)', item_url)

    title = info.get('title', 'thumbnail')
    safe_title = clean_filename(title)
    if is_playlist:
        print(f"\n[{index}/{total}] {title}")
    else:
        print()
    print("Fetching thumbnail...")

    downloaded_thumb = None

    if photo_quality and photo_quality.startswith("http"):
        import urllib.request
        temp_img = f"{safe_title}_raw.jpg"
        try:
            urllib.request.urlretrieve(photo_quality, temp_img)
            downloaded_thumb = temp_img
        except Exception as e:
            log_error(item_url, f"direct thumbnail download failed: {e}")

    if not downloaded_thumb:
        downloaded_thumb = download_thumbnail_file(item_url, safe_title)

    if not downloaded_thumb or not os.path.exists(downloaded_thumb):
        return item_failed(index, total, 'could not download the thumbnail', item_url)

    if not ensure_dir(save_path):
        safe_remove(downloaded_thumb)
        return item_failed(index, total, 'save folder is not writable', item_url)

    png_path = os.path.join(save_path, f"{safe_title}.png")
    ok, why = run_ffmpeg(['ffmpeg', '-y', '-i', downloaded_thumb, png_path])
    if ok:
        safe_remove(downloaded_thumb)
        print("Thumbnail downloaded")
        print_green(f"Saving to {save_path}")
        print(f"File #{index}/{total} saved")
        return True

    # Conversion failed: keep the original image instead of losing it
    safe_remove(png_path)
    log_error(item_url, f"png conversion failed: {why}")
    ext = os.path.splitext(downloaded_thumb)[1] or '.jpg'
    kept = os.path.join(save_path, f"{safe_title}{ext}")
    try:
        shutil.move(downloaded_thumb, kept)
    except OSError as e:
        safe_remove(downloaded_thumb)
        return item_failed(index, total, f"could not convert or keep the thumbnail ({short_reason(e)})", item_url)
    print(f"{YELLOW}PNG conversion failed ({why}){RESET}")
    print_green(f"Saved the original image instead: {kept}")
    print(f"File #{index}/{total} saved")
    return True

def process_single_item(item_url, mode, is_playlist, index, total, save_path, selected_format, pre_info=None):
    info = pre_info or fetch_info(item_url)
    if not info:
        return item_failed(index, total, 'video not available (private, deleted, or region-locked)', item_url)

    title = info.get('title', 'media')
    safe_title = clean_filename(title)
    png_path = f"{safe_title}.png"
    ext = 'mp3' if mode == '1' else 'mp4'
    temp_media = f"temp_{safe_title}.{ext}"
    final_output = os.path.join(save_path, f"{safe_title}.{ext}")

    if is_playlist:
        print(f"\n[{index}/{total}] {title}")
    else:
        print()

    # ---- thumbnail / cover art ----
    print("Fetching thumbnail...")
    have_cover = False
    downloaded_thumb = download_thumbnail_file(item_url, safe_title)
    if downloaded_thumb and os.path.exists(downloaded_thumb):
        if downloaded_thumb == png_path:
            # input and output would be the same file, so move the input aside first
            moved = f"{safe_title}_src.png"
            try:
                os.replace(downloaded_thumb, moved)
                downloaded_thumb = moved
            except OSError:
                pass
        if mode == '1':
            ffmpeg_cmd = ['ffmpeg', '-y', '-i', downloaded_thumb, '-vf', 'crop=ih:ih', png_path]
        else:
            ffmpeg_cmd = ['ffmpeg', '-y', '-i', downloaded_thumb, png_path]
        ok, why = run_ffmpeg(ffmpeg_cmd)
        safe_remove(downloaded_thumb)
        if ok and os.path.exists(png_path):
            have_cover = True
            print("Thumbnail downloaded")
        else:
            safe_remove(png_path)
            print(f"{YELLOW}Thumbnail conversion failed ({why or 'unknown error'}), continuing without cover art{RESET}")
            log_error(item_url, f"thumbnail conversion failed: {why}")
    else:
        print(f"{YELLOW}No thumbnail available, continuing without cover art{RESET}")

    # ---- download ----
    if not ensure_dir(save_path):
        cleanup_partials(safe_title, png_path)
        return item_failed(index, total, 'save folder is not writable', item_url)

    print_green("Starting download")
    out_base = f"temp_{safe_title}".replace('%', '%%')
    if mode == '1':
        dl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_base + '.%(ext)s',
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': selected_format},
                {'key': 'FFmpegMetadata', 'add_metadata': True},
            ],
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
        }
    else:
        dl_opts = {
            'format': selected_format,
            'outtmpl': out_base + '.mp4',
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegMetadata', 'add_metadata': True, 'add_chapters': True}],
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
        }

    try:
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            ydl.download([item_url])
    except Exception as e:
        print()
        cleanup_partials(safe_title, png_path)
        return item_failed(index, total, f"download failed ({short_reason(e)})", item_url)

    print("Finished download")

    if not os.path.exists(temp_media):
        cleanup_partials(safe_title, png_path)
        return item_failed(index, total, 'the download finished but the file is missing (is ffmpeg working?)', item_url)

    # ---- save, with cover art when possible ----
    print_green(f"Saving to {save_path}")
    cover_done = False
    cover_failed = False
    if have_cover and os.path.exists(png_path):
        if mode == '1':
            cmd = [
                'ffmpeg', '-y', '-i', temp_media, '-i', png_path,
                '-map', '0:0', '-map', '1:0', '-c', 'copy',
                '-id3v2_version', '3',
                '-metadata:s:v', 'title="Album cover"',
                '-metadata:s:v', 'comment="Cover (front)"',
                final_output
            ]
        else:
            cmd = [
                'ffmpeg', '-y', '-i', temp_media, '-i', png_path,
                '-map', '0', '-map', '1',
                '-c', 'copy',
                '-disposition:v:1', 'attached_pic',
                final_output
            ]
        ok, why = run_ffmpeg(cmd)
        if ok and os.path.exists(final_output):
            cover_done = True
            safe_remove(temp_media)
        else:
            cover_failed = True
            safe_remove(final_output)  # remove the broken partial file
            print(f"{YELLOW}Adding cover art failed ({why or 'unknown error'}){RESET}")
            log_error(item_url, f"cover art failed: {why}")

    if not cover_done:
        try:
            shutil.move(temp_media, final_output)
        except OSError as e:
            cleanup_partials(safe_title, png_path)
            return item_failed(index, total, f"could not save the file ({short_reason(e)})", item_url)
        if cover_failed:
            print_green("Saved without cover art")

    safe_remove(png_path)
    print(f"File #{index}/{total} saved")
    return True

# ---------------- Settings / Uninstall ----------------

PROGRAM_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = os.name == 'nt'
IS_MAC = sys.platform == 'darwin'
IS_TERMUX = os.path.isdir('/data/data/com.termux') or 'com.termux' in os.environ.get('PREFIX', '')

# Rough sizes in MB (installed size), used only to give the user an idea
SIZES_MB = {
    'windows': {'ffmpeg': 300, 'yt-dlp': 20, 'python': 100, 'git': 350},
    'termux':  {'ffmpeg': 150, 'yt-dlp': 20, 'python': 100, 'git': 40},
    'linux':   {'ffmpeg': 250, 'yt-dlp': 20, 'python': 60,  'git': 50},
    'mac':     {'ffmpeg': 400, 'yt-dlp': 20, 'python': 150, 'git': 60},
}
DISPLAY = {'ffmpeg': 'FFmpeg', 'yt-dlp': 'yt-dlp', 'python': 'Python', 'git': 'Git'}

def platform_key():
    if IS_WINDOWS:
        return 'windows'
    if IS_TERMUX:
        return 'termux'
    if IS_MAC:
        return 'mac'
    return 'linux'

def fmt_mb(mb):
    return f"{mb:.1f} MB" if mb < 10 else f"{int(round(mb))} MB"

def folder_size_mb(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / 1048576

def program_dir_is_safe(path):
    """Only allow deleting a folder that really looks like this project."""
    real = os.path.realpath(path)
    home = os.path.realpath(os.path.expanduser('~'))
    if real == home or os.path.dirname(real) == real:
        return False
    if not os.path.isfile(os.path.join(real, 'main_cli.py')):
        return False
    name = os.path.basename(real).lower()
    return name in ('catwiz-ytdl', 'ytdl-termux') or os.path.isdir(os.path.join(real, '.git'))

def shortcut_path():
    key = platform_key()
    if key == 'termux':
        prefix = os.environ.get('PREFIX', '/data/data/com.termux/files/usr')
        return os.path.join(prefix, 'bin', 'ytdl')
    if key in ('linux', 'mac'):
        return '/usr/local/bin/ytdl'
    local = os.environ.get('LOCALAPPDATA')
    if local:
        return os.path.join(local, 'Microsoft', 'WindowsApps', 'ytdl.cmd')
    return None

def in_venv():
    return sys.prefix != getattr(sys, 'base_prefix', sys.prefix)

def find_brew():
    found = shutil.which('brew')
    if found:
        return found
    for p in ('/opt/homebrew/bin/brew', '/usr/local/bin/brew'):
        if os.path.exists(p):
            return p
    return None

def brew_formulae():
    brew = find_brew()
    if not brew:
        return set()
    try:
        r = subprocess.run([brew, 'list', '--formula'], capture_output=True, text=True)
        return set(r.stdout.split())
    except Exception:
        return set()

def mac_python_formula():
    for f in sorted(brew_formulae()):
        if f == 'python' or f.startswith('python@'):
            return f
    return 'python'

def windows_python_id():
    """Find the winget id of the installed Python (falls back to 3.12)."""
    try:
        r = subprocess.run(['winget', 'list', 'Python.Python', '--accept-source-agreements'],
                           capture_output=True, text=True)
        m = re.search(r'Python\.Python\.\d+\.\d+', r.stdout or '')
        if m:
            return m.group(0)
    except Exception:
        pass
    return 'Python.Python.3.12'

def removable_items():
    key = platform_key()
    items = []
    if key == 'mac':
        formulae = brew_formulae()
        has_python = any(f == 'python' or f.startswith('python@') for f in formulae)
        items.append({'id': 'ffmpeg', 'found': 'ffmpeg' in formulae})
        if not in_venv():
            items.append({'id': 'yt-dlp', 'found': importlib.util.find_spec('yt_dlp') is not None})
        items.append({'id': 'python', 'found': has_python})
        items.append({'id': 'git', 'found': 'git' in formulae})
        return items
    items.append({'id': 'ffmpeg', 'found': shutil.which('ffmpeg') is not None})
    if not in_venv():
        items.append({'id': 'yt-dlp', 'found': importlib.util.find_spec('yt_dlp') is not None})
    if key != 'linux':
        # Debian/Ubuntu is skipped on purpose: system tools depend on Python there
        items.append({'id': 'python', 'found': True})
    items.append({'id': 'git', 'found': shutil.which('git') is not None})
    return items

def removal_command(item):
    key = platform_key()
    if item == 'yt-dlp':
        return [sys.executable, '-m', 'pip', 'uninstall', '-y', 'yt-dlp']
    if key == 'termux':
        return ['pkg', 'uninstall', '-y', item]
    if key == 'linux':
        return ['sudo', 'apt-get', 'remove', '-y', item]
    if key == 'mac':
        name = mac_python_formula() if item == 'python' else item
        return [find_brew() or 'brew', 'uninstall', name]
    ids = {'ffmpeg': 'Gyan.FFmpeg', 'python': 'Python.Python.3.12', 'git': 'Git.Git'}
    return ['winget', 'uninstall', '-e', '--id', ids[item], '--silent', '--accept-source-agreements']

def run_quiet(cmd):
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        lines = (r.stderr or '').strip().splitlines()
        return r.returncode == 0, (lines[-1] if lines else '')
    except Exception as e:
        return False, str(e)

def report(ok, reason=''):
    if ok:
        print_green("done")
    else:
        print(f"{RED}failed{RESET}" + (f" ({reason[:120]})" if reason else ""))

def ask_yes_no(prompt):
    while True:
        ans = input(f"\n{YELLOW}{prompt} [y/n]:{RESET} ").strip().lower()
        if ans in ('y', 'n'):
            return ans == 'y'

def parse_selection(text, count):
    tokens = text.replace(',', ' ').split()
    if not tokens:
        return None
    picked = set()
    for tok in tokens:
        if not tok.isdigit():
            return None
        v = int(tok)
        if v == 0:
            return [] if len(tokens) == 1 else None
        if v == count + 1:
            return list(range(1, count + 1))
        if 1 <= v <= count:
            picked.add(v)
        else:
            return None
    return sorted(picked)

def schedule_windows_cleanup(folder, remove_python, python_id='Python.Python.3.12'):
    """A running program can't delete its own folder on Windows, so a helper does it after we exit."""
    lines = ['@echo off', 'cd /d "%USERPROFILE%"', 'ping 127.0.0.1 -n 4 >nul']
    if remove_python:
        lines.append(f'winget uninstall -e --id {python_id} --silent --accept-source-agreements >nul 2>&1')
    if folder:
        lines += [
            'for /l %%i in (1,1,60) do (',
            f'  rmdir /s /q "{folder}" >nul 2>&1',
            f'  if not exist "{folder}" goto done',
            '  ping 127.0.0.1 -n 3 >nul',
            ')',
            ':done',
        ]
    lines.append('del "%~f0" >nul 2>&1')
    bat = os.path.join(tempfile.gettempdir(), 'catwiz_cleanup.bat')
    with open(bat, 'w') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    flags = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
    subprocess.Popen(['cmd', '/c', bat], creationflags=flags, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def uninstall_menu():
    key = platform_key()
    sizes = SIZES_MB[key]
    folder_ok = program_dir_is_safe(PROGRAM_DIR)
    folder_mb = folder_size_mb(PROGRAM_DIR) if folder_ok else 0
    shortcut = shortcut_path()
    shortcut_exists = bool(shortcut) and os.path.exists(shortcut)

    print(f"\n{CYAN}--------------------------------------{RESET}")
    print(" Uninstall CATWIZ-ytdl")
    print(f"{CYAN}--------------------------------------{RESET}")
    print("This will remove:")
    if folder_ok:
        print(f"  - Program folder: {PROGRAM_DIR} (~{fmt_mb(folder_mb)})")
    else:
        print(f"  - {YELLOW}Program folder not recognised, so it will NOT be deleted:{RESET}")
        print(f"    {PROGRAM_DIR}")
    if shortcut_exists:
        print(f"  - Shortcut: {shortcut}")
    print("Your downloaded files will NOT be deleted.")

    items = removable_items()
    found = [it for it in items if it['found']]
    selected = []

    print("\nAlso remove these programs? Other apps may use them.")
    n = 0
    for it in items:
        label = DISPLAY[it['id']]
        if it['found']:
            n += 1
            it['num'] = n
            print(f"  {n}. {label:<8} (found, ~{sizes[it['id']]} MB)")
        else:
            print(f"  -  {label:<8} (not found)")
    if found:
        print(f"  {n + 1}. All of the above")
    print("  0. Keep them all")

    if found:
        attempts = 0
        max_attempts = 3
        while True:
            choice = input(f"{YELLOW}Select (e.g. 1,3):{RESET} ")
            picked = parse_selection(choice, len(found))
            if picked is not None:
                selected = [it for it in found if it['num'] in picked]
                break
            attempts += 1
            if attempts >= max_attempts:
                print_green("Too many invalid attempts. Exiting.")
                sys.exit(1)
            print_green("Invalid selection.")

    names = []
    freed = 0
    if folder_ok:
        names.append("Program folder")
        freed += folder_mb
    for it in selected:
        names.append(DISPLAY[it['id']])
        freed += sizes[it['id']]
    if not names and not shortcut_exists:
        print_green("\nNothing to remove.")
        return

    print(f"\nYou chose to remove: {', '.join(names) if names else 'Shortcut only'}")
    print(f"This frees about {fmt_mb(freed)}.")
    if not ask_yes_no("Are you sure? This can't be undone."):
        print_green("Cancelled.")
        return

    print()
    needs_sudo = key == 'linux' and (shortcut_exists or any(it['id'] != 'yt-dlp' for it in selected))
    needs_sudo = needs_sudo or (key == 'mac' and shortcut_exists)
    sudo_ok = True
    if needs_sudo:
        sudo_ok = subprocess.run(['sudo', '-v']).returncode == 0

    if shortcut_exists:
        print("Removing shortcut... ", end='', flush=True)
        if key in ('termux', 'windows'):
            try:
                os.remove(shortcut)
                report(True)
            except OSError as e:
                report(False, str(e))
        elif sudo_ok:
            report(*run_quiet(['sudo', 'rm', '-f', shortcut]))
        else:
            report(False, 'sudo password needed')

    deferred_python = False
    order = ['yt-dlp', 'ffmpeg', 'git', 'python']
    for item_id in order:
        it = next((x for x in selected if x['id'] == item_id), None)
        if not it:
            continue
        label = DISPLAY[item_id]
        if item_id == 'python' and key == 'windows':
            deferred_python = True
            continue
        print(f"Removing {label}... ", end='', flush=True)
        if key == 'linux' and not sudo_ok and item_id != 'yt-dlp':
            report(False, 'sudo password needed')
            continue
        ok, why = run_quiet(removal_command(item_id))
        if not ok and not why and key == 'windows':
            why = 'not installed with winget? remove it in Settings > Apps'
        report(ok, why)

    if folder_ok:
        print("Removing program folder... ", end='', flush=True)
        try:
            os.chdir(os.path.expanduser('~'))
        except OSError:
            pass
        if key == 'windows':
            try:
                schedule_windows_cleanup(PROGRAM_DIR, deferred_python, windows_python_id())
                print_green("scheduled")
            except Exception as e:
                report(False, str(e))
        else:
            try:
                shutil.rmtree(PROGRAM_DIR)
                report(True)
            except Exception as e:
                report(False, str(e))
    elif deferred_python:
        try:
            schedule_windows_cleanup(None, True, windows_python_id())
        except Exception:
            pass

    print_green("\nCATWIZ-ytdl has been uninstalled.")
    if key == 'windows':
        if folder_ok:
            print("The program folder is deleted in the background once this terminal is no longer inside it.")
            print("If it is still there after a minute, run: cd ~")
        if deferred_python:
            print("Python is removed in the background after this window closes (a permission prompt may appear).")
    sys.exit(0)

# ---------------- Update ----------------

def run_capture(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
        return r.returncode == 0, ((r.stdout or '') + (r.stderr or '')).strip()
    except Exception as e:
        return False, str(e)

def last_line(text):
    lines = [l.strip() for l in (text or '').splitlines() if l.strip()]
    return lines[-1] if lines else ''

def show_status(status, msg):
    if status in ('changed', 'same'):
        print_green(msg)
    elif status == 'skipped':
        print(f"{YELLOW}{msg}{RESET}")
    else:
        print(f"{RED}failed ({msg}){RESET}")

def ytdlp_version():
    ok, out = run_capture([sys.executable, '-c', 'import yt_dlp.version as v; print(v.__version__)'])
    return last_line(out) if ok else None

def update_program():
    if not os.path.isdir(os.path.join(PROGRAM_DIR, '.git')):
        return 'skipped', 'skipped (not a git copy, run the install command again to enable updates)'
    if not shutil.which('git'):
        return 'failed', 'git not found'
    ok, out = run_capture(['git', '-C', PROGRAM_DIR, 'pull', '--ff-only'])
    if not ok:
        return 'failed', last_line(out)[:140]
    if 'already up to date' in out.lower():
        return 'same', 'already up to date'
    return 'changed', 'updated'

def update_ytdlp():
    before = ytdlp_version()
    cmd = [sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp']
    ok, out = run_capture(cmd)
    if not ok and 'externally-managed' in out.lower() and not in_venv():
        ok, out = run_capture(cmd + ['--break-system-packages'])
    if not ok:
        return 'failed', last_line(out)[:140]
    after = ytdlp_version()
    if before and after and before != after:
        return 'changed', f"{before} -> {after}"
    return 'same', f"already up to date ({after or before or 'unknown version'})"

def run_step(label, cmd, same_texts=()):
    print(f"Updating {label}... ", end='', flush=True)
    ok, out = run_capture(cmd)
    low = out.lower()
    if any(t in low for t in same_texts):
        print_green("already up to date")
        return 'same'
    if ok:
        print_green("done")
        return 'changed'
    print(f"{RED}failed ({last_line(out)[:120]}){RESET}")
    return 'failed'

def schedule_windows_python_upgrade(python_id):
    """Python can't be upgraded while this program is running it, so a helper does it after we exit."""
    lines = [
        '@echo off',
        'cd /d "%USERPROFILE%"',
        'ping 127.0.0.1 -n 4 >nul',
        f'winget upgrade -e --id {python_id} --silent --accept-package-agreements --accept-source-agreements >nul 2>&1',
        'del "%~f0" >nul 2>&1',
    ]
    bat = os.path.join(tempfile.gettempdir(), 'catwiz_update.bat')
    with open(bat, 'w') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    flags = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
    subprocess.Popen(['cmd', '/c', bat], creationflags=flags, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def update_system_packages():
    """Upgrade FFmpeg, Python and Git with the system package manager. Returns a list of statuses."""
    key = platform_key()
    results = []
    if key == 'termux':
        results.append(run_step('package lists', ['pkg', 'update', '-y']))
        names = ['python'] + [n for n in ('ffmpeg', 'git') if shutil.which(n)]
        for n in names:
            results.append(run_step(DISPLAY.get(n, n), ['pkg', 'install', '-y', n],
                                    ('already the newest version',)))
    elif key == 'linux':
        results.append(run_step('package lists', ['sudo', 'apt-get', 'update', '-y']))
        for n, pkg in (('ffmpeg', 'ffmpeg'), ('git', 'git'), ('python', 'python3')):
            if n == 'python' or shutil.which(n):
                results.append(run_step(DISPLAY[n], ['sudo', 'apt-get', 'install', '-y', '--only-upgrade', pkg],
                                        ('already the newest version',)))
    elif key == 'mac':
        brew = find_brew()
        if not brew:
            print(f"{YELLOW}Homebrew not found, skipping FFmpeg, Python and Git.{RESET}")
            return results
        results.append(run_step('Homebrew', [brew, 'update']))
        formulae = brew_formulae()
        todo = [('FFmpeg', 'ffmpeg' if 'ffmpeg' in formulae else None),
                ('Python', mac_python_formula() if any(f == 'python' or f.startswith('python@') for f in formulae) else None),
                ('Git', 'git' if 'git' in formulae else None)]
        for label, name in todo:
            if not name:
                print(f"Updating {label}... {YELLOW}skipped (not installed with Homebrew){RESET}")
                continue
            _, before = run_capture([brew, 'list', '--versions', name])
            st = run_step(label, [brew, 'upgrade', name], ('already installed',))
            if st == 'changed':
                _, after = run_capture([brew, 'list', '--versions', name])
                if before == after:
                    st = 'same'
                    print(f"  ({label} was already up to date)")
            results.append(st)
    else:
        if not shutil.which('winget'):
            print(f"{YELLOW}winget not found, skipping FFmpeg, Python and Git.{RESET}")
            return results
        same = ('no available upgrade found', 'no newer package versions')
        base = ['winget', 'upgrade', '-e', '--silent',
                '--accept-package-agreements', '--accept-source-agreements', '--id']
        if shutil.which('ffmpeg'):
            results.append(run_step('FFmpeg', base + ['Gyan.FFmpeg'], same))
        if shutil.which('git'):
            results.append(run_step('Git', base + ['Git.Git'], same))
        try:
            schedule_windows_python_upgrade(windows_python_id())
            print(f"Updating Python... {GREEN}scheduled{RESET} (runs in the background after this program closes)")
            results.append('changed')
        except Exception as e:
            print(f"Updating Python... {RED}failed ({short_reason(e)}){RESET}")
            results.append('failed')
    return results

def update_necessary():
    print(f"\n{CYAN}--------------------------------------{RESET}")
    print(" Updating what's necessary")
    print(f"{CYAN}--------------------------------------{RESET}")
    statuses = []
    print("Updating CATWIZ-ytdl... ", end='', flush=True)
    st, msg = update_program()
    show_status(st, msg)
    statuses.append(st)
    print("Updating yt-dlp... ", end='', flush=True)
    st, msg = update_ytdlp()
    show_status(st, msg)
    statuses.append(st)
    return statuses

def update_everything():
    key = platform_key()
    print(f"\n{CYAN}--------------------------------------{RESET}")
    print(" Update everything")
    print(f"{CYAN}--------------------------------------{RESET}")
    tools = {'termux': 'pkg', 'linux': 'apt', 'mac': 'Homebrew', 'windows': 'winget'}[key]
    print("This will check for updates to:")
    print("  - CATWIZ-ytdl (the program)")
    print("  - yt-dlp")
    print(f"  - FFmpeg, Python and Git (using {tools})")
    if key == 'windows':
        print("  A Windows permission prompt may appear.")
    elif key in ('linux', 'mac'):
        print("  You may be asked for your password.")
    print("This can take a few minutes.")
    if not ask_yes_no("Proceed?"):
        print_green("Cancelled.")
        return None
    if key == 'linux' and subprocess.run(['sudo', '-v']).returncode != 0:
        print(f"{RED}Could not get permission (sudo). Nothing was updated.{RESET}")
        return []
    print()
    statuses = []
    print("Updating CATWIZ-ytdl... ", end='', flush=True)
    st, msg = update_program()
    show_status(st, msg)
    statuses.append(st)
    statuses += update_system_packages()
    # yt-dlp last, because a Python upgrade can remove packages installed outside a virtual environment
    print("Updating yt-dlp... ", end='', flush=True)
    st, msg = update_ytdlp()
    show_status(st, msg)
    statuses.append(st)
    return statuses

def update_menu():
    max_attempts = 3
    print(f"\n{CYAN}======================================{RESET}")
    print(" Update")
    print("  1. Update what's necessary (CATWIZ-ytdl and yt-dlp)")
    print("  2. Update everything (also FFmpeg, Python and Git)")
    print("  0. Back")
    print(f"{CYAN}--------------------------------------{RESET}")
    attempts = 0
    choice = None
    while attempts < max_attempts:
        choice = input(f"{YELLOW}Select option [1/2/0]:{RESET} ").strip()
        if choice in ('0', '1', '2'):
            break
        attempts += 1
        if attempts < max_attempts:
            print_green("Invalid option selected.")
        else:
            print_green("Too many invalid attempts. Exiting.")
            sys.exit(1)
    if choice == '0':
        return
    statuses = update_necessary() if choice == '1' else update_everything()
    if statuses is None:
        return
    print()
    if 'failed' in statuses:
        print(f"{YELLOW}Some updates failed. Running the install command again usually repairs everything.{RESET}")
    if 'changed' in statuses:
        print_green("Updates installed. Restart CATWIZ-ytdl to use them.")
        sys.exit(0)
    if 'failed' not in statuses:
        print_green("Everything is up to date.")

# ---------------- Settings menu ----------------

def settings_menu():
    max_attempts = 3
    while True:
        print(f"\n{CYAN}======================================{RESET}")
        print(" Settings")
        print("  1. Update")
        print("  2. Uninstall CATWIZ-ytdl")
        print("  0. Back")
        print(f"{CYAN}--------------------------------------{RESET}")
        attempts = 0
        choice = None
        while attempts < max_attempts:
            choice = input(f"{YELLOW}Select option [1/2/0]:{RESET} ").strip()
            if choice in ('0', '1', '2'):
                break
            attempts += 1
            if attempts < max_attempts:
                print_green("Invalid option selected.")
            else:
                print_green("Too many invalid attempts. Exiting.")
                sys.exit(1)
        if choice == '0':
            return
        if choice == '1':
            update_menu()
        else:
            uninstall_menu()

def print_main_menu():
    print(f"{CYAN}======================================{RESET}")
    print(" -1. Settings")
    print("  1. Audio (.mp3)")
    print("  2. Video (.mp4)")
    print("  3. Extract Thumbnail (.png)")
    print("  0. Exit")
    print(f"{CYAN}--------------------------------------{RESET}")

def main():
    check_ffmpeg()
    print(BANNER)
    max_attempts = 3
    while True:
        print_main_menu()
        attempts = 0
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
        if mode == '-1':
            settings_menu()
            print()
            continue
        break

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
    url, info, playlist_items = get_validated_url(is_playlist, mode)

    if mode == '1':
        selected_quality = select_audio_quality(info, is_playlist)
        save_path = os.path.join(get_download_dir(), 'Music')
    elif mode == '2':
        selected_quality = select_video_quality(info, is_playlist)
        save_path = get_download_dir()
    else:
        selected_quality = select_photo_quality(info, is_playlist)
        save_path = os.path.join(get_download_dir(), 'Thumbnails')

    results = []
    if is_playlist:
        total = len(playlist_items)
        for idx, item in enumerate(playlist_items, 1):
            if mode == '3':
                results.append(process_thumbnail_only(item, True, idx, total, save_path, selected_quality))
            else:
                results.append(process_single_item(item, mode, True, idx, total, save_path, selected_quality))
        saved = results.count(True)
        failed = results.count(False)
        print()
        if failed:
            print(f"{YELLOW}Finished: {saved} saved, {failed} failed (details in errors.log){RESET}")
        else:
            print_green(f"Finished: all {saved} saved")
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
