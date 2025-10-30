import requests
import urllib3
from dotenv import load_dotenv
import os

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
username = os.getenv("API_USERNAME")
password = os.getenv("API_PASSWORD")
portfolio_url = "https://abchomes.rentvinedev.com/api/manager/portfolios/391?includes=owners%2Cproperties%2Cposting%2CstatementSetting%2Cledger"

print("USERNAME", username)
print("PASSWORD", password if password else "NOT SET")
print("URL", portfolio_url)

# Disable SSL verification for dev environment (self-signed certificate)
response = requests.get(portfolio_url, auth=(username, password), verify=False)

print(f"\nStatus Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print(f"Response Text (first 500 chars): {response.text[:500]}")

if response.status_code == 200:
    try:
        json_data = response.json()
        print("\nRESPONSE JSON:", json_data)
    except ValueError as e:
        print(f"\nERROR: Response is not valid JSON: {e}")
        print(f"Response text: {response.text}")
else:
    print(f"\nERROR: Non-200 status code")
    response.raise_for_status()