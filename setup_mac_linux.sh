#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo " Adaptive AI Astronomy Tutor Setup"
echo " macOS / Linux"
echo "=============================================="

# Pick Python command
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "Python was not found. Please install Python 3.10+ first."
  echo "Download: https://www.python.org/downloads/"
  exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create local virtual environment
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate
python -m pip install --upgrade pip

if [ -f "requirements.txt" ]; then
  echo "Installing Python requirements..."
  pip install -r requirements.txt
fi

echo "Checking Ollama..."
if command -v ollama >/dev/null 2>&1; then
  echo "Ollama found. Pulling required local models..."
  ollama pull llama3.1
  ollama pull mistral
else
  echo "Ollama was not found."
  echo "Install Ollama from: https://ollama.com/download"
  echo "After installing, run:"
  echo "  ollama pull llama3.1"
  echo "  ollama pull mistral"
fi

echo ""
echo "Setup complete."
echo "To run the GUI:"
echo "  ./run_gui.sh"
echo ""
echo "If Ollama is installed, make sure it is running before using AI features."
echo "You can start it with: ollama serve"
