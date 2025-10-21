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

lm_studio_url = "http://127.0.0.1:1234/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer lm-studio"
}
payload = {
    "model": "openai/gpt-oss-20b", #Having issues with loading model off of code | look into changing engines
    "messages": [
        {"role": "system", "content": "You are a helpful customer support assistant."},
        {"role": "user", "content": f"""Here is the user's account info from the app API:\n\nsome data\n\nNow answer this support question:\nhello"""}
    ],
    "temperature": 0.5
}
lm_response = requests.post(lm_studio_url, headers=headers, json=payload)
lm_response.raise_for_status()
lm_data = lm_response.json()
reply = lm_data["choices"][0]["message"]["content"]
print(reply)