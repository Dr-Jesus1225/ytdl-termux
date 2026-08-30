import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
import yt_dlp

class YTDLApp(App):
    def build(self):
        self.title = "YT-DLP Downloader"
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="YT-DLP Android Downloader", font_size='20sp', size_hint_y=None, height=40))
        
        self.type_spinner = Spinner(
            text='Single Song (MP3)',
            values=('Single Song (MP3)', 'Playlist (MP3)'),
            size_hint_y=None, height=44
        )
        layout.add_widget(self.type_spinner)
        
        self.url_input = TextInput(hint_text="Paste YouTube URL here...", multiline=False, size_hint_y=None, height=44)
        layout.add_widget(self.url_input)
        
        self.download_btn = Button(text="Start Download", size_hint_y=None, height=50)
        self.download_btn.bind(on_press=self.start_download_thread)
        layout.add_widget(self.download_btn)
        
        self.status_label = Label(text="Status: Ready", size_hint_y=None, height=30)
        layout.add_widget(self.status_label)
        
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=20)
        layout.add_widget(self.progress_bar)
        
        return layout

    def update_status(self, text):
        self.status_label.text = text

    def update_progress(self, percent):
        self.progress_bar.value = percent

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                Clock.schedule_once(lambda dt: self.update_progress(percent))
                Clock.schedule_once(lambda dt: self.update_status(f"Downloading: {int(percent)}%"))
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: self.update_status("Processing audio..."))

    def start_download_thread(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = "Status: Please enter a URL"
            return
            
        self.download_btn.disabled = True
        self.status_label.text = "Status: Fetching metadata..."
        threading.Thread(target=self.run_download, args=(url,), daemon=True).start()

    def run_download(self, url):
        try:
            download_path = "/sdcard/Download/Music/%(title)s.%(ext)s"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': download_path,
                'writethumbnail': True,
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                    {'key': 'FFmpegMetadata'},
                    {'key': 'EmbedThumbnail'},
                ],
                'progress_hooks': [self.progress_hook],
                'quiet': True,
                'noplaylist': True if self.type_spinner.text == 'Single Song (MP3)' else False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            Clock.schedule_once(lambda dt: self.update_status("Status: Download Complete!"))
            Clock.schedule_once(lambda dt: self.update_progress(100))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"Error: {str(e)[:40]}"))
        finally:
            Clock.schedule_once(lambda dt: setattr(self.download_btn, 'disabled', False))

if __name__ == '__main__':
    YTDLApp().run()
