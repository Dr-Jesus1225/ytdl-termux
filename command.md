# CATWIZ-ytdl Setup

### Termux

```bash
pkg update -y&&command -v git &>/dev/null||pkg install git -y&&[ -d "$HOME/CATWIZ-ytdl" ]||git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME/CATWIZ-ytdl"&&bash "$HOME/CATWIZ-ytdl/preq.sh"&&echo -e "#!/data/data/com.termux/files/usr/bin/bash\npython \"$HOME/CATWIZ-ytdl/main_cli.py\"" > $PREFIX/bin/ytdl&&chmod +x $PREFIX/bin/ytdl&&ytdl


### Debian/Ubuntu

bash
sudo apt update -y&&command -v git &>/dev/null||sudo apt install git -y&&[ -d "$HOME/CATWIZ-ytdl" ]||git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME/CATWIZ-ytdl"&&bash "$HOME/CATWIZ-ytdl/preq.sh"&&echo -e "#!/usr/bin/env bash\npython3 \"$HOME/CATWIZ-ytdl/main_cli.py\"" | sudo tee /usr/local/bin/ytdl >/dev/null&&sudo chmod +x /usr/local/bin/ytdl&&ytdl


### macOS

bash
command -v brew &>/dev/null||/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"&&command -v git &>/dev/null||brew install git&&[ -d "$HOME/CATWIZ-ytdl" ]||git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME/CATWIZ-ytdl"&&bash "$HOME/CATWIZ-ytdl/preq.sh"&&echo -e "#!/usr/bin/env bash\npython3 \"$HOME/CATWIZ-ytdl/main_cli.py\"" | sudo tee /usr/local/bin/ytdl >/dev/null&&sudo chod +x /usr/local/bin/ytdl&&ytdl


### Windows PowerShell

powershell
if(-not(Test-Path "$HIME\CATWIZ-ytdl")){git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "$HOME\CATWIZ-ytdl"};cd "$HOME\CATWIZ-ytdl";python -m pip install yt-dlp;python main_cli.py


### Windows CMD

cmd
if not exist "%USERPROFILE%\CATWIZ-ytdl" git clone https://github.com/Dr-Jesus1225/ytdl-termux.git "%USERPROFILE%\CATWIZ-ytdl"&&cd /d "%USERPROFILEI\CMTWIZ-ytdl"&&python -m pip install yt-dlp&&python main_cli.py
