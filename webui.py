#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def read_url_file(path: Path) -> str | None:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return None

FRONTEND_DIR = Path(__file__).parent / "frontend"

ollama_url = read_url_file(FRONTEND_DIR / "ollama_url.txt")
cdp_url   = read_url_file(FRONTEND_DIR / "cdp_url.txt")
vnc_url   = read_url_file(FRONTEND_DIR / "vnc_url.txt")

if ollama_url:
    os.environ["OLLAMA_BASE_URL"] = ollama_url
    os.environ["OLLAMA_ENDPOINT"] = ollama_url
    print(f"✅ OLLAMA_BASE_URL set to {ollama_url}")
else:
    print("⚠️ frontend/ollama_url.txt not found")

if cdp_url:
    if cdp_url.startswith("https://"):
        cdp_url = "wss://" + cdp_url[8:]
    elif cdp_url.startswith("http://"):
        cdp_url = "ws://" + cdp_url[7:]
    os.environ["CDP_URL"] = cdp_url
    print(f"✅ CDP_URL set to {cdp_url}")
else:
    print("⚠️ frontend/cdp_url.txt not found")

if vnc_url:
    os.environ["VNC_URL"] = vnc_url
    print(f"✅ VNC_URL set to {vnc_url}")
else:
    print("⚠️ frontend/vnc_url.txt not found")

# Import UI only after env vars are set
from src.webui.interface import theme_map, create_ui

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7788)
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys())
    args = parser.parse_args()
    demo = create_ui(theme_name=args.theme)
    demo.queue().launch(server_name=args.ip, server_port=args.port)

if __name__ == "__main__":
    main()
