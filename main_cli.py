import sys
import os
import re

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is required. Please install it using: pip install yt-dlp")
    sys.exit(1)

def print_banner():
    print(r"""
  ____    _  _____ __        _____ _____ 
 / ___|  / \|_   _|\ \      / /_ _|__  / 
| |     / _ \ | |   \ \ /\ / / | |  / /  
| |___ / ___ \| |    \ V  V /  | | / /_  
 \____/_/   \_\_|     \_/\_/  |___/____| 
                                         
          CATWIZ-ytdl Media Downloader
""")

def progress_hook(d):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').strip()
        s = d.get('_speed_str', 'N/A').strip()
        e = d.get('_eta_str', 'N/A').strip()
        sys.stdout.write(f"\r[CATWIZ] Downloading... {p} at {s} ETA {e}   ")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        filepath = d.get('filename', '')
        info = d.get('info_dict', {})
        
        # Determine index tracking for playlist
        idx_str = ""
        p_index = info.get('playlist_index')
        p_count = info.get('playlist_count') or info.get('n_entries')
        
        if p_index and p_count:
            idx_str = f" #{p_index}/{p_count}"
        elif p_index:
            idx_str = f" #{p_index}"

        print(f"\nSaving to {filepath}")
        print(f"File{idx_str} saved")

def main():
    print_banner()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("Enter YouTube URL:")
        url = input().strip()
        
    if not url:
        print("No URL provided. Exiting, sir.")
        return

    print("\nSelect Download Mode:")
    print("1) Video (MP4)")
    print("2) Audio (MP3)")
    print("3) Playlist - Video")
    print("4) Playlist - Audio (MP3)")
    
    choice = input("\nChoice [1-4] (Default: 1): ").strip() or "1"

    is_audio = choice in ['2', '4']
    is_playlist = choice in ['3', '4']

    # Custom logger to print exact verbose messages during processing steps
    class CustomLogger:
        def debug(self, msg):
            if '[info] Downloading video thumbnail' in msg:
                print("Fetching Thumbnail")
            elif '[ThumbnailsConvertor] Converting thumbnail' in msg or 'Writing thumbnail' in msg:
                print("Thumbnail downloaded")
            elif '[download] Destination:' in msg and not hasattr(self, '_started'):
                print("Starting download")
                self._started = True

        def info(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            print(msg)

    # Media identification step
    media_label = "Song" if is_audio else "Video"
    print(f"\n{media_label} found")

    ydl_opts = {
        'writethumbnail': True,
        'logger': CustomLogger(),
        'progress_hooks': [progress_hook],
        'quiet': False,
        'nocheckcertificate': True,
    }

    if choice == '1':
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'postprocessors': [
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
        })
    elif choice == '2':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
        })
    elif choice == '3':
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s',
            'postprocessors': [
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
        })
    elif choice == '4':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s',
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
