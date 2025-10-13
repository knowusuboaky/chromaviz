import requests
from typing import List, Optional, Dict, Any
from flask import Flask, jsonify, request, render_template
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from chromaviz import visualize_collection
import socket
import webbrowser
import threading
from datetime import datetime
from urllib.parse import urlparse
import numpy as np
import json
import subprocess
import psutil
import shutil
import os
from sentence_transformers import SentenceTransformer
import time
import sys
import signal
import pprint
import re
import random





# Static variable, i update this manually each time i make a change
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
appversion_flask = "1.0.0.3000"
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




# Initialize Flask app
app = Flask(__name__)




# NOTES FOR THE BELOW:
# DO NOT CONFIGURE THESE - they are merely placeholders 
# ALL settings are now extracted from appsettings.json in the root folder
# if one doesnt exist, a default is copied in from /default-config
# if that doesnt exist (for any reason)  a manual one is written out instead to cover all bases. 
# =========================================================================================
address_flask = ''
CHROMA_DATA_PATH = ""
EMBEDMODEL = ""
EMBEDMODEL_LOCAL_PATH = ""
EMBEDMODEL_CONTEXTWINDOW = 128
PROXY_URL = "" 
CHROMAVIZ_PORT = 5013
CHROMAVIZ_HOST = "127.0.0.1"
# ==========================================================================================



# Function to check for appsettings.json, and copy one or create one if it doesnt exist. 
def check_or_create_app_settings_json():
    print("\nChecking for appsettings.json...\n")
    
    root_path = os.getcwd()
    appsettings_path = os.path.join(root_path, 'appsettings.json')
    default_config_path = os.path.join(root_path, 'default-config', 'appsettings.json')
    
    if os.path.exists(appsettings_path):
        print(f"###############################################")
        print("appsettings.json found in the root folder.")
        print(f"###############################################")
        return

    if os.path.exists(default_config_path):
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("appsettings.json not found in the root folder.")
        print("Found default config at /default-config/appsettings.json.")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        print("Copying default config to root...\n")
        shutil.copy(default_config_path, appsettings_path)
        print(f"##############################################################")
        print(f"Default config copied to\n{appsettings_path}")
        print(f"##############################################################")
        return

    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("No appsettings.json found in the root folder.")
    print("No default config found in /default-config.")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("Creating a default appsettings.json file in the root...\n")
    
    if os.name == "nt":
        # Use user-writable paths on Windows to avoid permissions errors
        default_config = {
            "flask_server_endpoint": "http://127.0.0.1:5000",
            "proxy_endpoint": "",
            "chromaDB_path": r".\chroma-data",
            "embedding_model_selected_preset": "all-MiniLM-L6-v2",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_context_window": 512,
            "embedding_model_dimension": 384,
            "embedding_model_path": r".\models\all-MiniLM-L6-v2",
            "language": "en-GB",
            "CPURAMIntervalEnabled": False,
            "CPURAMInterval": 2000,
            "autoGenCollectionName": "testCollection",
            "bugFix100DocumentsEnabled": True,
            "bugFix100DocumentsBatchSize": 50000
        }
    else:
        # Docker/Linux-friendly defaults
        default_config = {
            "flask_server_endpoint": "http://0.0.0.0:5000",
            "proxy_endpoint": "",
            "chromaDB_path": "/app/chroma-data",
            "embedding_model_selected_preset": "all-MiniLM-L6-v2",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_context_window": 512,
            "embedding_model_dimension": 384,
            "embedding_model_path": "/app/models/all-MiniLM-L6-v2",
            "language": "en-GB",
            "CPURAMIntervalEnabled": False,
            "CPURAMInterval": 2000,
            "autoGenCollectionName": "testCollection",
            "bugFix100DocumentsEnabled": True,
            "bugFix100DocumentsBatchSize": 50000
        }

    with open(appsettings_path, 'w', encoding="utf-8") as f:
        json.dump(default_config, f, indent=4)

    print(f"###############################################################")
    print(f"Default appsettings.json Manually written to\n{appsettings_path}")
    print(f"###############################################################")


# Check for the appsettings.json file before doing anything 
check_or_create_app_settings_json()



# Function to load settings from appsettings.json
def load_settings_from_json(file_path: str):
    defaults = {
        "flask_server_endpoint": "http://127.0.0.1:5000",
        "proxy_endpoint": "",
        "chromaDB_path": "./chroma-data",
        "embedding_model_selected_preset": "all-MiniLM-L6-v2",
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_context_window": 512,
        "embedding_model_dimension": 384,
        "embedding_model_path": "./models/all-MiniLM-L6-v2",
        "language": "en-GB",
        "CPURAMIntervalEnabled": False,
        "CPURAMInterval": 2000,
        "autoGenCollectionName": "testCollection",
        "bugFix100DocumentsEnabled": True,
        "bugFix100DocumentsBatchSize": 50000,
    }

    # Read JSON; if missing/empty/invalid, write defaults
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            raise ValueError("settings file is empty")
        settings = json.loads(raw)
    except Exception as e:
        print(f"[load_settings_from_json] {e}; writing defaults to {file_path}")
        settings = defaults
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

    def _norm_path(p: str) -> str:
        return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))

    def _getenv(name, fallback):
        v = os.getenv(name)
        return v if v not in (None, "") else fallback

    global address_flask, CHROMA_DATA_PATH, EMBEDMODEL, EMBEDMODEL_LOCAL_PATH
    global EMBEDMODEL_CONTEXTWINDOW, PROXY_URL, CHROMAVIZ_PORT, CHROMAVIZ_HOST

    # Allow env vars to override the file
    address_flask = _getenv("FLASK_SERVER_ENDPOINT", settings.get("flask_server_endpoint", defaults["flask_server_endpoint"]))
    PROXY_URL = _getenv("PROXY_ENDPOINT", settings.get("proxy_endpoint", defaults["proxy_endpoint"]))
    CHROMA_DATA_PATH = _norm_path(_getenv("CHROMA_DB_PATH", settings.get("chromaDB_path", defaults["chromaDB_path"])))
    EMBEDMODEL = _getenv("EMBEDDING_MODEL", settings.get("embedding_model", defaults["embedding_model"]))
    EMBEDMODEL_LOCAL_PATH = _norm_path(_getenv("EMBEDDING_MODEL_PATH", settings.get("embedding_model_path", defaults["embedding_model_path"])))
    EMBEDMODEL_CONTEXTWINDOW = int(_getenv("EMBEDDING_CONTEXT_WINDOW", settings.get("embedding_context_window", defaults["embedding_context_window"])))

    # Ensure important folders exist
    os.makedirs(CHROMA_DATA_PATH, exist_ok=True)
    os.makedirs(EMBEDMODEL_LOCAL_PATH, exist_ok=True)

    # Proxy envs if provided
    if PROXY_URL:
        os.environ['HTTP_PROXY'] = PROXY_URL
        os.environ['HTTPS_PROXY'] = PROXY_URL

    # Where to cache HF models
    os.environ.setdefault("HF_HOME", EMBEDMODEL_LOCAL_PATH)

    # Derive public host/port used by your viz and any browser-facing URLs
    parsed = urlparse(address_flask)
    base_port = parsed.port or int(os.getenv("FLASK_PORT", "5000"))

    host = parsed.hostname
    if not host or host == "0.0.0.0":
        host = "127.0.0.1"  # browsers shouldn't use 0.0.0.0

    # Allow override for reverse proxy / compose setups
    host = os.getenv("PUBLIC_HOST", host)
    public_port = int(os.getenv("PUBLIC_PORT", base_port))

    CHROMAVIZ_HOST = host
    CHROMAVIZ_PORT = public_port + 1

# Call this function to update global variables at the start of your application
load_settings_from_json("appsettings.json")







# If you're not using a proxy, simply comment out or leave these lines out
if PROXY_URL:
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL






# Print the config in a clean and readable format
print(f"\n\nFlask Web App:")
print(f"================================")
print(f"  Name:      Chroma Flow Studio")
print(f"  Version:   {appversion_flask}")
print("============================= Configuration ===========================================================")
print(f"  Flask Address:             {address_flask}")
print(f"  Chroma Data Path:          {CHROMA_DATA_PATH}")
print(f"  Embedding Model:           {EMBEDMODEL}")
print(f"  Embedding Model Path:      {EMBEDMODEL_LOCAL_PATH}")
print(f"  Embedding Context Window:  {EMBEDMODEL_CONTEXTWINDOW}")
print(f"  Proxy URL:                 {PROXY_URL if PROXY_URL else 'Not used'}")
print("=======================================================================================================")


print("""
        __                                  ______                      __            ___     
  _____/ /_  _________  ____ ___  ____ _   / __/ /___ _      __   _____/ /___  ______/ (_)___ 
 / ___/ __ \/ ___/ __ \/ __ `__ \/ __ `/  / /_/ / __ \ | /| / /  / ___/ __/ / / / __  / / __ \\
/ /__/ / / / /  / /_/ / / / / / / /_/ /  / __/ / /_/ / |/ |/ /  (__  ) /_/ /_/ / /_/ / / /_/ /
\___/_/ /_/_/   \____/_/ /_/ /_/\__,_/  /_/ /_/\____/|__/|__/  /____/\__/\__,_/\__,_/_/\____/ 
""")
print("\n\n")
time.sleep(3) 
print("Starting up... please wait...\n\n")



# Get Port numbers as separate variables from the host variables
# Parse the URLs and extract the port numbers
parsed_flask = urlparse(address_flask)

# Assign port numbers and host based on the parsed URLs (with safe fallbacks)
port_flask = parsed_flask.port or 5000
host_flask = parsed_flask.hostname or "127.0.0.1"

# Global variable to track connection status
client = None

# Create a persistent Chroma client (ensure path exists)
# os.makedirs(CHROMA_DATA_PATH, exist_ok=True)
# persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

def make_chroma_client():
    mode = os.getenv("CHROMA_MODE", "persistent").lower()
    if mode == "http":
        host = os.getenv("CHROMA_HTTP_HOST", "127.0.0.1")
        port = int(os.getenv("CHROMA_HTTP_PORT", "8000"))
        print(f"Connecting to Chroma HTTP at {host}:{port}")
        return chromadb.HttpClient(host=host, port=port)
    else:
        os.makedirs(CHROMA_DATA_PATH, exist_ok=True)
        print(f"Using local PersistentClient at: {CHROMA_DATA_PATH}")
        return chromadb.PersistentClient(path=CHROMA_DATA_PATH)

persistentChromaClient = make_chroma_client()



