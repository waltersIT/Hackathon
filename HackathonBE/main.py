import requests
import json

# Step 1: Query your app's API
response = requests.get(
    "https://your-api.com/endpoint",
    auth=("your_username", "your_password")
)
app_response = requests.get(app_api_url)
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
    "model": "your-model-name",  # This must match what LM Studio shows
    "messages": [
        {"role": "system", "content": "You are a helpful customer support assistant."},
        {"role": "user", "content": f"""Here is the user's account info from the app API:\n\n{formatted_data}\n\nNow answer this support question:\nWhy was the user charged twice this month?"""}
    ],
    "temperature": 0.5
}

response = requests.post(lm_studio_url, headers=headers, json=data)
print(response.json()["choices"][0]["message"]["content"])
