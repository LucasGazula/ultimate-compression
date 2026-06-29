#!/usr/bin/env bash
# Ultimate Compression Installer for Linux, macOS, and WSL

set -e

# Temporarily clean PATH from any active ultimate-compression shims during installation to prevent loops
CLEAN_PATH=""
IFS=:
for d in $PATH; do
  if [ -d "$d" ]; then
    abs_d=$(cd "$d" && pwd)
    case "$abs_d" in
      */ultimate-compression/shims) ;;
      *) CLEAN_PATH="${CLEAN_PATH:+$CLEAN_PATH:}$d" ;;
    esac
  fi
done
unset IFS
export PATH="$CLEAN_PATH"


# 1. Determine Installation Directory
if [ -d "/mnt/ssd" ]; then
  INSTALL_DIR="/mnt/ssd/ultimate-compression"
else
  INSTALL_DIR="$HOME/.ultimate-compression"
fi

echo "Installing Ultimate Compression to: $INSTALL_DIR"

# 2. Check Python 3
if ! command -v python3 &>/dev/null; then
  echo "Error: Python 3 is required but not installed." >&2
  exit 1
fi

# 3. Create directory if not exists (e.g. if running curl installer)
if [ ! -d "$INSTALL_DIR" ]; then
  mkdir -p "$INSTALL_DIR"
fi

# Download codebase if files aren't present (e.g., remote curl installation)
if [ ! -f "$INSTALL_DIR/uc" ]; then
  echo "Downloading codebase from GitHub (LucasGazula/ultimate-compression)..."
  curl -fsSL "https://github.com/LucasGazula/ultimate-compression/tarball/main" | tar -xz --strip-components=1 -C "$INSTALL_DIR"
fi

# 4. Setup Virtual Environment using uv
echo "Setting up Python environment using uv..."
if command -v uv &>/dev/null; then
  echo "uv detected. Creating virtual environment and installing packages..."
  uv venv "$INSTALL_DIR/.venv"
  # Install packages into the venv using uv
  uv pip install --python "$INSTALL_DIR/.venv/bin/python" -r "$INSTALL_DIR/requirements.txt"
else
  echo "uv not found. Falling back to standard python3-venv..."
  if python3 -m venv "$INSTALL_DIR/.venv" 2>/dev/null; then
    "$INSTALL_DIR/.venv/bin/pip" install --upgrade pip || true
    "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
  else
    echo "Error: Neither uv nor python3-venv could create the environment." >&2
    exit 1
  fi
fi



# 5. Make CLI Executable
chmod +x "$INSTALL_DIR/uc"

# 6. Clean Old Paths and Add New PATH (bashrc / zshrc)
echo "Configuring shell path..."
UC_PATH_LINE="export PATH=\"$INSTALL_DIR:\$PATH\""

clean_profile() {
  local profile="$1"
  if [ -f "$profile" ]; then
    if sed --version >/dev/null 2>&1; then
      # GNU sed (Linux)
      sed -i '/\/mnt\/ssd\/ultimate-compression/d' "$profile"
    else
      # BSD sed (macOS)
      sed -i '' '/\/mnt\/ssd\/ultimate-compression/d' "$profile"
    fi
  fi
}

clean_profile "$HOME/.bashrc"
clean_profile "$HOME/.zshrc"
clean_profile "$HOME/.profile"

add_to_profile() {
  local profile="$1"
  if [ -f "$profile" ]; then
    if ! grep -q "$INSTALL_DIR" "$profile"; then
      echo -e "\n# Ultimate Compression CLI\n$UC_PATH_LINE" >> "$profile"
      echo "Added 'uc' to $profile"
    fi
  fi
}

add_to_profile "$HOME/.bashrc"
add_to_profile "$HOME/.zshrc"
add_to_profile "$HOME/.profile"

echo "--------------------------------------------------------"
echo "✅ Ultimate Compression successfully installed!"
echo "--------------------------------------------------------"
echo "1. Reload your shell to apply PATH changes:"
echo "   exec bash  # (or restart your terminal)"
echo ""
echo "2. Start the local server:"
echo "   uc start"
echo ""
echo "3. Run 'uc init' inside your project repository to configure it!"
echo "--------------------------------------------------------"
