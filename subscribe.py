import os
import requests
from dotenv import load_dotenv

def subscribe_webhook():
    # Загружаем переменные из .env
    load_dotenv()
    
    access_token = os.environ.get("ACCESS_TOKEN")
    
    if not access_token:
        print("Ошибка: ACCESS_TOKEN не найден в .env файле")
        return

    url = "https://graph.instagram.com/v25.0/me/subscribed_apps"
    
    # Параметры запроса
    params = {
        "subscribed_fields": "messages",
        "access_token": access_token
    }
    
    try:
        print("Отправка запроса на подписку...")
        response = requests.post(url, params=params)
        
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        
    except Exception as e:
        print(f"Произошла ошибка при отправке запроса: {e}")

if __name__ == "__main__":
    subscribe_webhook()
