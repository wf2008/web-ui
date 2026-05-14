#!/usr/bin/env python3
"""
Browser‑Use WebUI – fully self‑hosted with Ollama, remote CDP, and VNC.
Environment variables are set from frontend/*.txt files (committed by GitHub Actions).
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env first (if any)
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
# Set environment variables for the entire application
# ------------------------------------------------------------------
if ollama_url:
    os.environ["OLLAMA_BASE_URL"] = ollama_url
    os.environ["OLLAMA_ENDPOINT"] = ollama_url
    print(f"✅ OLLAMA_BASE_URL set to {ollama_url}")
else:
    print("⚠️ frontend/ollama_url.txt not found – Ollama will not work")

if cdp_url:
    # Convert http/https to ws/wss for WebSocket CDP
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
# Optional: wait for Ollama to be reachable
# ------------------------------------------------------------------
def wait_for_ollama(url: str, max_retries: int = 20, delay: int = 4) -> bool:
    if not url:
        return False
    for i in range(max_retries):
        try:
            import requests
            resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=5)
            if resp.status_code == 200:
                print(f"✅ Ollama ready after {i*delay} seconds")
                return True
        except Exception:
            pass
        print(f"⏳ Waiting for Ollama... ({i+1}/{max_retries})")
        time.sleep(delay)
    print("⚠️ Ollama did not become ready – UI may show connection errors")
    return False

if ollama_url:
    wait_for_ollama(ollama_url)

# ------------------------------------------------------------------
# Now import the Gradio UI (after environment variables are set)
# ------------------------------------------------------------------
try:
    from src.webui.interface import theme_map, create_ui
except ImportError as e:
    print(f"❌ Failed to import UI: {e}", file=sys.stderr)
    sys.exit(1)

# ------------------------------------------------------------------
# Main entry point
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
