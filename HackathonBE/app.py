from flask import Flask, request, jsonify, make_response, send_from_directory
import requests
import json
from urllib.parse import urlparse
from flask_cors import CORS
from dotenv import load_dotenv, set_key
import os
from werkzeug.serving import make_server
import threading
from promptParsing import chunk_for_lm_studio
from apiRoutes import build_api_url

# Load .env vars
load_dotenv()

username = os.getenv("API_USERNAME")
password = os.getenv("API_PASSWORD")
base_url = os.getenv("API_URL")

# Frontend origins allowed to call your API
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "hackathonfe", "dist")

# Flask app
app = Flask(__name__,
    static_folder=FRONTEND_BUILD_DIR
)

# Enable CORS for /api/* routes; we'll still add precise headers below
CORS(
    app,
    resources={r"/api/*": {"origins": list(ALLOWED_ORIGINS)}},
    methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.after_request
def add_cors_headers(response):
    """
    Ensure CORS headers are present on every response (including errors),
    and echo back only allowed origins.
    """
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/api/query", methods=["POST", "OPTIONS"])
def query():
    # Handle preflight quickly
    if request.method == "OPTIONS":
        # 204 No Content is fine for preflight
        return ("", 204)

    try:
        print("Getting AI response")

        data = request.get_json(silent=True) or {}
        print(data)

        question = (data.get("question") or "").strip()
        if not question:
            return jsonify({"error": "Missing question"}), 400

        # Rentvine API call
        url = (data.get("url")).strip()
        api_url = build_api_url("https://123pm.rentvine.com/screening/applications/1630")
        app_response = requests.get(api_url, auth=(username, password)) #this is where the code is breaking, this request is not going through?
        app_response.raise_for_status()
        api_data = json.dumps(app_response.json(), indent=2)

        #chuncks API data
        parts = chunk_for_lm_studio(api_data, max_tokens=2000, reserve_tokens=600, overlap_tokens=64)
        print("API Response chunked")
        messages = [
                    {"role": "system", "content": f"You are a helpful customer support assistant. Here is the customers question: {question}. You will receive the context for this prompt in the following messages."},
                ]
        print("Messages initialized")
        cnt = 0
        for p in parts:
            cnt = cnt + 1
            messages.append({
                "role": "user",
                "content": f"[PART {p['index']+1}/{p['total']}] SHA256={p['sha256']}\n{p['content']}"
            })
        print("Messages added")
        messages.append({
            "role": "user",
            "content": f"Here is the chat history: {data.get("history")}"
            })
        print("history added")
        lm_studio_url = "http://localhost:1234/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio"
        }
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "temperature": 0.5
        }
        print("sending request")
        lm_response = requests.post(lm_studio_url, headers=headers, json=payload)
        print("count: ", cnt)
        print("awaiting status and response")
        lm_response.raise_for_status()
        lm_data = lm_response.json()

        reply = lm_data["choices"][0]["message"]["content"]
        print(reply)

        return jsonify({
            "answer": reply,
            "sources": [{"title": "N/A", "url": "#"}]
        })

    except Exception as e:
        # Headers will still be added by @after_request
        return jsonify({"error": str(e)}), 500


# Serve react's static pages from the backend. Not using for demo 
"""
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        # Serve static files (JS, CSS, images, etc.)
        return send_from_directory(app.static_folder, path)
    else:
        # Serve the React index.html for any other route
        return send_from_directory(app.static_folder, 'index.html')
"""

if __name__ == "__main__":
    def run_app():
        # Create the server, letting it pick any open port
        server = make_server("127.0.0.1", 0, app)  # 0 = auto-assign
        port = server.server_port                 # :white_check_mark: real assigned port
        app.config["PORT"] = port
        print(f":white_check_mark: Server running on http://127.0.0.1:{port}")
        env_path = os.path.join(os.path.dirname(__name__), "..", "hackathonFE", ".env")
        set_key(env_path, "VITE_BACKEND_PORT", str(port))
        server.serve_forever()                    # block here
    # Run Flask in a background thread
    thread = threading.Thread(target=run_app)
    thread.start()