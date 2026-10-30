#!/usr/bin/env bash
# CATWIZ-ytdl installer for Termux, Debian/Ubuntu and macOS
REPO="https://github.com/Dr-Jesus1225/ytdl-termux.git"
DIR="$HOME/CATWIZ-ytdl"

CYAN=$'\033[96m'; YELLOW=$'\033[93m'; GREEN=$'\033[92m'; RED=$'\033[91m'; RESET=$'\033[0m'

if [[ "$PREFIX" == *com.termux* ]]; then OS=termux
elif [ "$(uname)" = "Darwin" ]; then OS=mac
elif command -v apt-get &>/dev/null; then OS=linux
else
  echo "${RED}Unsupported system.${RESET} This installer supports Termux, Debian/Ubuntu and macOS."
  exit 1
fi

# Homebrew may be installed but not on PATH yet
if [ "$OS" = mac ]; then
  for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [ -x "$b" ] && eval "$("$b" shellenv)"
  done
fi

size_of() {
  case "$OS-$1" in
    termux-git) echo 40;;   termux-python) echo 100;; termux-ffmpeg) echo 150;; termux-yt-dlp) echo 20;;
    linux-git) echo 50;;    linux-python) echo 60;;    linux-ffmpeg) echo 250;;  linux-yt-dlp) echo 20;;
    mac-git) echo 60;;      mac-python) echo 150;;     mac-ffmpeg) echo 400;;    mac-yt-dlp) echo 20;;
    mac-homebrew) echo 1500;;
  esac
}

has_git() {
  if [ "$OS" = mac ]; then command -v git &>/dev/null && xcode-select -p &>/dev/null
  else command -v git &>/dev/null; fi
}
has_python() {
  case "$OS" in
    termux) command -v python &>/dev/null;;
    linux) command -v python3 &>/dev/null && python3 -c "import venv, ensurepip" &>/dev/null;;
    mac) [ -x /opt/homebrew/bin/python3 ] || [ -x /usr/local/bin/python3 ] ||
         { xcode-select -p &>/dev/null && python3 -c "import venv, ensurepip" &>/dev/null; };;
  esac
}
has_ffmpeg() { command -v ffmpeg &>/dev/null; }
has_ytdlp() {
  if [ "$OS" = termux ]; then python -c "import yt_dlp" &>/dev/null
  else [ -x "$DIR/.venv/bin/python" ] && "$DIR/.venv/bin/python" -c "import yt_dlp" &>/dev/null; fi
}

FOUND=(); MISSING=(); TOTAL=0
NEED_GIT=0; NEED_PYTHON=0; NEED_FFMPEG=0; NEED_YTDLP=0; NEED_BREW=0

check() { # label, id, function
  if "$3"; then FOUND+=("$1")
  else
    local mb; mb=$(size_of "$2")
    MISSING+=("$1 (~${mb} MB)"); TOTAL=$((TOTAL + mb))
    case "$2" in git) NEED_GIT=1;; python) NEED_PYTHON=1;; ffmpeg) NEED_FFMPEG=1;; yt-dlp) NEED_YTDLP=1;; esac
  fi
}

check "Git" git has_git
check "Python" python has_python
check "FFmpeg" ffmpeg has_ffmpeg
check "yt-dlp" yt-dlp has_ytdlp

if [ "$OS" = mac ] && ! command -v brew &>/dev/null && [ $((NEED_GIT + NEED_PYTHON + NEED_FFMPEG)) -gt 0 ]; then
  NEED_BREW=1
  mb=$(size_of homebrew)
  MISSING=("Homebrew + Xcode tools (~${mb} MB)" "${MISSING[@]}")
  TOTAL=$((TOTAL + mb))
fi

join() { local IFS=,; echo "$*" | sed 's/,/, /g'; }

