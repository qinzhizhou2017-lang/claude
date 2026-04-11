#!/usr/bin/env bash
# ============================================================
#  Hermes Agent - Developer Setup Script
#  For contributors who want to develop/modify Hermes Agent
# ============================================================

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

DEV_DIR="${1:-$(pwd)/hermes-agent-dev}"

main() {
    echo ""
    echo -e "${CYAN}=======================================${NC}"
    echo -e "${CYAN}  Hermes Agent - Developer Setup${NC}"
    echo -e "${CYAN}=======================================${NC}"
    echo ""

    # Step 1: Check prerequisites
    info "Checking prerequisites..."

    if ! command -v git &>/dev/null; then
        error "git is required. Please install it first."
        exit 1
    fi
    ok "git found"

    # Install uv if not present
    if ! command -v uv &>/dev/null; then
        info "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    ok "uv found"

    # Step 2: Clone repository
    info "Cloning Hermes Agent repository into $DEV_DIR..."
    if [ -d "$DEV_DIR" ]; then
        warn "Directory already exists, pulling latest changes..."
        cd "$DEV_DIR"
        git pull origin main
    else
        git clone https://github.com/NousResearch/hermes-agent.git "$DEV_DIR"
        cd "$DEV_DIR"
    fi
    ok "Repository cloned"

    # Step 3: Create virtual environment
    info "Creating virtual environment with Python 3.11..."
    uv venv venv --python 3.11
    source venv/bin/activate
    ok "Virtual environment ready"

    # Step 4: Install in development mode
    info "Installing in development mode (all extras + dev dependencies)..."
    uv pip install -e ".[all,dev]"
    ok "Dependencies installed"

    # Step 5: Run tests
    info "Running test suite to verify installation..."
    if python -m pytest tests/ -q 2>/dev/null; then
        ok "All tests passed"
    else
        warn "Some tests failed - this may be expected if API keys are not configured"
    fi

    # Step 6: Initialize git submodules (optional RL training)
    info "Initializing git submodules (Atropos RL)..."
    if git submodule update --init tinker-atropos 2>/dev/null; then
        uv pip install -e "./tinker-atropos" 2>/dev/null || true
        ok "Atropos RL environment initialized"
    else
        warn "Atropos submodule not available (optional)"
    fi

    echo ""
    echo -e "${GREEN}=======================================${NC}"
    echo -e "${GREEN}  Developer Setup Complete!${NC}"
    echo -e "${GREEN}=======================================${NC}"
    echo ""
    echo -e "  Development directory: ${YELLOW}$DEV_DIR${NC}"
    echo ""
    echo -e "  To start developing:"
    echo -e "    ${CYAN}cd $DEV_DIR${NC}"
    echo -e "    ${CYAN}source venv/bin/activate${NC}"
    echo -e "    ${CYAN}hermes${NC}"
    echo ""
    echo -e "  Useful commands:"
    echo -e "    ${CYAN}python -m pytest tests/ -q${NC}    Run tests"
    echo -e "    ${CYAN}hermes doctor${NC}                 Check system health"
    echo -e "    ${CYAN}hermes config set${NC}             Adjust settings"
    echo ""
}

main "$@"
