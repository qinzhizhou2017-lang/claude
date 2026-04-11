#!/usr/bin/env bash
# ============================================================
#  Hermes Agent - Automated Installation Script
#  https://github.com/NousResearch/hermes-agent
#
#  Supported platforms: Linux, macOS, WSL2, Android (Termux)
# ============================================================

set -euo pipefail

HERMES_DIR="${HERMES_HOME:-$HOME/.hermes}"
REPO_URL="https://github.com/NousResearch/hermes-agent.git"
PYTHON_VERSION="3.11"
VENV_DIR="$HERMES_DIR/venv"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Platform Detection ---
detect_platform() {
    case "$(uname -s)" in
        Linux*)
            if [ -d "/data/data/com.termux" ]; then
                PLATFORM="termux"
            else
                PLATFORM="linux"
            fi
            ;;
        Darwin*)  PLATFORM="macos" ;;
        MINGW*|CYGWIN*|MSYS*) error "Native Windows is not supported. Use WSL2."; exit 1 ;;
        *)        error "Unsupported platform: $(uname -s)"; exit 1 ;;
    esac
    info "Detected platform: $PLATFORM"
}

# --- Dependency Checks ---
check_python() {
    if command -v python3 &>/dev/null; then
        PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
            ok "Python $PY_VER found"
            return 0
        else
            warn "Python $PY_VER found, but 3.11+ is required"
        fi
    fi
    return 1
}

install_python() {
    info "Installing Python $PYTHON_VERSION..."
    case "$PLATFORM" in
        linux)
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y -qq software-properties-common
                sudo add-apt-repository -y ppa:deadsnakes/ppa
                sudo apt-get update -qq
                sudo apt-get install -y -qq python3.11 python3.11-venv python3.11-dev
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y python3.11 python3.11-devel
            elif command -v pacman &>/dev/null; then
                sudo pacman -S --noconfirm python
            else
                error "Could not determine package manager. Please install Python 3.11+ manually."
                exit 1
            fi
            ;;
        macos)
            if command -v brew &>/dev/null; then
                brew install python@3.11
            else
                error "Homebrew not found. Install it from https://brew.sh or install Python 3.11+ manually."
                exit 1
            fi
            ;;
        termux)
            pkg install -y python
            ;;
    esac
}

install_uv() {
    if command -v uv &>/dev/null; then
        ok "uv package manager already installed"
        return 0
    fi
    info "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    ok "uv installed"
}

install_git() {
    if command -v git &>/dev/null; then
        ok "git already installed"
        return 0
    fi
    info "Installing git..."
    case "$PLATFORM" in
        linux)
            if command -v apt-get &>/dev/null; then
                sudo apt-get install -y -qq git
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y git
            fi
            ;;
        macos)   brew install git ;;
        termux)  pkg install -y git ;;
    esac
}

# --- Main Installation ---
clone_repo() {
    if [ -d "$HERMES_DIR/repo" ]; then
        info "Updating existing Hermes Agent repository..."
        cd "$HERMES_DIR/repo"
        git pull origin main
    else
        info "Cloning Hermes Agent repository..."
        git clone "$REPO_URL" "$HERMES_DIR/repo"
    fi
    ok "Repository ready at $HERMES_DIR/repo"
}

setup_venv() {
    info "Creating Python virtual environment..."
    cd "$HERMES_DIR/repo"
    uv venv "$VENV_DIR" --python "$PYTHON_VERSION"
    ok "Virtual environment created at $VENV_DIR"
}

install_deps() {
    info "Installing Hermes Agent dependencies..."
    cd "$HERMES_DIR/repo"
    source "$VENV_DIR/bin/activate"

    if [ "$PLATFORM" = "termux" ]; then
        uv pip install -e ".[termux]"
    else
        uv pip install -e ".[all]"
    fi

    ok "Dependencies installed"
}