echo
echo "${CYAN}======================================${RESET}"
echo " CATWIZ-ytdl installer"
echo "${CYAN}--------------------------------------${RESET}"
echo "CATWIZ-ytdl needs: Git, Python, FFmpeg, yt-dlp"
if [ ${#FOUND[@]} -gt 0 ]; then echo "Found:   $(join "${FOUND[@]}")"; else echo "Found:   none"; fi

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "Missing: $(join "${MISSING[@]}")"
  echo "Total to install: about ${TOTAL} MB"
  while true; do
    read -r -p "${YELLOW}Install the missing items? [y/n]:${RESET} " ans
    case "$ans" in
      [Yy]) break;;
      [Nn]) echo "Install cancelled."; exit 0;;
    esac
  done
else
  echo "${GREEN}Everything is already installed.${RESET}"
fi
echo

fail() { echo "${RED}$1${RESET}"; exit 1; }

# ---- install missing programs ----
case "$OS" in
  termux)
    pkgs=()
    [ $NEED_GIT = 1 ] && pkgs+=(git)
    [ $NEED_PYTHON = 1 ] && pkgs+=(python)
    [ $NEED_FFMPEG = 1 ] && pkgs+=(ffmpeg)
    if [ ${#pkgs[@]} -gt 0 ]; then
      pkg update -y && pkg install -y "${pkgs[@]}" || fail "Could not install: ${pkgs[*]}"
    fi
    ;;
  linux)
    pkgs=()
    [ $NEED_GIT = 1 ] && pkgs+=(git)
    [ $NEED_PYTHON = 1 ] && pkgs+=(python3 python3-pip python3-venv)
    [ $NEED_FFMPEG = 1 ] && pkgs+=(ffmpeg)
    if [ ${#pkgs[@]} -gt 0 ]; then
      sudo apt-get update -y && sudo apt-get install -y "${pkgs[@]}" || fail "Could not install: ${pkgs[*]}"
    fi
    ;;
  mac)
    if [ $NEED_BREW = 1 ]; then
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || fail "Homebrew install failed"
      for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
        [ -x "$b" ] && eval "$("$b" shellenv)"
      done
    fi
    pkgs=()
    [ $NEED_GIT = 1 ] && pkgs+=(git)
    [ $NEED_PYTHON = 1 ] && pkgs+=(python)
    [ $NEED_FFMPEG = 1 ] && pkgs+=(ffmpeg)
    if [ ${#pkgs[@]} -gt 0 ]; then
      brew install "${pkgs[@]}" || fail "Could not install: ${pkgs[*]}"
    fi
    ;;
esac

# ---- download or update the project ----
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull || echo "${YELLOW}Could not update, using the existing copy.${RESET}"
elif [ -d "$DIR" ]; then
  echo "${YELLOW}$DIR already exists and is not a git copy, leaving it as it is.${RESET}"
else
  git clone "$REPO" "$DIR" || fail "Could not download the project"
fi

# ---- yt-dlp and the ytdl shortcut ----
if [ "$OS" = termux ]; then
  python -m pip install -U yt-dlp || fail "Could not install yt-dlp"
  SHORTCUT="$PREFIX/bin/ytdl"
  printf '#!/data/data/com.termux/files/usr/bin/bash\nexec python "%s/main_cli.py" "$@"\n' "$DIR" > "$SHORTCUT"
  chmod +x "$SHORTCUT"
  if [ ! -d "$HOME/storage" ]; then
    echo "${YELLOW}Allow storage access when asked, so downloads can be saved to your phone.${RESET}"
    termux-setup-storage
    sleep 3
  fi
else
  [ -x "$DIR/.venv/bin/python" ] || python3 -m venv "$DIR/.venv" || fail "Could not create the Python environment"
  "$DIR/.venv/bin/pip" install -U yt-dlp || fail "Could not install yt-dlp"
  SHORTCUT="/usr/local/bin/ytdl"
  [ "$OS" = mac ] && sudo mkdir -p /usr/local/bin
  printf '#!/usr/bin/env bash\nexec "%s/.venv/bin/python" "%s/main_cli.py" "$@"\n' "$DIR" "$DIR" | sudo tee "$SHORTCUT" >/dev/null
  sudo chmod +x "$SHORTCUT"
fi

echo
echo "${GREEN}Installed. Starting CATWIZ-ytdl (type ytdl next time).${RESET}"
exec "$SHORTCUT"
