import requests
import uuid
import time
from datetime import datetime

BOT_URL = "http://localhost:3978/api/messages"

def send_message(text):
    payload = {
        "type": "message",
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "channelId": "emulator",
        "serviceUrl": "http://localhost:3978/",
        "from": {"id": "user1", "name": "User"},
        "conversation": {"id": "conv1", "name": "Conv"},
        "recipient": {"id": "bot1", "name": "Bot"},
        "text": text
    }
    
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(BOT_URL, json=payload, headers=headers)
        print(f"Sent: {text} | Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

# Simulate successful booking
send_message("Book a flight from Paris to London for tomorrow returning in 5 days with a budget of 1000")
time.sleep(2)
send_message("yes") # Confirm booking

# Simulate failure
send_message("I like eating shoes") # Triggers BotComprehensionFailure
