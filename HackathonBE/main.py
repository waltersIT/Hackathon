import requests
import json
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()  # By default, it looks for a .env file in the current directory

# Access the environment variables
username = os.getenv("API_USERNAME")
password = os.getenv("API_PASSWORD")
base_url = os.getenv("API_URL")

# Step 1: Query your app's API
app_response = requests.get(
    f'{base_url}/properties/611',
    auth=(username, password)
)
app_data = app_response.json()

# Format the data (optional - make it readable)
formatted_data = json.dumps(app_data, indent=2)

# Step 2: Send the API response as context to LM Studio
lm_studio_url = "http://localhost:1234/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer lm-studio"
}

data = {
    "model": "gpt-oss-20b",  # This must match what LM Studio shows
    "messages": [
        {"role": "system", "content": "You are a helpful customer support assistant."},
        {"role": "user", "content": f"""Here is the user's account info from the app API:\n\n{formatted_data}\n\nNow answer this support question:\nWhy was the user charged twice this month?"""}
    ],
    "temperature": 0.5
}

response = requests.post(lm_studio_url, headers=headers, json=data)
print(response.json()["choices"][0]["message"]["content"])
