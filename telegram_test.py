import requests





url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": "🎬 Cinepolis alert bot is working!"
}

response = requests.post(url, data=data)

print("Status:", response.status_code)
print(response.json())