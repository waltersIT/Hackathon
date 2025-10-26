from flask import Flask, request, jsonify, make_response, send_from_directory
import requests
import json
from urllib.parse import urlparse
from flask_cors import CORS
from dotenv import load_dotenv, set_key
import os
from werkzeug.serving import make_server
import threading

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

def getApiData(full_url: str):
    # Parse path off the frontend origin (adjust if you change your frontend host)
    p = urlparse(full_url or "")
    path = p.path or "/"
    if p.query:
        path += f"?{p.query}"
    # now path is like "/portfolios/351?x=y"
    app_response = requests.get(f"{base_url}{path}", auth=(username, password))
    app_response.raise_for_status()
    return json.dumps(app_response.json(), indent=2)
    
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
        url = (data.get("url") or "").strip()
        formatted_data = getApiData(url)
        print("API fetched successfully")

        # Prepare message for LM Studio
        lm_studio_url = "http://localhost:1234/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio"
        }
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user", "content": f"Here is the user's account info from the app API:\n\n{formatted_data}\n\nNow answer this support question:\n{question}"}
            ],
            "temperature": 0.5
        }

        lm_response = requests.post(lm_studio_url, headers=headers, json=payload)
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


# 🟢 Serve React frontend for all non-API routes

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        # Serve static files (JS, CSS, images, etc.)
        return send_from_directory(app.static_folder, path)
    else:
        # Serve the React index.html for any other route
        return send_from_directory(app.static_folder, 'index.html')



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