setup_shell_alias() {
    local shell_rc=""
    if [ -n "${ZSH_VERSION:-}" ] || [ -f "$HOME/.zshrc" ]; then
        shell_rc="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        shell_rc="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        shell_rc="$HOME/.bash_profile"
    fi

    if [ -z "$shell_rc" ]; then
        warn "Could not detect shell config. Add the following manually:"
        echo "  export PATH=\"$VENV_DIR/bin:\$PATH\""
        return
    fi

    local marker="# >>> hermes-agent >>>"
    if grep -q "$marker" "$shell_rc" 2>/dev/null; then
        info "Shell config already contains Hermes Agent path"
    else
        info "Adding Hermes Agent to $shell_rc..."
        cat >> "$shell_rc" << EOF

$marker
export HERMES_HOME="$HERMES_DIR"
export PATH="$VENV_DIR/bin:\$PATH"
# <<< hermes-agent <<<
EOF
        ok "Shell config updated"
    fi
}

create_config_dir() {
    mkdir -p "$HERMES_DIR/config"
    mkdir -p "$HERMES_DIR/skills"
    mkdir -p "$HERMES_DIR/memory"
    mkdir -p "$HERMES_DIR/logs"

    if [ ! -f "$HERMES_DIR/config/settings.yaml" ]; then
        cat > "$HERMES_DIR/config/settings.yaml" << 'YAML'
# Hermes Agent Configuration
# See: https://hermes-agent.nousresearch.com/docs/configuration

# --- LLM Provider ---
provider:
  # Options: nous, openrouter, openai, custom
  name: openrouter
  # model: nousresearch/hermes-3-llama-3.1-405b
  # api_key: your-api-key-here  # Or set OPENROUTER_API_KEY env var

# --- Terminal Backend ---
terminal:
  # Options: local, docker, ssh, daytona, singularity, modal
  backend: local

# --- Memory ---
memory:
  enabled: true
  auto_refresh: true

# --- Skills ---
skills:
  auto_learn: true
  marketplace: true

# --- Messaging Gateways (optional) ---
# gateway:
#   telegram:
#     token: your-telegram-bot-token
#   discord:
#     token: your-discord-bot-token
#   slack:
#     token: your-slack-bot-token

# --- Cron Scheduler (optional) ---
# cron:
#   enabled: false
#   jobs: []
YAML
        ok "Default configuration created at $HERMES_DIR/config/settings.yaml"
    fi
}

# --- Entry Point ---
main() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  Hermes Agent Installer${NC}"
    echo -e "${CYAN}  https://github.com/NousResearch/hermes-agent${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    detect_platform

    # Step 1: Dependencies
    info "Step 1/6: Checking dependencies..."
    install_git
    if ! check_python; then
        install_python
        check_python || { error "Python 3.11+ installation failed"; exit 1; }
    fi
    install_uv

    # Step 2: Clone
    info "Step 2/6: Cloning repository..."
    mkdir -p "$HERMES_DIR"
    clone_repo

    # Step 3: Virtual environment
    info "Step 3/6: Setting up virtual environment..."
    setup_venv

    # Step 4: Install dependencies
    info "Step 4/6: Installing dependencies..."
    install_deps

    # Step 5: Configuration
    info "Step 5/6: Creating configuration..."
    create_config_dir

    # Step 6: Shell integration
    info "Step 6/6: Setting up shell integration..."
    setup_shell_alias

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "  Next steps:"
    echo -e "    1. ${CYAN}source ~/.bashrc${NC}  (or ~/.zshrc)"
    echo -e "    2. ${CYAN}hermes setup${NC}      Run interactive setup wizard"
    echo -e "    3. ${CYAN}hermes model${NC}      Select your LLM provider"
    echo -e "    4. ${CYAN}hermes${NC}            Start chatting!"
    echo ""
    echo -e "  Config:  ${YELLOW}$HERMES_DIR/config/settings.yaml${NC}"
    echo -e "  Logs:    ${YELLOW}$HERMES_DIR/logs/${NC}"
    echo -e "  Docs:    ${CYAN}https://hermes-agent.nousresearch.com/docs${NC}"
    echo ""
}

main "$@"
