import sys,os,re
try:import yt_dlp
except ImportError:sys.exit(1)
def progress_hook(d):
 if d["status"]=="downloading":
  p=d.get("_percent_str","0%").strip()
  s=d.get("_speed_str","N/A").strip()
  e=d.get("_eta_str","N/A").strip()
  f=d.get("filename","")
  m=re.search(r"_(\d+)_of_(\d+)\.",f)
  idx=f" #{m.group(1)}/{m.group(2)}" if m else ""
  sys.stdout.write(f"\r[CATWIZ-ytdl]{idx} {p} at {s} ETA#tw {p} at {s} ETA#{e} ")
  sys.stdout.flush()
 elif d["status"]=="finished":
  print("\nProcessing metadata & thumbnail...")
def main():
 if len(sys.argv)>1:url=sys.argv[1]
 else:url=input("URL: ").strip()
 if not url:return
 opts={"format":"bestvideo+bestaudio/best","outtmpl":"%(title)s.%(ext)s","writethumbnail":True,"postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"},{"key":"EmbedThumbnail"},{"key":"FFmpegMetadata"}],"progress_hooks":[progress_hook],"quiet":True,"nocheckcertificate":True}
 with yt_dlp.YoutubeDL(opts) as ydl:
  try:ydl.download([url])
  except Exception as e:print(e)
if __name__=="__main__":main()
