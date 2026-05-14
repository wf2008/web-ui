from dotenv import load_dotenv
load_dotenv()

import os
import argparse
from pathlib import Path
from src.webui.interface import theme_map, create_ui

# ------------------------------------------------------------
# Helper: read a URL from a file and convert protocol if needed
# ------------------------------------------------------------
def read_url_file(path: str) -> str | None:
    try:
        with open(path, "r") as f:
            url = f.read().strip()
            return url if url else None
    except (FileNotFoundError, OSError):
        return None

def set_env_from_file(file_path: str, env_var: str, convert_to_wss: bool = False):
    """Read a URL from a file and set it as an environment variable."""
    url = read_url_file(file_path)
    if url:
        if convert_to_wss and url.startswith("https://"):
            url = "wss://" + url[8:]
        elif convert_to_wss and url.startswith("http://"):
            url = "ws://" + url[7:]
        os.environ[env_var] = url
        print(f"✅ Set {env_var} from {file_path} -> {url}")
    else:
        print(f"⚠️ {file_path} not found, using existing environment or defaults")

# ------------------------------------------------------------
# Override environment variables with the three URL files
# ------------------------------------------------------------
FRONTEND_DIR = Path(__file__).parent / "frontend"

# 1. Ollama API endpoint (HTTP)
set_env_from_file(FRONTEND_DIR / "ollama_url.txt", "OLLAMA_BASE_URL", convert_to_wss=False)

# 2. Chrome DevTools Protocol endpoint (WebSocket) – used by the browser agent
set_env_from_file(FRONTEND_DIR / "cdp_url.txt", "CDP_URL", convert_to_wss=True)

# 3. VNC noVNC endpoint (HTTP) – used by the Gradio iframe
set_env_from_file(FRONTEND_DIR / "vnc_url.txt", "VNC_URL", convert_to_wss=False)

# ------------------------------------------------------------
# Original main function (unchanged)
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)
    demo.queue().launch(server_name=args.ip, server_port=args.port)


if __name__ == '__main__':
    main()
