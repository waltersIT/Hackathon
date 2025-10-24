from flask import Flask, request, jsonify, make_response
import requests
import json
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load .env vars
load_dotenv()

username = os.getenv("API_USERNAME")
password = os.getenv("API_PASSWORD")
base_url = os.getenv("API_URL")

# Frontend origins allowed to call your API
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}

# Flask app
app = Flask(__name__)

# Enable CORS for /api/* routes; we'll still add precise headers below
CORS(
    app,
    resources={r"/api/*": {"origins": list(ALLOWED_ORIGINS)}},
    methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

def getApiData(url):
    # Parse path off the frontend origin (adjust if you change your frontend host)
    url = url.split("localhost:5173", 1)[1]  # returns "/portfolios/351"
    app_response = requests.get(f"{base_url}{url}", auth=(username, password))
    app_response.raise_for_status()
    app_data = app_response.json()
    formatted_data = json.dumps(app_data, indent=2)
    return formatted_data

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

if __name__ == "__main__":
    # please work 
    app.run(host="127.0.0.1", port=5051, debug=True)