# ---- Embeddings: local OR HTTP server ---------------------------------------
class HttpEmbeddingFunction:
    """
    Minimal wrapper so Chroma can call a remote embeddings API.
    Expects a server that supports: POST {base_url}/embed?model=...
    Request body: {"texts": [...], "mode": "auto"}
    Response: {"vectors": [[float, ...], ...]}
    """
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 30,
        *,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        max_batch: Optional[int] = None,
        retries: int = 2,
        backoff: float = 0.5,
    ):
        import os, requests  # local import to avoid module-level side effects

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.verify = verify
        self.retries = max(0, int(retries))
        self.backoff = float(backoff)

        # Optional max batch size (env can override)
        env_max = os.getenv("EMBEDDINGS_HTTP_MAX_BATCH")
        self.max_batch = int(env_max) if (env_max and env_max.isdigit()) else max_batch

        # Reuse a session for performance; attach headers (e.g., auth)
        self.session = requests.Session()
        hdrs = dict(headers or {})
        token = os.getenv("EMBEDDINGS_HTTP_AUTH_TOKEN", "").strip()
        if token and not any(k.lower() == "authorization" for k in hdrs):
            hdrs["Authorization"] = f"Bearer {token}"
        # Default JSON content type (server may not require it but it's harmless)
        hdrs.setdefault("Content-Type", "application/json")
        self.session.headers.update(hdrs)

    def __call__(self, texts):
        import time

        # Accept a single string or an iterable of strings
        if isinstance(texts, str):
            inputs = [texts]
        else:
            inputs = list(texts or [])
        if not inputs:
            return []

        # Helper to split into batches
        def _chunks(seq, n):
            if not n or n <= 0:
                yield seq
                return
            for i in range(0, len(seq), n):
                yield seq[i : i + n]

        vectors_out = []
        for batch in _chunks(inputs, self.max_batch or 0):
            vecs = self._post_embed(batch)
            vectors_out.extend(vecs)

        # Sanity check length
        if len(vectors_out) != len(inputs):
            raise RuntimeError(
                f"Embedding server returned {len(vectors_out)} vectors for {len(inputs)} texts."
            )

        return vectors_out

    def _post_embed(self, batch):
        import time, json

        url = f"{self.base_url}/embed"
        params = {"model": self.model}
        payload = {"texts": list(batch), "mode": "auto"}

        last_err = None
        for attempt in range(self.retries + 1):
            resp = None
            try:
                resp = self.session.post(
                    url,
                    params=params,
                    json=payload,
                    timeout=self.timeout,
                    verify=self.verify,
                )
                resp.raise_for_status()

                # Parse and validate JSON
                data = resp.json()
                if not isinstance(data, dict) or "vectors" not in data:
                    raise ValueError("Response JSON missing 'vectors' key.")
                vectors = data["vectors"]
                if not isinstance(vectors, list):
                    raise ValueError("'vectors' must be a list.")

                # Ensure each vector is a list[float]
                out = []
                for v in vectors:
                    if not isinstance(v, (list, tuple)):
                        raise ValueError("Each embedding must be a list/tuple.")
                    # Force to float to avoid np types leaking
                    out.append([float(x) for x in v])
                return out

            except Exception as e:
                last_err = e
                # Backoff then retry (if any left)
                if attempt < self.retries:
                    sleep_for = self.backoff * (2 ** attempt)
                    time.sleep(sleep_for)
                else:
                    body = getattr(resp, "text", None) if resp is not None else None
                    raise RuntimeError(
                        f"HTTP embeddings request failed after {self.retries + 1} attempt(s): {e}. "
                        f"URL={url} params={params} "
                        f"{' body='+body[:500] if body else ''}"
                    ) from e


def make_embedding_function():
    """
    Decide at runtime if we use:
      - local SentenceTransformers (default), OR
      - remote HTTP server (EMBEDDINGS_MODE=http)
    Env vars:
      EMBEDDINGS_MODE:           'local' (default) | 'http'
      EMBEDDINGS_HTTP_URL:       e.g. 'http://embeddings:9005'
      EMBEDDINGS_HTTP_MODEL:     e.g. 'e5-large-v2' | 'mxbai' | 'arctic' | 'nomic' | 'bge-m3'
      EMBEDDINGS_HTTP_TIMEOUT:   seconds (default 30)
      EMBEDDINGS_HTTP_VERIFY:    'true' (default) | 'false'  # TLS verify for HTTPS endpoints
      CONTINUE_WITHOUT_EMBEDDINGS: 'true'|'false' (default true)
    """
    mode = os.getenv("EMBEDDINGS_MODE", "local").lower()
    continue_without = os.getenv("CONTINUE_WITHOUT_EMBEDDINGS", "true").lower() == "true"

    if mode == "http":
        base_url = os.getenv("EMBEDDINGS_HTTP_URL", "http://127.0.0.1:9005")
        model = os.getenv("EMBEDDINGS_HTTP_MODEL", "e5-large-v2")
        timeout = int(os.getenv("EMBEDDINGS_HTTP_TIMEOUT", "30"))

        # NEW: allow disabling TLS verification for self-signed certs, etc.
        verify_env = (os.getenv("EMBEDDINGS_HTTP_VERIFY", "true") or "").strip().lower()
        verify = verify_env in ("1", "true", "yes", "y", "on")

        print(f"[embeddings] Using HTTP server at {base_url} (model='{model}', verify={verify})")
        try:
            # Optional quick probe (respect verify); won't fail startup if it errors
            try:
                import requests
                requests.get(f"{base_url.rstrip('/')}/healthz", timeout=timeout, verify=verify)
            except Exception:
                pass

            # Pass verify through to the embedding function
            return HttpEmbeddingFunction(base_url, model, timeout=timeout, verify=verify)

        except Exception as e:
            print(f"[embeddings] ERROR creating HTTP embedding function: {e}")
            if continue_without:
                print("[embeddings] Continuing without embeddings.")
                return None
            sys.exit(1)

    # ---- LOCAL (fallback/default) ----
    try:
        print("\n\nPre-checks from embedding function...\nChecking Embedding Model Path exists and contains models....")
        local_model_ready = os.path.isdir(EMBEDMODEL_LOCAL_PATH) and len(os.listdir(EMBEDMODEL_LOCAL_PATH)) > 0

        if local_model_ready:
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print(f"Found - Loaded model from local path:\n{EMBEDMODEL_LOCAL_PATH}")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            return embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL_LOCAL_PATH)

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(f"Not Found Locally - Downloading model {EMBEDMODEL} from Hugging Face...")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        os.makedirs(EMBEDMODEL_LOCAL_PATH, exist_ok=True)
        model = SentenceTransformer(EMBEDMODEL)
        print("Saving Model to Embedding Path...")
        model.save(EMBEDMODEL_LOCAL_PATH)
        print(f"Model downloaded and saved to: {EMBEDMODEL_LOCAL_PATH}")
        print("Now Loading locally...")
        return embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL_LOCAL_PATH)

    except Exception as e:
        print(f"\nError loading local embeddings: {e}")
        print("Also check internet connection / proxy / HF connectivity, or set EMBEDDINGS_MODE=http.")
        if continue_without:
            print("Continuing as a viewer. Embeddings won't work.")
            return None
        sys.exit(1)

# Prepare embedding function via factory (local or HTTP)
pyEmbedFunction = make_embedding_function()  # None if continuing without embeddings


# Indicate that Flask will continue launching regardless of ChromaDB status
print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print(f"Launching Flask Web App on:\n{host_flask}:{port_flask}...")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


# Auto Launch Flask and Web App 
def open_browser():
    IN_DOCKER = os.path.exists("/.dockerenv")
    AUTO_OPEN_BROWSER = os.getenv("AUTO_OPEN_BROWSER", "false").lower() == "true"
    if not IN_DOCKER and AUTO_OPEN_BROWSER:
        time.sleep(4)
        webbrowser.open(address_flask)


@app.route('/')
def index():
    # Serve the HTML page when the root is accessed
    return app.send_static_file('index.html')


# Function to clear and reinitialize the app components
def reinitialize_app():
    # reload settings so env/paths/ports are up to date
    load_settings_from_json("appsettings.json")
    global client, persistentChromaClient, pyEmbedFunction

    # drop any cached client handles if you use them elsewhere
    client = None

    # recreate the Chroma client (important if CHROMA_MODE/host/port changed)
    persistentChromaClient = make_chroma_client()

    # recreate the embedding function according to EMBEDDINGS_MODE
    print("\n\nReinitializing embedding function...")
    pyEmbedFunction = make_embedding_function()

    # (optional) log what we're using for quick visibility
    print(f"[reinit] embeddings mode: {os.getenv('EMBEDDINGS_MODE', 'local')}")
    if os.getenv('EMBEDDINGS_MODE', 'local').lower() == 'local':
        print(f"[reinit] local model path: {EMBEDMODEL_LOCAL_PATH}")



# Example route to restart (reinitialize) the Flask server without killing the process
@app.route('/restart', methods=['GET'])
def restart():
    # Call this function to update global variables at the start of your application
    load_settings_from_json("appsettings.json")

    """Endpoint to restart/reinitialize the server"""
    print("Reinitializing the app components...")
    
    # Run the reinitialization in a separate thread to avoid blocking the request
    threading.Thread(target=reinitialize_app).start()
    
    time.sleep(2) 
    return jsonify(message="Server components are being reinitialized. Please wait..."), 200


