import requests

# The URL where your FastAPI server is running locally
URL = "http://127.0.0.1:8000/webhook"

# A mock CloudMailin JSON payload
payload = {
    "headers": {
        "Subject": "Project Sync - Meeting Id: a0B1234567890abcde",
        "From": "client@example.com",
        "To": "36825d4b588029922f81@cloudmailin.net"
    },
    "envelope": {
        "to": "36825d4b588029922f81@cloudmailin.net",
        "from": "client@example.com",
        "helo_domain": "example.com",
        "remote_ip": "127.0.0.1",
        "recipients": ["36825d4b588029922f81@cloudmailin.net"]
    },
    "plain": "Hi team, great meeting today. We agreed to move forward with the Q3 roadmap. Let's reconvene next week. Here is the meeting link: https://zoom.us/j/123456789?pwd=abc",
    "html": "<p>Hi team, great meeting today...</p>",
    "reply_plain": ""
}

print(f"Sending test payload to {URL}...")

try:
    response = requests.post(URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
except Exception as e:
    print(f"Failed to connect to the server. Is it running? Error: {e}")
