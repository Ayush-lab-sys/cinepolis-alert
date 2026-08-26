import requests

BOT_TOKEN = "8706318691:AAFFg9nwV2DpYdJ-15AMQAQrhVVknv4Vnyo"
CHAT_ID = "5314697440"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": "🎬 Cinepolis alert bot is working!"
}

response = requests.post(url, data=data)

print("Status:", response.status_code)
print(response.json())