@app.route('/read-settings', methods=['GET'])
def read_settings():
    try:
        # Open and read the appsettings.json file
        with open('appsettings.json', 'r') as file:
            settings = json.load(file)
        
        # Print the settings to the console
        print(json.dumps(settings, indent=4))  # Print nicely formatted JSON

        # Call this function to update global variables at the start of your application
        load_settings_from_json('appsettings.json')

        # Return a response (could be the same data or a success message)
        return jsonify({"status": "success", "settings": settings}), 200

    except Exception as e:
        # Handle error (file not found, JSON parse error, etc.)
        print(f"Error reading settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/save-settings', methods=['POST'])
def save_settings():
    try:
        # Get the JSON data from the request
        updated_settings = request.get_json()
        
        # Save the settings back to appsettings.json
        with open('appsettings.json', 'w') as file:
            json.dump(updated_settings, file, indent=4)
        
        # Call this function to update global variables at the start of your application
        load_settings_from_json("appsettings.json")

        # Return a success response
        return jsonify({"status": "success", "message": "Settings saved successfully!"}), 200
    except Exception as e:
        # Handle errors (e.g., file write errors, invalid JSON)
        print(f"Error saving settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/write-default-config', methods=['POST'])
def write_default_config_route():
    print("Received request to manually write default config file.")
    print("Creating default JSON object...")

    # OS-aware defaults (user-writable on Windows; Docker/Linux-friendly paths)
    if os.name == "nt":
        default_config = {
            "flask_server_endpoint": "http://127.0.0.1:5000",
            "proxy_endpoint": "",
            "chromaDB_path": r".\chroma-data",
            "embedding_model_selected_preset": "all-MiniLM-L6-v2",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_context_window": 512,
            "embedding_model_dimension": 384,
            "embedding_model_path": r".\models\all-MiniLM-L6-v2",
            "language": "en-GB",
            "CPURAMIntervalEnabled": False,
            "CPURAMInterval": 2000,
            "autoGenCollectionName": "testCollection",
            "bugFix100DocumentsEnabled": True,
            "bugFix100DocumentsBatchSize": 50000
        }
    else:
        default_config = {
            "flask_server_endpoint": "http://0.0.0.0:5000",
            "proxy_endpoint": "",
            "chromaDB_path": "/app/chroma-data",
            "embedding_model_selected_preset": "all-MiniLM-L6-v2",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_context_window": 512,
            "embedding_model_dimension": 384,
            "embedding_model_path": "/app/models/all-MiniLM-L6-v2",
            "language": "en-GB",
            "CPURAMIntervalEnabled": False,
            "CPURAMInterval": 2000,
            "autoGenCollectionName": "testCollection",
            "bugFix100DocumentsEnabled": True,
            "bugFix100DocumentsBatchSize": 50000
        }

    appsettings_path = os.path.join(os.getcwd(), 'appsettings.json')

    print(f"DEBUG\nShowing config that will be written:\n{default_config}")

    try:
        # Ensure the directory exists (in case cwd is unusual)
        os.makedirs(os.path.dirname(appsettings_path) or ".", exist_ok=True)

        # Always overwrite the file with the default config
        with open(appsettings_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)

        return jsonify({
            "message": "Default configuration written successfully!",
            "path": appsettings_path
        }), 200

    except Exception as e:
        return jsonify({"message": f"Error writing default config: {e}"}), 500


@app.route('/system-stats', methods=['GET'])
def system_stats():
    # Get the system stats
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    return jsonify(cpu=cpu_usage, ram=ram_usage)



@app.route('/python-stats', methods=['GET'])
def python_stats():
    # Get the current process ID (PID)
    pid = os.getpid()
    
    # Get the process object for the current Python app
    process = psutil.Process(pid)
    
    # Get CPU usage of the current Python process
    cpu_usage = process.cpu_percent(interval=1)
    
    # Get memory usage of the current Python process
    ram_usage = process.memory_percent()
    
    return jsonify(cpu=cpu_usage, ram=ram_usage)



@app.route('/version', methods=['GET'])
def get_flask_app_version():

    if persistentChromaClient is None:
        # If the ChromaDB client is not initialized, return an error message
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    try:
        # Return global variable appversion_flask as a JSON object
        return jsonify({'flaskAppVersion': appversion_flask})

    except Exception as e:
        # Handle any error that occurs during the ChromaDB request
        return jsonify({'error': str(e)}), 500


@app.route('/version-chroma', methods=['GET'])
def get_chromadb_app_version():
    try:
        import chromadb
        return jsonify({"version": getattr(chromadb, "__version__", "unknown")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/embedmodelinfo', methods=['GET'])
def get_embedding_model_info():
    if persistentChromaClient is None:
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500
    try:
        mode = os.getenv("EMBEDDINGS_MODE", "local").lower()
        info = {
            "mode": mode,
            "embedding_model": EMBEDMODEL,
            "embedding_model_path": EMBEDMODEL_LOCAL_PATH,
            "embedding_model_context_window": EMBEDMODEL_CONTEXTWINDOW,
        }
        if mode == "http":
            info.update({
                "http_url": os.getenv("EMBEDDINGS_HTTP_URL", "http://127.0.0.1:9005"),
                "http_model": os.getenv("EMBEDDINGS_HTTP_MODEL", "e5-large-v2"),
                "http_timeout": int(os.getenv("EMBEDDINGS_HTTP_TIMEOUT", "30")),
            })
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/heartbeat', methods=['GET'])
def flask_heartbeat():
    return jsonify({'heartbeat': True})


def list_collection_names_safe(client) -> List[str]:
    """
    Returns collection names across Chroma versions:
    - v0.6+: list_collections() -> List[str]
    - v0.5.x: list_collections() -> List[Collection] (with .name)
    """
    cols = client.list_collections()
    names = []
    for c in cols:
        if isinstance(c, str):
            names.append(c)
        else:
            name = getattr(c, "name", None)
            if name:
                names.append(name)
    return names

@app.route('/get-collections', methods=['GET'])
def get_collections():
    print("=======================================")
    print("Received request for: /get-collections")
    print("=======================================")

    if persistentChromaClient is None:
        print("   FROM: /get-collections   ERROR: ChromaDB server is unavailable")
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    try:
        names = list_collection_names_safe(persistentChromaClient)
        payload = [{"name": n} for n in names]
        print("   FROM: /get-collections   Returning collections as JSON")
        return jsonify(payload), 200
    except Exception as e:
        print(f"   FROM: /get-collections   Error fetching collections: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/count-collections', methods=['GET'])
def count_collections():
    print("=========================================")
    print("Received request for: /count-collections")
    print("=========================================")

    if persistentChromaClient is None:
        print("   FROM: /count-collections   ERROR: ChromaDB server is unavailable")
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    try:
        # Use the version-agnostic helper introduced earlier
        names = list_collection_names_safe(persistentChromaClient)
        count = len(names)
        print(f"   FROM: /count-collections   Returning Collection Count: {count}")
        # Return a consistent object, not a bare JSON number
        return jsonify({'count': count}), 200
    except Exception as e:
        print(f"   FROM: /count-collections   Error counting Collections: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get-collection-overview', methods=['GET'])
def get_collection_overview():
    print("================================================")
    print("Received request for: /get-collection-overview")
    print("================================================")

    if persistentChromaClient is None:
        print("   FROM: /get-collection-overview   ERROR: ChromaDB server is unavailable")
        return jsonify({'status': 'error', 'message': 'ChromaDB server is unavailable'}), 500

    try:
        # version-agnostic: get names once
        names = list_collection_names_safe(persistentChromaClient)

        overview = []
        for name in names:
            try:
                coll = persistentChromaClient.get_collection(name, embedding_function=pyEmbedFunction)

                # count() may be None for corrupted/empty states; handle gracefully
                try:
                    doc_count = coll.count()
                except Exception as e:
                    print(f"   FROM: /get-collection-overview   count() failed for {name}: {e}")
                    doc_count = None

                overview.append({
                    'id': str(getattr(coll, 'id', 'unknown')),
                    'name': name,
                    'document_count': doc_count
                })
            except Exception as e:
                print(f"   FROM: /get-collection-overview   ERROR accessing collection {name}: {e}")
                overview.append({
                    'name': name,
                    'error': str(e)
                })

        print("   FROM: /get-collection-overview   SUCCESS - Returning Collection Overview as JSON")
        return jsonify({
            'status': 'success',
            'total_collections': len(overview),
            'collections': overview
        }), 200

    except Exception as e:
        print(f"   FROM: /get-collection-overview   Error getting Collection Overview: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/get-collection-details', methods=['GET'])
def get_collection_details():
    print(f"===================================================")
    print(f"Recevied request for: /api/get-collection-details")
    print(f"===================================================")

    if persistentChromaClient is None:
        print(f"   FROM: /api/get-collection-details   ERROR: ChromaDB server is unavailable")
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Extract collection name from the request's query parameters
    passed_collection_name = request.args.get("collection_name")
    if not passed_collection_name:
        print(f"   FROM: /api/get-collection-details   Collection name is required")
        return jsonify({'error': 'Collection name is required'}), 400

    print(f"   FROM: /api/get-collection-details   Passed Collection: {passed_collection_name}")

    try:
        # Try getting the collection details
        coll = persistentChromaClient.get_collection(passed_collection_name)

        # Extract the collection details and convert UUID fields to string safely
        collection_details = {
            'id': str(getattr(coll, 'id', 'unknown')),
            'name': getattr(coll, 'name', passed_collection_name),
            'tenant': getattr(coll, 'tenant', 'N/A'),
            'database': getattr(coll, 'database', 'N/A'),
            'metadata': getattr(coll, 'metadata', {}),
        }

        cfg = getattr(coll, "configuration_json", {}) or {}
        hnsw = cfg.get("hnsw_configuration") or {}
        collection_details.update({
            'config_name': hnsw.get('name', 'N/A'),
            'config_space': hnsw.get('space', 'N/A'),
            'config_ef_construction': hnsw.get('ef_construction', 'N/A'),
            'config_ef_search': hnsw.get('ef_search', 'N/A'),
            'config_num_threads': hnsw.get('num_threads', 'N/A'),
            'config_m': hnsw.get('m', 'N/A'),
            'config_resize_factor': hnsw.get('resize_factor', 'N/A'),
            'config_batch_size': hnsw.get('batch_size', 'N/A'),
            'config_sync_threshold': hnsw.get('sync_threshold', 'N/A'),
        })

        print(f"   FROM: /api/get-collection-details   SUCCESS - Returning {passed_collection_name} Details as JSON")
        return jsonify(collection_details)

    except Exception as e:
        print(f"   FROM: /api/get-collection-details   Error getting {passed_collection_name} Details: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/create-new-collection', methods=['POST'])
def create_new_collection():
    if persistentChromaClient is None:  # Assuming client is defined elsewhere
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Extract collection data from the request's JSON payload
    data = request.json
    passed_collection_name = data.get("collection_name")
    space = data.get("space")
    ef_construction = data.get("ef_construction")
    ef_search = data.get("ef_search")
    num_of_threads = data.get("num_of_threads")
    m = data.get("m")
    resize_factor = data.get("resize_factor")
    batch_size = data.get("batch_size")
    sync_threshold = data.get("sync_threshold")
    passed_metadata = data.get("metadata", {})

    # Debugging: print all extracted values to the server's log
    print(f"Received data:\ncollection_name={passed_collection_name},\nspace={space},\n"
          f"ef_construction={ef_construction},\nef_search={ef_search},\n"
          f"num_of_threads={num_of_threads},\nm={m},\nresize_factor={resize_factor},\n"
          f"batch_size={batch_size},\nsync_threshold={sync_threshold},\nmetadata={passed_metadata}\n")

    # Ensure collection name is provided
    if not passed_collection_name:
        return jsonify({'error': 'Collection name is required'}), 400

    try:
        # Try getting the collection first (doesn't raise exception if collection is not found)
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Existing Collection '{passed_collection_name}' found.")

        # If collection is found, no need to create it again, just return success
        return jsonify({"message": f"Collection '{passed_collection_name}' already exists."}), 200

    except Exception as e:
        # Handle unexpected errors
        print(f"{str(e)}")
        print(f"Collection not found, proceeding to create it...")

    try:
        # If collection is not found, proceed to create it
        # Check if metadata is provided and use it accordingly
        if passed_metadata:  # If metadata is not empty (not None or empty dict)
            pycollection = persistentChromaClient.create_collection(
                passed_collection_name,
                embedding_function=pyEmbedFunction,
                metadata=passed_metadata
            )
        else:
            pycollection = persistentChromaClient.create_collection(
                passed_collection_name,
                embedding_function=pyEmbedFunction
            )
    
        print(f"Created new collection '{passed_collection_name}' successfully.")
        
        return jsonify({"message": f"Collection '{passed_collection_name}' created successfully."}), 200
    
    except Exception as e:
        # Catch the error and return the actual error message
        error_message = str(e)
        print(f"Error occurred while creating collection '{passed_collection_name}': {error_message}")
        return jsonify({"error": f"Failed to create collection: {error_message}"}), 500


@app.route('/clone-new-collection', methods=['POST'])
def clone_new_collection():
    if persistentChromaClient is None:  # Assuming client is defined elsewhere
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Extract collection data from the request's JSON payload
    data = request.json
    passed_collection_name = data.get("collection_name")
    new_collection_name = data.get("new_collection_name")
    batch_limit = data.get('batch_limit', 100)  # Default to 100 if not provided

    # Debugging: print all extracted values to the server's log
    print(f"Received data:\ncollection_name={passed_collection_name}")
    print(f"Received data:\nnew_collection_name={new_collection_name}")
    print(f"Batch Limit: {batch_limit}")

    # Ensure collection name is provided
    if not passed_collection_name or not new_collection_name:
        return jsonify({'error': 'Collection name and new collection name are required'}), 400

    try:
        # Try getting the collection first (doesn't raise exception if collection is not found)
        pycollection_old = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Existing Collection '{passed_collection_name}' found.")

    except Exception as e:
        # Handle unexpected errors
        print(f"{str(e)}")
        return jsonify({"message": f"Collection '{passed_collection_name}' Not Found, aborting..."}), 404

    # Also confirm the new name doesn't already exist 
    try:
        pycollection_new = persistentChromaClient.get_collection(
            new_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"New Collection Name '{new_collection_name}' already exists, aborting.")
        return jsonify({"message": f"New Collection Name '{new_collection_name}' already exists, aborting."}), 567

    except Exception as e:
        # Handle unexpected errors
        print(f"New Collection Name '{new_collection_name}' is available...proceeding...")

    # Now extract the old ids, documents, and metadata into object variables
    old_collection_metadata = pycollection_old.metadata

    # Fetch the documents and their metadata
    old_results = pycollection_old.get(include=["documents", "metadatas"])

    old_doc_ids = old_results['ids']
    old_documents = old_results['documents']
    old_document_metadata = old_results['metadatas']

    # Now we need to create a new one with the same parameters
    try:
        if old_collection_metadata:  # If metadata is not empty
            pycollection_new = persistentChromaClient.create_collection(
                new_collection_name,
                embedding_function=pyEmbedFunction,
                metadata=old_collection_metadata
            )
        else:
            pycollection_new = persistentChromaClient.create_collection(
                new_collection_name,
                embedding_function=pyEmbedFunction
            )

        print(f"Created new collection '{new_collection_name}' from '{passed_collection_name}' successfully.")
    except Exception as e:
        print(f"Failed to create collection '{new_collection_name}': {str(e)}")
        return jsonify({'error': f'Failed to create new collection: {str(e)}'}), 500

    # Function to split documents into smaller batches
    def chunk_records(doc_ids, documents, metadata, batch_size):
        for i in range(0, len(doc_ids), batch_size):
            yield doc_ids[i:i + batch_size], documents[i:i + batch_size], metadata[i:i + batch_size]

    batches = chunk_records(old_doc_ids, old_documents, old_document_metadata, batch_limit)

    # Now we need to copy the data in batches
    try:
        print(f"Copying Data into New Cloned Collection...")
        
        # Process each batch separately
        for batch_ids, batch_documents, batch_metadata in batches:
            try:
                print(f"Upserting batch of size {len(batch_ids)}...")
                pycollection_new.upsert(
                    documents=batch_documents,
                    metadatas=batch_metadata,
                    ids=batch_ids
                )
                print(f"Upsert for batch successful!")

            except Exception as e:
                print(f"Error during upsert: {str(e)}")
                print(f"Deleting Cloned Collection to Rollback Changes...")
                persistentChromaClient.delete_collection(name=new_collection_name)

                # Check if the exception message contains "exceeds maximum batch size"
                if "exceeds maximum batch size" in str(e):
                    return jsonify({'error': f'Batch exceeds maximum size: {str(e)}'}), 566

                return jsonify({'error': f'Failed to upsert documents: {str(e)}'}), 500

        print(f"Clone Complete - Data migrated successfully.")
        return jsonify({"message": "Clone Complete - Data migrated successfully."}), 200

    except Exception as e:
        print(f"Error migrating documents to Cloned Collection: {str(e)}")
        print(f"Deleting Cloned Collection to Rollback Changes...")
        persistentChromaClient.delete_collection(name=new_collection_name)
        return jsonify({"error": f"Error migrating documents to Cloned Collection: {str(e)}"}), 500


@app.route('/api/delete-collection-v2', methods=['POST'])
def delete_collection():
    if persistentChromaClient is None:  # Assuming client is defined elsewhere
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Extract collection data from the request's JSON payload
    data = request.json
    passed_collection_name = data.get("collection_name")

    # Debugging: print all extracted values to the server's log
    print(f"Received data:\ncollection_name={passed_collection_name}")

    # Ensure collection name is provided
    if not passed_collection_name:
        return jsonify({'error': 'Collection name is required'}), 400

    try:
        # Try getting the collection first (doesn't raise exception if collection is not found)
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Existing Collection '{passed_collection_name}' found.")

        # If the collection exists, delete it
        persistentChromaClient.delete_collection(passed_collection_name)
        print(f"Collection '{passed_collection_name}' deleted successfully.")
        return jsonify({'message': f"Collection '{passed_collection_name}' deleted successfully."}), 200

    except Exception as e:
        # Handle unexpected errors
        print(f"Error: {str(e)}")
        return jsonify({'error': 'An error occurred while deleting the collection'}), 500


@app.route('/api/delete-all-collections-v2', methods=['POST'])
def delete_all_collections():
    print("=====================================================")
    print("Received request for: /api/delete-all-collections-v2")
    print("=====================================================")

    if persistentChromaClient is None:
        print("   FROM: /api/delete-all-collections-v2   ERROR: ChromaDB server is unavailable")
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    try:
        # Get collections (works across Chroma versions)
        cols = persistentChromaClient.list_collections()
        print("   FROM: /api/delete-all-collections-v2   Collections fetched")

        if not cols:
            print("   FROM: /api/delete-all-collections-v2   No collections found to delete")
            return jsonify({'message': 'No collections found to delete.'}), 200

        # Normalize to names (v0.6+: list[str], v0.5.x: list[Collection])
        names = []
        for c in cols:
            if isinstance(c, str):
                if c:
                    names.append(c.strip())
            else:
                name = getattr(c, "name", None)
                if name:
                    names.append(str(name).strip())

        # De-dupe & drop empties
        seen = set()
        names = [n for n in names if n and not (n in seen or seen.add(n))]

        deleted_collections = []
        failed_collections = []

        for name in names:
            try:
                persistentChromaClient.delete_collection(name)
                deleted_collections.append(name)
                print(f"Deleted collection: {name}")
            except Exception as e:
                failed_collections.append({'collection': name, 'error': str(e)})
                print(f"Failed to delete collection {name}: {e}")

        return jsonify({
            'deleted_collections': deleted_collections,
            'failed_collections': failed_collections
        }), 200

    except Exception as e:
        print(f"Error in delete_all_collections: {e}")
        return jsonify({'error': f'An error occurred while deleting all collections: {e}'}), 500


@app.route('/generate-embedding', methods=['POST'])
def generate_embedding():
    if pyEmbedFunction is None:
        return jsonify({"error": "Embeddings are disabled. Set EMBEDDINGS_MODE=local or http."}), 503


    data = request.get_json()
    input_string = data.get('text')
    if not input_string:
        return jsonify({"error": "No text provided"}), 400

    try:
        vectors = pyEmbedFunction([input_string])  # list[list[float]] or list[np.ndarray]
        vec = vectors[0]
        if isinstance(vec, np.ndarray):
            vec = vec.tolist()
        return jsonify({"embedding": vec})
    except Exception as e:
        return jsonify({"error": f"An error occurred while generating the embedding: {str(e)}"}), 500


@app.route('/api/add-document', methods=['POST'])
def add_document():
    print("=====================================================")
    print("Recevied request for: /api/add-document")
    print("=====================================================")

    data = request.get_json(silent=True) or {}

    collection_name = (data.get("collection_name") or "").strip()
    doc_id = str(data.get("id") or "").strip()
    doc_content = data.get("document")
    metadata = data.get("metadata", {}) or {}

    # Allow metadata as JSON string
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata) or {}
        except Exception:
            return jsonify({'error': 'metadata must be a JSON object (or JSON string representing an object)'}), 400

    if not collection_name or not doc_id or doc_content in (None, ""):
        return jsonify({'error': 'Missing required fields (collection_name, id, document)'}), 400

    try:
        coll = persistentChromaClient.get_collection(
            collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Collection {collection_name} found and retrieved.")
    except Exception as e:
        return jsonify({'error': f"Collection {collection_name} not found: {str(e)}"}), 500

    try:
        # Prefer direct existence check over fetching whole collection
        exists = False
        try:
            existing = coll.get(ids=[doc_id], include=['metadatas'])
            exists = bool(existing.get("ids") and doc_id in existing["ids"])
        except Exception:
            # If older server/version has trouble with targeted get, fall back to add() and catch duplicate error.
            pass

        if exists:
            return jsonify({'message': 'Document already exists'}), 409

        # Set defaults if missing
        metadata.setdefault("date_modified", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        metadata.setdefault("embedding_model", EMBEDMODEL)
        metadata.setdefault("embedding_model_context_window", EMBEDMODEL_CONTEXTWINDOW)

        # Add (not upsert) to catch accidental overwrite attempts
        coll.add(
            documents=[doc_content],
            metadatas=[metadata],
            ids=[doc_id]
        )

        return jsonify({'message': 'Document added successfully'}), 200

    except Exception as e:
        return jsonify({'error': f"Error adding document: {str(e)}"}), 500


@app.route('/api/add-many-test-document', methods=['POST'])
def add_many_test_documents():
    if persistentChromaClient is None:
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    data = request.get_json(silent=True) or {}
    passed_collection_name = (data.get("collection_name") or "").strip()

    if not passed_collection_name:
        return jsonify({'error': 'Missing required field: collection_name'}), 400

    print("Request to add multiple documents to collection.")
    print(f"Passed Collection Name: {passed_collection_name}")

    try:
        coll = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Collection {passed_collection_name} found and retrieved.")
    except Exception as e:
        return jsonify({'error': f"Collection {passed_collection_name} not found: {str(e)}"}), 500

    # --- Dummy data (unchanged) ---
    documents = [
        {"id": "doc_1", "document": "The football team trained intensely for the upcoming match. The football team dedicated themselves to an intense training regimen as they prepared for their upcoming match. Every player understood the importance of this game, and the atmosphere during practice was filled with focus and determination. Coaches pushed them harder than ever before, emphasizing fitness, technique, and mental toughness. Each drill was designed to sharpen their skills and build chemistry on the field. They practiced set pieces, defensive formations, and quick transitions, all with the goal of achieving perfection when game time arrived. The intensity of the training sessions was palpable. Sweat poured down the players' faces as they tirelessly ran drills under the watchful eyes of their coaches. Despite the exhaustion, there was a palpable sense of unity within the team. They were no longer just individuals; they were a collective, working toward a single goal. The upcoming match loomed large in their minds, and they knew that every moment spent on the field during training was one step closer to success. The players pushed each other to their limits, knowing that victory would depend on how well they executed everything they practiced.", "metadata": {"source": "sports","team_focus": True,"intensity_level": 8,"training_sessions": 5,"days_until_match": 4,"players_determined": True,"coaches_involved": True,"exhaustion_level": 7.5,"match_importance": 10,"team_spirit": True,"mental_preparation": True}},
        {"id": "doc_2", "document": "The basketball game was thrilling. The tension was palpable as the teams faced off in an exciting contest that kept the audience on the edge of their seats. The court was alive with the sound of sneakers sliding, basketballs bouncing, and the roar of the crowd. Every pass, every shot, and every defensive maneuver was met with enthusiasm. The players were locked in, giving it their all, with the score neck-and-neck for most of the game. Key players rose to the occasion, hitting critical shots under pressure, and making defensive plays that could turn the tide of the game. As the final buzzer sounded, the fans erupted in cheers, recognizing the players' dedication and skill that made the game a memorable spectacle.", "metadata": {"source": "sports","game_intensity": 9,"audience_engagement": True,"score_close": True,"key_players_shining": True,"crowd_cheering": True,"momentum_shift": True,"game_outcome": "exciting"}},
        {"id": "doc_3", "document": "Technology is constantly evolving. In recent years, the pace of technological advancements has accelerated at an unprecedented rate. Innovations like artificial intelligence, quantum computing, and blockchain are disrupting industries across the globe. Devices are becoming smarter, more intuitive, and deeply integrated into our daily lives. From self-driving cars to advanced medical diagnostics, technology is changing the way we live and work. The rapid pace of change can be overwhelming, but it also offers incredible opportunities for growth and improvement. As we continue to push the boundaries of what is possible, it's exciting to imagine where technology will take us next.", "metadata": {"source": "technology","evolution_speed": "fast","disruptive_technologies":"AI, quantum computing, blockchain","impact_on_life": True,"innovation_opportunities": True,"transformation_in_life": True,"growth_potential": True}},
        {"id": "doc_4", "document": "The latest smartphone models feature AI capabilities. New smartphone models now come equipped with advanced artificial intelligence technologies that enhance user experience. From camera optimization to voice assistants, AI is helping to make smartphones smarter and more intuitive. These devices can analyze user behavior to predict needs, automate tasks, and even provide personalized recommendations. With the integration of AI, smartphones have become powerful tools for everything from productivity to entertainment. As the technology continues to evolve, we can expect even more sophisticated features that blur the line between user interaction and automation.", "metadata": {"source": "technology","ai_integration": True,"device_features":"camera optimization, voice assistants, personalization","user_experience_improvement": True,"automation": True,"advancement_rate": "high"}},
        {"id": "doc_5", "document": "Artificial intelligence is reshaping how businesses operate. AI is transforming the business landscape by automating processes, improving decision-making, and enhancing customer experiences. With the ability to analyze vast amounts of data, AI algorithms can uncover patterns and insights that humans might miss. From personalized marketing to predictive analytics, businesses are leveraging AI to streamline operations and drive growth. However, the integration of AI also raises important ethical and privacy concerns, as the technology collects and processes personal data at an unprecedented scale. Businesses must carefully consider these implications as they adopt AI solutions.", "metadata": {"source": "technology","business_impact": True,"ai_applications":"automation, decision-making, customer experience","data_analysis": True,"ethical_concerns": True,"privacy_issues": True,"growth_acceleration": True}},
        {"id": "doc_6", "document": "Good health is important for longevity. Maintaining good health is crucial for living a long and fulfilling life. A balanced diet, regular exercise, and mental well-being are key components of overall health. Research has shown that individuals who prioritize healthy habits are more likely to live longer and enjoy a higher quality of life. Regular physical activity not only helps to prevent chronic diseases, but it also boosts mood, energy levels, and cognitive function. Good health is not just the absence of illness, but the presence of a lifestyle that supports vitality and longevity.", "metadata": {"source": "health","importance_of_health": True,"healthy_habits":"balanced diet, exercise, mental well-being","life_expectancy": "longer","disease_prevention": True,"mood_boosting": True,"cognitive_benefits": True}},
        {"id": "doc_7", "document": "A balanced diet is key to staying in good shape. A well-rounded diet rich in fruits, vegetables, lean proteins, and whole grains is essential for maintaining optimal physical health. Nutrients like vitamins, minerals, and antioxidants support bodily functions and boost the immune system. Moreover, staying hydrated and moderating sugar and processed food intake can prevent lifestyle-related diseases such as obesity, heart disease, and diabetes. Maintaining a balanced diet not only helps manage weight but also improves energy levels, mental clarity, and overall well-being.", "metadata": {"source": "health","balanced_diet_essential": True,"nutrient_sources":"fruits, vegetables, lean proteins, whole grains","disease_prevention": "obesity, heart disease, diabetes","energy_boosting": True,"mental_clarity_improvement": True,"weight_management": True}},
        {"id": "doc_8", "document": "AI is revolutionizing healthcare diagnostics. Artificial intelligence is significantly improving the way medical diagnoses are made. By analyzing medical images, genetic data, and patient histories, AI can assist doctors in identifying diseases more quickly and accurately. This technology helps to reduce human error, speed up diagnoses, and even predict potential health risks before they become severe. From detecting early-stage cancers to assessing cardiovascular risks, AI is playing a crucial role in improving patient outcomes and making healthcare more efficient.", "metadata": {"source": "technology-health","ai_impact_on_healthcare": True,"diagnostic_accuracy": True,"healthcare_efficiency": True,"disease_detection": "cancer, cardiovascular risks","early_detection": True,"risk_assessment": True}},
        {"id": "doc_9", "document": "AI-powered applications in healthcare are helping doctors. With the integration of AI tools, healthcare professionals are now able to provide better care and treatment to patients. AI-powered applications assist doctors in making more informed decisions by analyzing large amounts of medical data, suggesting potential diagnoses, and recommending personalized treatment plans. These applications have been particularly useful in fields like radiology, pathology, and oncology, where the precision and speed of AI algorithms can save lives. Additionally, AI helps streamline administrative tasks, allowing healthcare providers to focus more on patient care.", "metadata": {"source": "technology-health","ai_in_healthcare_applications": True,"doctor_assistance": True,"data_analysis": True,"personalized_treatment": True,"radiology_oncology_pathology": True,"administrative_efficiency": True}},
        {"id": "doc_10", "document": "The impact of technology on sports is growing. Technology has become an integral part of modern sports, from training to performance analysis and fan engagement. Devices like wearables track athletes' performance in real-time, while advanced analytics tools help coaches and teams make better decisions. In addition, augmented reality and virtual reality are enhancing the fan experience, bringing stadiums and sports events directly into people's homes. As the integration of technology continues to evolve, sports organizations are looking for new ways to leverage innovation to improve both on-field performance and fan satisfaction.", "metadata": {"source": "sports-technology","tech_in_sports": True,"performance_tracking": True,"fan_engagement": True,"real_time_analysis": True,"augmented_reality": True,"virtual_reality": True,"innovation_in_sports": True}}
    ]

    document_texts = [doc["document"] for doc in documents]
    document_ids = [doc["id"] for doc in documents]
    document_metadatas = [doc["metadata"] for doc in documents]

    print("Test Documents, IDs and Metadatas generated - ready for insert")
    print(f"DEBUG: all ids:\n{document_ids}\n")

    try:
        coll.upsert(
            documents=document_texts,
            metadatas=document_metadatas,
            ids=document_ids
        )
        return jsonify({"message": "Documents added successfully to the collection."}), 200
    except Exception as e:
        print(f"Error inserting multiple test documents: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/import-data-file', methods=['POST'])
def import_data_file():
    print(f"=====================================")
    print(f"Received Request: /import-data-file")
    print(f"=====================================")

    if persistentChromaClient is None:
        print(f"   FROM: /import-data-file   ChromaDB server is unavailable")
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Get the JSON data from the request
    data = request.get_json()

    # Extract collection name, records, and batch_limit from the incoming data
    passed_collection_name = data.get('collection_name')
    records = data.get('records', [])
    batch_limit = data.get('batch_limit', 100)  # Default to 100 if not provided

    print(f"Collection: {passed_collection_name}")
    print(f"Batch Limit: {batch_limit}")
    print(f"Number of Records: {len(records)}")

    # Get the collection and assign the embedding function
    try:
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Collection {passed_collection_name} retrieved.")
    except Exception as e:
        print(f"Collection {passed_collection_name} not found.")
        return jsonify({'error': 'Collection not found. Create the collection first.'}), 500

    # Function to split the records into smaller batches
    def chunk_records(records, batch_size):
        for i in range(0, len(records), batch_size):
            yield records[i:i + batch_size]

    # Split the records into batches based on the batch_limit
    batches = chunk_records(records, batch_limit)

    # Loop through each record and extract id, document, and metadata
    #print(f"DEBUG - Looping through Records just to check...")
    #for record in records:
    #    record_id = record.get('id')
    #    document = record.get('document')
    #    metadata = record.get('metadata')
    #
    #    # Print the extracted variables to the console
    #    print(f"ID: {record_id}")
    #    print(f"Document: {document}")
    #    print(f"Metadata: {metadata}")


    # Process each batch separately
    for batch in batches:
        # Extract document ids and texts
        document_ids = [record.get('id') for record in batch]
        document_texts = [record.get('document') for record in batch]
        
        # Check if metadata is available
        document_metadatas = [record.get('metadata', {}) for record in batch]
        
        # If metadata is empty (default is empty dict), we won't include it in the upsert
        if all(not metadata for metadata in document_metadatas):
            try:
                print(f"Upserting batch of size {len(batch)} without metadata...")
                pycollection.upsert(
                    documents=document_texts,
                    ids=document_ids
                )
                print(f"Upsert for batch successful!")
            except Exception as e:
                print(f"Error during upsert: {str(e)}")
                # Handle the exception
                return jsonify({'error': f'Failed to upsert documents without metadata: {str(e)}'}), 500
        else:
            # When metadata is available, proceed with upserting it as well
            try:
                print(f"Upserting batch of size {len(batch)} with metadata...")
                pycollection.upsert(
                    documents=document_texts,
                    metadatas=document_metadatas,
                    ids=document_ids
                )
                print(f"Upsert for batch successful!")
            except Exception as e:
                print(f"Error during upsert: {str(e)}")
                # Check if the exception message contains "exceeds maximum batch size"
                if "exceeds maximum batch size" in str(e):
                    return jsonify({'error': str(e)}), 566
                return jsonify({'error': f'Failed to upsert documents: {str(e)}'}), 500
    
    # Return a success response once all batches are processed
    return jsonify({"message": "Data received and imported successfully!"}), 200
    

@app.route('/gather-export-data', methods=['POST'])
def gather_export_data():
    print(f"######################################################")
    print(f"REQUEST RECEVIED: /gather-export-data")
    print(f"######################################################")

    # Check if ChromaDB client is available
    if persistentChromaClient is None:
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Get the JSON data from the request
    data = request.get_json()

    # Extract collection name and export choices from the incoming data
    print(f"Extracting data from JSON Payload...")
    passed_collection_name = data.get('collectionName')
    export_choices = data.get('exportOptions', {})

    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"Received Collection Name:\n{passed_collection_name}\n")
    print(f"Received Export Choices:\n{export_choices}")
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

    # Get the collection and assign the embedding function
    print(f"Checking collection exists...")
    try:
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"{passed_collection_name} found.")
    except Exception as e:
        print(f"Collection {passed_collection_name} not found.\n")
        return jsonify({'error': 'Collection not found. Create the collection first.'}), 500

    # Check if the collection is empty
    print(f"Checking Document Count...")
    if pycollection.count() == 0:
        print(f"No documents found in collection")
        return jsonify({'message': 'No documents found in collection'}), 200
    print(f"Collection contains documents to export. Proceeding...\n")

    # Gather the fields to include based on the user's selection
    include_fields = []

    print(f"Building Object for - Content Options")
    content_options = export_choices.get('contentOptions', {})

    if content_options.get('documents', False):
        include_fields.append('documents')
    if content_options.get('metadata', False):
        include_fields.append('metadatas')
    if content_options.get('embeddings', False):
        include_fields.append('embeddings')

    if not include_fields:
        include_fields.append('documents')
        print(f"No Content Options were included - falling back to including documents as default")

    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"DEBUG: These are the include fields we'll use:\n{include_fields}")
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

    # Retrieve the results based on the selected export options
    print(f"Gathering Results...")
    results = pycollection.get(include=include_fields)
    ids = results.get('ids', [])
    if not ids:
        print("No ids returned by get(); nothing to export.")
        return jsonify({'message': 'No documents found in collection'}), 200

    print(f"Building Object for - Record Options")
    record_options = export_choices.get('recordOptions', {})
    print(f"Record Options:        {record_options}")

    # Pull option-specific values
    if record_options == 'all_documents':
        record_options_values = export_choices.get('all_documents', {})
        print(f"Record Options Values: {record_options_values}\n")
    elif record_options == 'list_of_ids':
        record_options_values = export_choices.get('listOfIds', '')
        print(f"Record Options Values: {record_options_values}\n")
    elif record_options == 'from_to_record':
        record_options_values = export_choices.get('fromToRecord', {})
        print(f"Record Options Values: {record_options_values}\n")
    else:
        print("Invalid record option provided.\n")

    # Build the response according to record selection
    documents = []
    print(f"Looping through Results...")

    if record_options == 'all_documents':
        for i, doc_id in enumerate(ids):
            document_data = {'id': doc_id}
            if 'documents' in include_fields and 'documents' in results:
                document_data['document'] = results['documents'][i]
            if 'metadatas' in include_fields and 'metadatas' in results:
                document_data['metadata'] = results['metadatas'][i]
            if 'embeddings' in include_fields and 'embeddings' in results:
                embedding = results['embeddings'][i]
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()
                document_data['embedding'] = embedding
            documents.append(document_data)

    elif record_options == 'list_of_ids':
        raw = str(record_options_values)
        list_of_ids = [x.strip() for x in raw.split(',') if x.strip()]
        for doc_id in list_of_ids:
            if doc_id in ids:
                idx = ids.index(doc_id)
                document_data = {'id': doc_id}
                if 'documents' in include_fields and 'documents' in results:
                    document_data['document'] = results['documents'][idx]
                if 'metadatas' in include_fields and 'metadatas' in results:
                    document_data['metadata'] = results['metadatas'][idx]
                if 'embeddings' in include_fields and 'embeddings' in results:
                    embedding = results['embeddings'][idx]
                    if isinstance(embedding, np.ndarray):
                        embedding = embedding.tolist()
                    document_data['embedding'] = embedding
                documents.append(document_data)

    elif record_options == 'from_to_record':
        # Safer 1-based, bounds-checked range handling
        try:
            total = len(ids)

            raw_from = record_options_values.get('from', 1)
            raw_to   = record_options_values.get('to', total)

            from_record = int(str(raw_from).strip() or 1)
            to_record   = int(str(raw_to).strip() or total)

            if from_record > to_record:
                from_record, to_record = to_record, from_record

            from_record = max(1, from_record)
            to_record   = min(total, to_record)

            print(f"DEBUG3 extracted from: {from_record} --- extracted to: {to_record}")

            start_idx = from_record - 1   # 0-based inclusive
            end_idx   = to_record         # end exclusive

            for i in range(start_idx, end_idx):
                doc_id = ids[i]
                document_data = {'id': doc_id}

                if 'documents' in include_fields and 'documents' in results:
                    document_data['document'] = results['documents'][i]
                if 'metadatas' in include_fields and 'metadatas' in results:
                    document_data['metadata'] = results['metadatas'][i]
                if 'embeddings' in include_fields and 'embeddings' in results:
                    embedding = results['embeddings'][i]
                    if isinstance(embedding, np.ndarray):
                        embedding = embedding.tolist()
                    document_data['embedding'] = embedding

                documents.append(document_data)

        except KeyError as e:
            print(f"KeyError: Missing expected key - {e}")
        except ValueError as e:
            print(f"ValueError: Invalid value encountered - {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    else:
        print("Invalid record option provided.\n")

    # Return the gathered documents as a response
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"Sending Response Data back to Web App")
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    return jsonify({'documents': documents}), 200


@app.route('/export-data-to-json', methods=['POST'])
def export_data_to_json():
    print(f"######################################################")
    print(f"REQUEST RECEIVED: /export-data-to-json")
    print(f"######################################################")

    # Check if ChromaDB client is available
    if persistentChromaClient is None:
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Get the JSON data from the request
    data = request.get_json()

    # Extract collection name and export choices from the incoming data
    passed_collection_name = data.get('collectionName')
    export_choices = data.get('exportOptions', {})

    # Extract the output directory and filename from the incoming data
    output_directory = data.get('outputFolder')
    filename = data.get('outputFilename')

    # Validate output filename
    if not filename:
        return jsonify({'error': 'Filename is mandatory'}), 400

    # Validate output directory, if not, default to current directory
    if not output_directory:
        output_directory = os.getcwd()

    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"Received Collection Name:\n{passed_collection_name}\n")
    print(f"Received Export Choices:\n{export_choices}\n")
    print(f"Output Directory: {output_directory}")
    print(f"Filename:         {filename}")
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

    # Get the collection and assign the embedding function
    print(f"Checking collection exists...")
    try:
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"{passed_collection_name} found.")
    except Exception:
        print(f"Collection {passed_collection_name} not found.\n")
        return jsonify({'error': 'Collection not found. Create the collection first.'}), 500

    # Check if the collection is empty
    print(f"Checking Document Count...")
    if pycollection.count() == 0:
        print(f"No documents found in collection")
        return jsonify({'message': 'No documents found in collection'}), 200
    print(f"Collection contains documents to export. Proceeding...\n")

    # Gather the fields to include based on the user's selection
    include_fields = []

    print(f"Building Object for - Content Options")
    content_options = export_choices.get('contentOptions', {})

    if content_options.get('documents', False):
        include_fields.append('documents')
    if content_options.get('metadata', False):
        include_fields.append('metadatas')
    if content_options.get('embeddings', False):
        include_fields.append('embeddings')

    if not include_fields:
        include_fields.append('documents')
        print(f"No Content Options were included - falling back to including documents as default")

    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"DEBUG: These are the include fields we'll use:\n{include_fields}")
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

    # Retrieve the results
    print(f"Gathering Results...")
    results = pycollection.get(include=include_fields)

    documents = []
    print(f"Looping through Results...")

    print(f"Building Object for - Record Options")
    record_options = export_choices.get('recordOptions', '')
    print(f"Record Options:        {record_options}")

    if record_options == 'all_documents':
        record_options_values = export_choices.get('all_documents', {})
        print(f"Record Options Values: {record_options_values}\n")

        print(f"Exporting all documents.")
        for i, doc_id in enumerate(results['ids']):
            document_data = {'id': doc_id}
            if 'documents' in include_fields:
                document_data['document'] = results['documents'][i]
            if 'metadatas' in include_fields:
                document_data['metadata'] = results['metadatas'][i]
            if 'embeddings' in include_fields:
                embedding = results['embeddings'][i]
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()
                document_data['embedding'] = embedding
            documents.append(document_data)

    elif record_options == 'list_of_ids':
        # Coerce to string; split safely
        record_options_values = str(export_choices.get('listOfIds', '') or '')
        print(f"Record Options Values: {record_options_values}\n")

        list_of_ids = [x.strip() for x in record_options_values.split(',') if x.strip()]
        print(f"Exporting based on provided list of IDs: {list_of_ids}")

        for doc_id in list_of_ids:
            if doc_id in results['ids']:
                idx = results['ids'].index(doc_id)
                document_data = {'id': doc_id}
                if 'documents' in include_fields:
                    document_data['document'] = results['documents'][idx]
                if 'metadatas' in include_fields:
                    document_data['metadata'] = results['metadatas'][idx]
                if 'embeddings' in include_fields:
                    embedding = results['embeddings'][idx]
                    if isinstance(embedding, np.ndarray):
                        embedding = embedding.tolist()
                    document_data['embedding'] = embedding
                documents.append(document_data)

    elif record_options == 'from_to_record':
        record_options_values = export_choices.get('fromToRecord', {})
        print(f"Record Options Values: {record_options_values}\n")

        try:
            from_record = int(record_options_values.get('from', 1))
            to_record = int(record_options_values.get('to', len(results['ids'])))
        except ValueError as e:
            print(f"Error: Invalid value for 'from' or 'to'. They must be integers. Error: {e}")
            return jsonify({'error': 'Invalid value for "from" or "to". They must be integers.'}), 400

        print(f"DEBUG: Extracted from: {from_record} --- Extracted to: {to_record}")

        try:
            for i in range(from_record - 1, min(to_record, len(results['ids']))):
                doc_id = results['ids'][i]
                document_data = {'id': doc_id}
                if 'documents' in include_fields:
                    document_data['document'] = results['documents'][i]
                if 'metadatas' in include_fields:
                    document_data['metadata'] = results['metadatas'][i]
                if 'embeddings' in include_fields:
                    embedding = results['embeddings'][i]
                    if isinstance(embedding, np.ndarray):
                        embedding = embedding.tolist()
                    document_data['embedding'] = embedding
                documents.append(document_data)

        except KeyError as e:
            print(f"KeyError: Missing expected key - {e}")
        except ValueError as e:
            print(f"ValueError: Invalid value encountered - {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        print("Invalid record option provided.\n")

    # Define the full output file path
    output_path = os.path.join(output_directory, filename)

    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        try:
            os.makedirs(output_directory)
            print(f"Created missing output directory: {output_directory}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            return jsonify({'error': f'Failed to create directory: {output_directory}'}), 500

    # Write the documents to the file in JSON format
    try:
        with open(output_path, 'w') as json_file:
            json.dump(documents, json_file, indent=2)
        print(f"Data successfully written to {output_path}")
        return jsonify({'message': f'Data successfully exported to {output_path}'}), 200
    except Exception as e:
        print(f"Error writing to file: {e}")
        return jsonify({'error': 'Failed to write data to file'}), 500


@app.route('/count-documents', methods=['GET'])
def count_collection_documents():
    if persistentChromaClient is None:
        # If the ChromaDB client is not initialized, return an error message
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Get the collection name from the URL query parameters
    passed_collection_name = request.args.get("collection_name")

    if not passed_collection_name:
        return jsonify({'error': 'Collection name not provided'}), 400
    print(f"Passed Collection Name: {passed_collection_name}")

    try:
        # Attempt to get the collection
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )

        # Check if the collection is empty
        print(f"Checking if '{passed_collection_name}' has any documents")
        collection_count = pycollection.count()
        if collection_count == 0:
            print(f"No documents found in collection")
            return jsonify({'document_count': 0}), 200

        # Return the count of documents
        print(f"Documents found")
        print(f"Count: {collection_count}")
        return jsonify({'document_count': collection_count}), 200

    except Exception as e:
        # Handle any error that occurs during the ChromaDB request
        return jsonify({'error': f"Error accessing collection {passed_collection_name}: {str(e)}"}), 500


@app.route('/count-all-documents', methods=['GET'])
def count_all_documents():
    print("==========================================")
    print("Received request for: /count-all-documents")
    print("==========================================")

    if persistentChromaClient is None:
        print("   FROM: /count-all-documents   ChromaDB server is unavailable - Error 500")
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    try:
        # Version-agnostic: get names safely, then count each collection
        names = list_collection_names_safe(persistentChromaClient)
        print(f"   FROM: /count-all-documents   Collections found: {len(names)}")

        total_document_count = 0

        for name in names:
            try:
                coll = persistentChromaClient.get_collection(name, embedding_function=pyEmbedFunction)
                try:
                    count = coll.count()
                    if count is None:
                        print(f"   FROM: /count-all-documents   Collection '{name}': count() returned None")
                        continue
                    total_document_count += int(count)
                except Exception as e:
                    print(f"   FROM: /count-all-documents   count() failed for '{name}': {e}")
            except Exception as e:
                print(f"   FROM: /count-all-documents   Error accessing collection '{name}': {e}")

        print(f"   FROM: /count-all-documents   Total Document Count: {total_document_count}")
        print(f"   FROM: /count-all-documents   Returned Count as JSON")
        return jsonify({'total_document_count': total_document_count}), 200

    except Exception as e:
        print(f"   FROM: /count-all-documents   Error counting Total Documents from all Collections: {e}")
        return jsonify({'error': str(e)}), 500

    
@app.route('/api/get-all-documents', methods=['POST'])
def get_all_documents():

    # Get the collection name from the request body
    collection_name = request.json.get("collection_name")

    if not collection_name:
        return jsonify({'error': 'Collection name not provided'}), 400
    
    try:
        pycollection = persistentChromaClient.get_collection(
            collection_name, embedding_function=pyEmbedFunction
        )
    except Exception as e:
        return jsonify({'error': f"Collection {collection_name} not found: {str(e)}"}), 500

    # Check if the collection is empty
    if pycollection.count() == 0:
        return jsonify({'message': 'No documents found in collection'}), 200

    # Fetch the documents and their embeddings
    results = pycollection.get(include=["embeddings", "documents", "metadatas"])

    documents = []
    for i, doc_id in enumerate(results['ids']):
        # Convert embedding to a serializable list
        embedding = results['embeddings'][i].tolist() if isinstance(results['embeddings'][i], np.ndarray) else results['embeddings'][i]
        
        documents.append({
            'id': doc_id,
            'document': results['documents'][i],
            'metadata': results['metadatas'][i],
            'embedding': embedding
        })

    return jsonify({'documents': documents}), 200


# Route to handle document deletion
@app.route('/api/delete-document', methods=['POST'])
def delete_document():
    # Get the data from the POST request
    data = request.json
    
    # Extract the document ID and collection name from the request
    doc_id_to_delete = data.get('id')
    collection_name = data.get('collection_name')

    if not doc_id_to_delete or not collection_name:
        return jsonify({"error": "Document ID and collection name are required."}), 400
    
    try:
        # Get the Collection and assign the Embedding Function to it
        pycollection = persistentChromaClient.get_collection(collection_name, embedding_function=pyEmbedFunction)
        print(f"Collection {collection_name} found and retrieved.")
    except Exception as e:
        return jsonify({"error": f"Collection {collection_name} not found: {str(e)}"}), 500
    
    try:
        # Delete the document
        pycollection.delete([doc_id_to_delete])
        print(f"Document with ID {doc_id_to_delete} has been deleted.")
        return jsonify({"message": f"Document with ID {doc_id_to_delete} has been deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete document: {str(e)}"}), 500


# Route to handle document deletion
@app.route('/api/delete-all-documents', methods=['POST'])
def delete_all_documents():

    if persistentChromaClient is None:  # Assuming client is defined elsewhere
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    # Extract collection data from the request's JSON payload
    data = request.json
    passed_collection_name = data.get("collection_name")

    # Debugging: print all extracted values to the server's log
    print(f"Received data:\ncollection_name={passed_collection_name}")

    # Ensure collection name is provided
    if not passed_collection_name:
        return jsonify({'error': 'Collection name required'}), 400

    try:
        # Try getting the collection first (doesn't raise exception if collection is not found)
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Existing Collection '{passed_collection_name}' found.")

    except Exception as e:
        # Handle unexpected errors
        print(f"Collection '{passed_collection_name}' Not Found, aborting...\n{str(e)}")
        return jsonify({"message": f"Collection '{passed_collection_name}' Not Found, aborting..."}), 404

    # Now extract the ids, documents, and metadata into object variables
    old_collection_metadata = pycollection.metadata

    # Fetch the documents and their metadata
    old_results = pycollection.get(include=["documents", "metadatas"])

    old_doc_ids = old_results['ids']
    old_documents = old_results['documents']
    old_document_metadata = old_results['metadatas']

    # Now Delete the Collection to free up its name 
    print(f"Deleting Collection to Free Up Collection Name...")
    try:
        persistentChromaClient.delete_collection(name=passed_collection_name)
    except Exception as e:
        print(f"Error deleting collection: {str(e)}")
        return jsonify({'error': f'Failed to delete collection: {str(e)}'}), 500

    # Now we need to create a new one with the same parameters
    try:
        if old_collection_metadata:  # If metadata is not empty
            pycollection_new = persistentChromaClient.create_collection(
                passed_collection_name,
                embedding_function=pyEmbedFunction,
                metadata=old_collection_metadata
            )
        else:
            pycollection_new = persistentChromaClient.create_collection(
                passed_collection_name,
                embedding_function=pyEmbedFunction
            )
        print(f"All Documents Deleted from '{passed_collection_name}' successfully.")
        return jsonify({"message": f"Documents deleted and collection recreated for '{passed_collection_name}' successfully."}), 200

    except Exception as e:
        print(f"Failed to Recreate collection when deleting all documents: {str(e)}")
        return jsonify({'error': f'Failed to Recreate collection when deleting all documents: {str(e)}'}), 500


@app.route('/api/query-documents', methods=['POST'])
def query_documents():
    data = request.get_json(silent=True) or {}

    passed_collection_name = (data.get("collection_name") or "").strip()
    query_text = (data.get("query_text") or "").strip()

    # n_results: sanitize and clamp
    try:
        n_results = int(data.get("num_of_results", 5))
    except Exception:
        n_results = 5
    n_results = max(1, min(100, n_results))

    # Optional filters (accept dicts or JSON strings)
    def _maybe_parse_json(val):
        if isinstance(val, str) and val.strip().startswith(("{", "[")):
            try:
                return json.loads(val)
            except Exception:
                return val
        return val

    passed_where_document_filters = _maybe_parse_json(data.get("where_document"))
    passed_where_metadata_filters = _maybe_parse_json(data.get("where"))

    if not passed_collection_name or not query_text:
        return jsonify({'error': 'Missing required fields (collection_name, query_text)'}), 400

    # Debug logging
    print("\n\n------------------------")
    print("Data from JSON payload:")
    print("------------------------")
    print(f"passed Collection Name:          {passed_collection_name}")
    print(f"passed Query Text:               {query_text}")
    print(f"passed Num of Results:           {n_results}")
    print(f"passed Where Document Filters:   {passed_where_document_filters}")
    print(f"passed Where Metadata Filters:   {passed_where_metadata_filters}\n")

    try:
        coll = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"Collection {passed_collection_name} found and retrieved.")
    except Exception as e:
        return jsonify({'error': f"Collection {passed_collection_name} not found: {str(e)}"}), 500

    # Build query params
    params = {
        "query_texts": [query_text],
        "n_results": n_results
    }
    if passed_where_document_filters:
        params["where_document"] = passed_where_document_filters
    if passed_where_metadata_filters:
        params["where"] = passed_where_metadata_filters

    try:
        print("Querying collection with the following parameters:")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(f"Query Text:\n{query_text}\n")
        print(f"Number of Results:        {n_results}")
        print(f"Where Document Filters:   {passed_where_document_filters}")
        print(f"Where Metadata Filters:   {passed_where_metadata_filters}")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

        res = coll.query(**params)

        docs      = (res.get("documents") or [[]])[0]
        ids_      = (res.get("ids")       or [[]])[0]
        metas     = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]

        # Return empty results (200) rather than a 404 — easier for clients to handle
        if not docs:
            return jsonify({'results': []}), 200

        out = []
        for i, (doc_id, doc) in enumerate(zip(ids_, docs)):
            out.append({
                "result_index": i,
                "similarity_score": distances[i] if i < len(distances) else None,
                "doc_id": doc_id,
                "metadata": metas[i] if i < len(metas) else None,
                "document": doc,
            })

        return jsonify({'results': out}), 200

    except Exception as e:
        return jsonify({'error': f"Error querying documents: {str(e)}"}), 500


@app.route('/api/update-document', methods=['POST'])
def update_document():
    try:
        # Retrieve JSON data from request
        data = request.get_json()
        
        # Extract required fields
        passed_collection_name = data.get('collection_name')
        passed_doc_id = data.get('doc_id')
        passed_document_content = data.get('document_content')
        
        # Optional: Retrieve metadata if provided
        passed_metadata = data.get('metadata', None)
        
        # If metadata is a string, attempt to convert it to a dictionary
        if passed_metadata and isinstance(passed_metadata, str):
            try:
                passed_metadata = json.loads(passed_metadata)
            except json.JSONDecodeError:
                return jsonify({"error": "Metadata is not a valid JSON string"}), 400
        
        # Get the Collection and assign the Embedding Function to it
        pycollection = persistentChromaClient.get_collection(passed_collection_name, embedding_function=pyEmbedFunction)
        print(f"Collection {passed_collection_name} found and retrieved.")
        

        # Fetch all the documents and their embeddings
        #results = pycollection.get(include=["documents"])

        # Find the document with the specific ID
        #doc_found = False
        #for i, loop_doc_id in enumerate(results['ids']):
        #    if loop_doc_id == passed_doc_id:
        #        doc_found = True
        #        print(f"Matching Doc ID found: {passed_doc_id}")
        #        break
        #
        #if not doc_found:
        #    # Document with the given ID doesn't exist
        #    print(f"Error: Document with ID {passed_doc_id} does not exist.")
        #    return jsonify({"message": f"Error: Document with ID {passed_doc_id} does not exist."}), 400

        # Update the document content (mandatory part)
        #pycollection.upsert([passed_doc_id])

       
        try:
            # Check if metadata was provided and update if needed
            if passed_metadata:
                pycollection.upsert(
                    documents=[passed_document_content],
                    metadatas=[passed_metadata],
                    ids=[passed_doc_id]
                )
            else:
                pycollection.upsert(
                    documents=[passed_document_content],
                    ids=[passed_doc_id]
                )

        
        except Exception as e:
            # If there is an error, return error message with the exception details
            return jsonify({
                "message": f"Error Updating Document: {str(e)}",
                "status_code": 500
            }), 500

        return jsonify({"message": f"Document with ID {passed_doc_id} has been updated successfully."}), 200


    except Exception as e:
        return jsonify({"error": f"Failed to update document: {str(e)}"}), 500



@app.route('/visualize-collection', methods=['POST'])
def visualize_my_collection():
    """
    Safer, env-aware visualizer:
    - Uses CHROMAVIZ_HOST/CHROMAVIZ_PORT computed at startup (no local overrides)
    - Works regardless of current working directory (paths resolved relative to this file)
    - Robust regex patches http/https endpoints
    - Atomic file writes + clear JSON errors
    """
    # 1) Basic checks
    if persistentChromaClient is None:
        return jsonify({'error': 'ChromaDB server is unavailable'}), 500

    data = request.get_json(silent=True) or {}
    passed_collection_name = data.get("collection_name")
    if not passed_collection_name:
        return jsonify({'error': 'Collection name required'}), 400

    # 2) Confirm collection exists
    try:
        pycollection = persistentChromaClient.get_collection(
            passed_collection_name, embedding_function=pyEmbedFunction
        )
        print(f"=======================================================")
        print(f"Existing Collection '{passed_collection_name}' found.")
        print(f"=======================================================")
    except Exception as e:
        print(f"Collection '{passed_collection_name}' Not Found: {e}")
        return jsonify({"message": f"Collection '{passed_collection_name}' Not Found, aborting...", "detail": str(e)}), 404

    # 3) Resolve asset paths relative to this file (not CWD)
    try:
        from pathlib import Path
        base_dir = Path(__file__).resolve().parent
        chromaviz_dir = base_dir / "chromaviz"
        js_path = chromaviz_dir / "index-351494fc.js"
        html_path = chromaviz_dir / "index.html"

        if not js_path.exists() or not html_path.exists():
            return jsonify({
                "error": "ChromaViz assets not found",
                "expected_paths": {"js": str(js_path), "html": str(html_path)}
            }), 500
    except Exception as e:
        return jsonify({"error": f"Failed to resolve ChromaViz asset paths: {e}"}), 500

    # 4) Build target URLs using globals set during startup
    target_data_url = f'fetch("http://{CHROMAVIZ_HOST}:{CHROMAVIZ_PORT}/data")'
    back_link = f'<a href="http://{CHROMAVIZ_HOST}:{CHROMAVIZ_PORT - 1}" target="_self">'

    # 5) Patch the JS fetch endpoint (atomic write)
    try:
        import re, tempfile, shutil
        pattern = r'fetch\("http[s]?://[^"]+/data"\)'
        text = js_path.read_text(encoding="utf-8")
        new_text, n = re.subn(pattern, target_data_url, text)
        if n == 0:
            # Pattern not found; keep file intact but add a warning comment
            new_text = text + f'\n/* WARN: fetch pattern not found; expected to replace with {target_data_url} */\n'
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            tmp.write(new_text)
            tmp_path = tmp.name
        shutil.move(tmp_path, js_path)
        print(f"Patched JS endpoint in: {js_path}")
    except Exception as e:
        return jsonify({"error": f"Failed to patch JS endpoint: {e}"}), 500

    # 6) Patch the index.html back-link (atomic write)
    try:
        pattern = r'(<a href="http[s]?://)[^"]+(" target="_self">)'
        text = html_path.read_text(encoding="utf-8")
        new_text, n = re.subn(pattern, back_link, text)
        if n == 0:
            new_text = text + f'\n<!-- WARN: link pattern not found; expected to replace with {back_link} -->\n'
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            tmp.write(new_text)
            tmp_path = tmp.name
        shutil.move(tmp_path, html_path)
        print(f"Patched back-link in: {html_path}")
    except Exception as e:
        return jsonify({"error": f"Failed to patch index.html backlink: {e}"}), 500

    # 7) Launch visualizer
    try:
        visualize_collection(pycollection, CHROMAVIZ_PORT)
    except Exception as e:
        return jsonify({"error": f"Failed to start visualizer: {e}"}), 500

    return jsonify({"message": "Visual Data is Generating... Please Wait..."}), 200


@app.route('/clear-console')
def clear_console():
    # This command clears the terminal/console where the Flask server is running
    os.system('cls' if os.name == 'nt' else 'clear')
    return "Flask Console Cleared!"


# ---- Storage info helper + routes -------------------------------------------
def _compute_storage_info() -> dict:
    """
    Describe where Chroma stores data.
    - HTTP mode: show CHROMA_DATA_PATH from *this* process (what you set in PowerShell)
    - Local mode: show the resolved CHROMA_DATA_PATH used by PersistentClient
    Always return strings so the UI never gets null.
    """
    mode = os.getenv("CHROMA_MODE", "persistent").lower()
    info = {"mode": mode}

    if mode == "http":
        host = os.getenv("CHROMA_HTTP_HOST", "127.0.0.1")
        port = int(os.getenv("CHROMA_HTTP_PORT", "8000"))
        server_path = os.getenv("CHROMA_DATA_PATH", "")  # you set this in PS

        info["server_host"] = host
        info["server_port"] = port
        info["data_path"]   = str(server_path or "")
        info["accessible"]  = bool(server_path and os.path.isdir(server_path))
        info["note"]        = "HTTP mode. data_path is on the server; accessible only if co-located."
    else:
        data_dir = CHROMA_DATA_PATH or ""
        info["data_path"]   = str(data_dir)
        info["accessible"]  = bool(data_dir and os.path.isdir(data_dir))
        info["note"]        = "Local PersistentClient data directory."

    return info


@app.route('/chromadb-path-sqllite', methods=['GET'])
def chromadb_path_sqllite():
    """
    Return exactly what the UI expects:
      { "chromadb_path_sqllite": "<string>" }
    Never return null; provide a friendly message instead.
    """
    try:
        info = _compute_storage_info()
        path = info.get("data_path") or ""
        if not path:
            path = ("Remote HTTP mode — no local path or CHROMA_DATA_PATH not set."
                    if info.get("mode") == "http" else "Not configured.")
        return jsonify({"chromadb_path_sqllite": str(path)}), 200
    except Exception as e:
        # Keep the shape the same so the front-end can still show something
        return jsonify({"chromadb_path_sqllite": f"Error: {e}"}), 200




# Run the app locally
if __name__ == '__main__':
    # Start a separate thread to open the browser
    threading.Thread(target=open_browser).start()

    # Disable Flask's debugger reloader (prevents it from re-running the connection check)
    app.run(host=host_flask, debug=True, port=port_flask, use_reloader=False)
