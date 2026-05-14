#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------
# Helper: read a URL from a text file
# ------------------------------------------------------------------
def read_url_file(path: Path) -> str | None:
    try:
        with open(path, "r") as f:
            url = f.read().strip()
            return url if url else None
    except (FileNotFoundError, OSError):
        return None

# ------------------------------------------------------------------
# Read the three tunnel files (written by GitHub Actions)
# ------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).parent / "frontend"

ollama_url = read_url_file(FRONTEND_DIR / "ollama_url.txt")
cdp_url   = read_url_file(FRONTEND_DIR / "cdp_url.txt")
vnc_url   = read_url_file(FRONTEND_DIR / "vnc_url.txt")

# ------------------------------------------------------------------
# Set environment variables
# ------------------------------------------------------------------
if ollama_url:
    os.environ["OLLAMA_BASE_URL"] = ollama_url
    os.environ["OLLAMA_ENDPOINT"] = ollama_url
    print(f"✅ OLLAMA_BASE_URL set to {ollama_url}")
else:
    print("⚠️ frontend/ollama_url.txt not found – Ollama will not work")

if cdp_url:
    if cdp_url.startswith("https://"):
        cdp_url = "wss://" + cdp_url[8:]
    elif cdp_url.startswith("http://"):
        cdp_url = "ws://" + cdp_url[7:]
    os.environ["CDP_URL"] = cdp_url
    print(f"✅ CDP_URL set to {cdp_url}")
else:
    print("⚠️ frontend/cdp_url.txt not found – browser agent will not work")

if vnc_url:
    os.environ["VNC_URL"] = vnc_url
    print(f"✅ VNC_URL set to {vnc_url}")
else:
    print("⚠️ frontend/vnc_url.txt not found – VNC tab will show offline")

# ------------------------------------------------------------------
# Import UI (after env vars are set)
# ------------------------------------------------------------------
try:
    from src.webui.interface import theme_map, create_ui
except ImportError as e:
    print(f"❌ Failed to import UI: {e}", file=sys.stderr)
    sys.exit(1)

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)
    demo.queue().launch(server_name=args.ip, server_port=args.port)

if __name__ == "__main__":
    main()
