from flask import Flask, request, jsonify
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

# Flask app
app = Flask(__name__)
CORS(app)  # allow frontend requests (adjust origin if needed)

def getApiData(url):
    #figure out how to parse this string
    url = url.split("localhost:5173", 1)[1]  # returns "/portfolios/351" CHANGE TO RENTVINE.COM
    print(url)
    app_response = requests.get(
            f"{base_url}{url}",
            auth=(username, password)
        )
    app_response.raise_for_status()
    app_data = app_response.json()
    print(app_data)
    formatted_data = json.dumps(app_data, indent=2)
    return formatted_data

@app.route("/api/query", methods=["POST"])
def query():
    try:
        data = request.get_json()
        print(data)
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "Missing question"}), 400
        # Rentvine API call
        url = data.get("url", "").strip()
        formatted_data = getApiData(url)
        

        # Prepare message for LM Studio
        lm_studio_url = "http://localhost:1234/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio"
        }

        payload = {
            "model": "gpt-oss-20b", #Having issues with loading model off of code
            "messages": [
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user", "content": f"""Here is the user's account info from the app API:\n\n{formatted_data}\n\nNow answer this support question:\n{question}"""}
            ],
            "temperature": 0.5
        }

        lm_response = requests.post(lm_studio_url, headers=headers, json=payload)
        lm_response.raise_for_status()
        lm_data = lm_response.json()

        reply = lm_data["choices"][0]["message"]["content"]

        return jsonify({
            "answer": reply,
            "sources": [
                {"title": "Late Fee Settings Overview", "url": "#"},
                {"title": "Creating Custom Fields", "url": "#"}
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
