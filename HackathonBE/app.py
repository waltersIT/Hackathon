from flask import Flask, render_template_string, request
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get values from .env
username = os.getenv("API_USERNAME")
password = os.getenv("API_PASSWORD")
base_url = os.getenv("API_URL")

# Flask app setup
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    try:
        # Step 1: Get data from your app's API
        app_response = requests.get(
            f"{base_url}/properties/611",
            auth=(username, password)
        )
        app_response.raise_for_status()
        app_data = app_response.json()
        formatted_data = json.dumps(app_data, indent=2)

        # Step 2: Send to LM Studio
        lm_studio_url = "http://localhost:1234/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio"
        }

        data = {
            "model": "gpt-oss-20b",
            "messages": [
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user", "content": f"""Here is the user's account info from the app API:\n\n{formatted_data}\n\nNow answer this support question:\nWhy was the user charged twice this month?"""}
            ],
            "temperature": 0.5
        }

        lm_response = requests.post(lm_studio_url, headers=headers, json=data)
        lm_response.raise_for_status()
        reply = lm_response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"Error: {str(e)}"

    # Simple template to show result
    return render_template_string("""
        <h1>LM Studio Response</h1>
        <pre>{{ reply }}</pre>
    """, reply=reply)

if __name__ == "__main__":
    app.run(debug=True)
