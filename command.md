# CATWIZ-ytdl Setup

Run this command in Termux:

```bash
pkg update -y && command -v git &>/dev/null || pkg install git -y && [ -d "$HOME/CATWIZ-ytdl" ] || git clone [https://github.com/Dr-Jesus1225/ytdl-termux.git](https://github.com/Dr-Jesus1225/ytdl-termux.git) "$HOME/CATWIZ-ytdl" && bash "$HOME/CATWIZ-ytdl/preq.sh" && echo -e "#!/data/data/com.termux/files/usr/bin/bash\npython \"$HOME/CATWIZ-ytdl/main_cli.py\"" > $PREFIX/bin/ytdl && chmod +x$PREFIX/bin/ytdl && ytdl
```
