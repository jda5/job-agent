#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "=============================="
echo "  Job Agent — Setup"
echo "=============================="
echo ""

# ── 1. Check platform ──────────────────────────────────────────────────────────
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This installer is designed for macOS.${NC}"
    exit 1
fi

# ── 2. Install uv if needed ────────────────────────────────────────────────────
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v uv &> /dev/null; then
    echo "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    echo -e "${GREEN}✓ uv installed${NC}"
else
    echo -e "${GREEN}✓ uv already installed${NC}"
fi

# ── 3. Install Python dependencies ────────────────────────────────────────────
echo ""
echo "Installing Python dependencies..."
cd "$DIR"
uv sync
echo -e "${GREEN}✓ Dependencies ready${NC}"

# ── 4. Configure API key ───────────────────────────────────────────────────────
echo ""
if [ -f "$DIR/.env" ]; then
    echo -e "${GREEN}✓ API key already configured (.env exists)${NC}"
    read -p "  Re-enter your API key to update it, or press Enter to skip: " api_key
    if [ -n "$api_key" ]; then
        echo "OPENAI_API_KEY=$api_key" > "$DIR/.env"
        echo -e "${GREEN}✓ API key updated${NC}"
    fi
else
    echo "You need an OpenAI API key to use Job Agent."
    echo "Get one at: https://platform.openai.com/api-keys"
    echo ""
    read -p "  Enter your OpenAI API key: " api_key
    if [ -n "$api_key" ]; then
        echo "OPENAI_API_KEY=$api_key" > "$DIR/.env"
        echo -e "${GREEN}✓ API key saved${NC}"
    else
        echo -e "${YELLOW}! No key entered — edit .env manually before running the app.${NC}"
    fi
fi

# ── 5. Make launcher executable ────────────────────────────────────────────────
chmod +x "$DIR/Launch Job Agent.command"

echo ""
echo "=============================="
echo -e "${GREEN}  Setup complete!${NC}"
echo "=============================="
echo ""
echo "To run Job Agent, double-click 'Launch Job Agent.command' in Finder."
echo ""
echo "Note: The first time you open it, macOS may block it."
echo "If that happens: right-click the file → Open → Open."
echo ""
