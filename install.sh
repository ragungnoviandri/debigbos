#!/usr/bin/env bash
# TheBigBos Cross-Platform Installer
# Run: curl -fsSL https://raw.githubusercontent.com/ragungnoviandri/thebigbos/main/install.sh | bash

set -e

INSTALL_DIR="${THEBIGBOS_HOME:-$HOME/.local/share/thebigbos}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/thebigbos"
REPO_URL="https://github.com/ragungnoviandri/thebigbos.git"
PYTHON_VERSION="3.11"
BIN_DIR="$HOME/.local/bin"

echo ""
echo "============================================"
echo "  TheBigBos Installer"
echo "============================================"
echo ""

# 1. Detect OS + prerequisites
echo "[1/6] Checking prerequisites..."

if ! command -v git &>/dev/null; then
    echo "  ERROR: git not found. Install with your package manager."
    echo "    Ubuntu: sudo apt install git"
    echo "    macOS:  brew install git"
    exit 1
fi
echo "  git: $(which git)"

# Find Python
if command -v python3.11 &>/dev/null; then
    PYTHON=python3.11
elif command -v python3 &>/dev/null; then
    PYTHON=python3
else
    echo "  WARNING: python3 not found. Attempting to install..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python@3.11
        PYTHON=python3.11
    elif [[ -f /etc/debian_version ]]; then
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update && sudo apt install -y python3.11 python3.11-venv
        PYTHON=python3.11
    else
        echo "  ERROR: Please install Python 3.11+ manually."
        exit 1
    fi
fi
echo "  python: $(which $PYTHON) ($($PYTHON --version))"

# 2. Create directories
echo "[2/6] Creating directories..."
mkdir -p "$INSTALL_DIR/repo"
mkdir -p "$INSTALL_DIR/bin"
mkdir -p "$INSTALL_DIR/versions"
mkdir -p "$CONFIG_DIR/skills"
mkdir -p "$CONFIG_DIR/agents"
mkdir -p "$CONFIG_DIR/tools"
mkdir -p "$BIN_DIR"
echo "  Install: $INSTALL_DIR"
echo "  Config:  $CONFIG_DIR"

# 3. Clone repository
echo "[3/6] Cloning repository..."
if [ -d "$INSTALL_DIR/repo/.git" ]; then
    echo "  Repo exists, pulling latest..."
    git -C "$INSTALL_DIR/repo" pull origin main
else
    git clone "$REPO_URL" "$INSTALL_DIR/repo"
fi
echo "  Repository ready"

# 4. Create venv + install
echo "[4/6] Creating virtual environment..."
VENV_DIR="$INSTALL_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install -e "$INSTALL_DIR/repo" --quiet
echo "  Dependencies installed"

# 5. Create wrapper script
echo "[5/6] Creating wrapper..."
cat > "$INSTALL_DIR/bin/thebigbos" << 'WRAPPER'
#!/usr/bin/env bash
TB_HOME="${THEBIGBOS_HOME:-$HOME/.local/share/thebigbos}"
exec "$TB_HOME/venv/bin/python" -m thebigbos "$@"
WRAPPER
chmod +x "$INSTALL_DIR/bin/thebigbos"
ln -sf "$INSTALL_DIR/bin/thebigbos" "$BIN_DIR/thebigbos"
echo "  Wrapper: $BIN_DIR/thebigbos"

# 6. Default config
echo "[6/6] Setting up config..."
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp "$INSTALL_DIR/repo/thebigbos.json" "$CONFIG_DIR/config.json"
    echo "  Created default config: $CONFIG_DIR/config.json"
else
    echo "  Config already exists"
fi

# PATH reminder
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "  [!] Add to your shell profile:"
    echo "      export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "============================================"
echo "  TheBigBos installed!"
echo "============================================"
echo ""
echo "  Run: thebigbos setup"
echo "       thebigbos"
echo ""
