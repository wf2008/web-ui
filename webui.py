import os
import argparse
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from src.webui.interface import theme_map, create_ui

# Load environment variables from .env file
load_dotenv()

# ------------------------------------------------------------------
# Helper: read a URL from a file
# ------------------------------------------------------------------
def read_url_file(path: Path) -> str | None:
    """Read a URL from a text file. Returns None if file does not exist."""
    try:
        with open(path, "r") as f:
            url = f.read().strip()
            return url if url else None
    except (FileNotFoundError, OSError):
        return None

# ------------------------------------------------------------------
# Helper: write a URL to a file (for debugging)
# ------------------------------------------------------------------
def write_url_file(path: Path, url: str):
    """Write a URL to a text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(url)

# ------------------------------------------------------------------
# Set environment variable from file content
# ------------------------------------------------------------------
def set_env_from_file(file_path: Path, env_var: str, convert_to_wss: bool = False):
    """Read URL from file and set as environment variable."""
    url = read_url_file(file_path)
    if url:
        if convert_to_wss and url.startswith("https://"):
            url = "wss://" + url[8:]
        elif convert_to_wss and url.startswith("http://"):
            url = "ws://" + url[7:]
        os.environ[env_var] = url
        print(f"✅ Set {env_var} from {file_path} -> {url}")
    else:
        print(f"⚠️ {file_path} not found – using existing environment or defaults")

# ------------------------------------------------------------------
# Wait for Ollama API to be reachable (with retries)
# ------------------------------------------------------------------
def wait_for_ollama(base_url: str, max_retries: int = 30, delay: int = 5) -> bool:
    """
    Poll Ollama's /api/tags endpoint until it responds successfully.
    Returns True if ready, False otherwise.
    """
    if not base_url:
        print("❌ No Ollama URL provided, cannot wait.")
        return False

    # Ensure the URL does not end with a slash
    base_url = base_url.rstrip("/")
    tags_url = f"{base_url}/api/tags"

    for i in range(max_retries):
        try:
            resp = requests.get(tags_url, timeout=10)
            if resp.status_code == 200:
                print(f"✅ Ollama is ready after {i * delay} seconds.")
                # Print available models to confirm the service is working
                models = resp.json().get("models", [])
                if models:
                    names = [m.get("name", "unknown") for m in models]
                    print(f"   Available models: {', '.join(names)}")
                return True
            else:
                print(f"⏳ Ollama not ready (HTTP {resp.status_code}), retrying...")
        except requests.exceptions.RequestException as e:
            print(f"⏳ Ollama not reachable ({e}), retrying...")
        time.sleep(delay)

    print("❌ Ollama did not become ready within the timeout period.")
    return False

# ------------------------------------------------------------------
# Read the three tunnel files and set environment variables
# ------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).parent / "frontend"

# 1. Ollama API endpoint (HTTP)
set_env_from_file(FRONTEND_DIR / "ollama_url.txt", "OLLAMA_BASE_URL", convert_to_wss=False)
set_env_from_file(FRONTEND_DIR / "ollama_url.txt", "OLLAMA_ENDPOINT", convert_to_wss=False)

# 2. Chrome DevTools Protocol endpoint (WebSocket) – used by the browser agent
set_env_from_file(FRONTEND_DIR / "cdp_url.txt", "CDP_URL", convert_to_wss=True)

# 3. VNC noVNC endpoint (HTTP) – used by the Gradio iframe
set_env_from_file(FRONTEND_DIR / "vnc_url.txt", "VNC_URL", convert_to_wss=False)

# Set a dummy OpenAI API key to prevent the UI from defaulting to OpenAI
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "ollama-no-key-needed"

# ------------------------------------------------------------------
# Wait for Ollama to become responsive
# ------------------------------------------------------------------
ollama_url = os.environ.get("OLLAMA_ENDPOINT") or os.environ.get("OLLAMA_BASE_URL")
if ollama_url:
    wait_for_ollama(ollama_url, max_retries=30, delay=5)
else:
    print("⚠️ No Ollama URL set – the UI will show a connection error.")

# ------------------------------------------------------------------
# Original main function (unchanged)
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
