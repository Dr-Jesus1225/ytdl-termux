import sys, os, re

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
        f = d.get('filename', '')
        m = re.search(r'_(\d+)_of_(\d+)\.', f)
        idx = f" #{m.group(1)}/{m.group(2)}" if m else ""
        sys.stdout.write(f"\r[CATWIZ-ytdl]{idx} {p} at {s} ETA {e}   ")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        print("\n[CATWIZ] Processing metadata & formatting...")

def main():
    print_banner()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Media URL: ").strip()
        
    if not url:
        print("No URL provided. Exiting, sir.")
        return

    print("\nSelect Download Mode:")
    print("1) Video (Best Quality - MP4)")
    print("2) Audio Only (MP3)")
    print("3) Playlist - Video")
    print("4) Playlist - Audio (MP3)")
    
    choice = input("\nChoice [1-4] (Default: 1): ").strip() or "1"

    ydl_opts = {
        'progress_hooks': [progress_hook],
        'quiet': True,
        'nocheckcertificate': True,
    }

    if choice == '1':
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
        })
    elif choice == '2':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata'},
            ],
        })
    elif choice == '3':
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s',
        })
    elif choice == '4':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s',
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata'},
            ],
        })

    print("\n[CATWIZ] Starting download...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("\n[CATWIZ] Download complete, sir.")
        except Exception as e:
            print(f"\n[CATWIZ] Error: {e}")

if __name__ == "__main__":
    main()
