import requests
import socket
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print("Checking DNS resolution for generativelanguage.googleapis.com...")
try:
    ip = socket.gethostbyname('generativelanguage.googleapis.com')
    print(f"Success! Resolved to: {ip}")
except Exception as e:
    print(f"DNS Resolution FAILED: {str(e)}")

print("\nTesting simple HTTPS GET to Google...")
try:
    res = requests.get('https://www.google.com', timeout=5)
    print(f"Internet reachable. Status code: {res.status_code}")
except Exception as e:
    print(f"Internet check FAILED: {str(e)}")

print("\nTesting Gemini API endpoint with GET...")
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
try:
    res = requests.get(url, timeout=5)
    print(f"Gemini API check completed. Status code: {res.status_code}")
    if res.status_code != 200:
        print(res.json())
except Exception as e:
    print(f"Gemini API check FAILED: {str(e)}")
