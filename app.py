import os
import hmac
import hashlib
import requests
from flask import Flask, request, make_response
from dotenv import load_dotenv
from rag import get_answer

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
IG_ID = os.environ.get("IG_ID")
APP_SECRET = os.environ.get("APP_SECRET", "")

BLOCKED_PHRASES = [
    "ignore previous", "forget instructions", "system prompt",
    "ignore instructions", "new role", "pretend you are",
    "забудь инструкции", "игнорируй", "системный промпт"
]

def is_injection(text):
    if not text:
        return False
    return any(phrase in text.lower() for phrase in BLOCKED_PHRASES)

def verify_signature(request):
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = request.get_data()
    expected = "sha256=" + hmac.new(APP_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
    
    is_valid = hmac.compare_digest(signature, expected)
    if not is_valid:
        print(f"[AUTH ERROR] Signature mismatch! Received: {signature}")
        # print(f"Expected: {expected}") # Не выводим ожидаемую подпись в логи на всякий случай для безопасности
    return is_valid

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode and token:
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                return challenge, 200
            else:
                return 'Verification token mismatch', 403
        return 'OK', 200

    if request.method == 'POST':
        # Временно отключили проверку подписи:
        # if not verify_signature(request):
        #     return make_response("Unauthorized", 401)
            
        data = request.json
        print(f"[WEBHOOK] Incoming POST data: {data}")
        if data and 'entry' in data:
            for entry in data['entry']:
                if 'messaging' in entry:
                    for event in entry['messaging']:
                        sender_id = event.get('sender', {}).get('id')
                        message_text = event.get('message', {}).get('text')
                        print(f"[WEBHOOK] sender_id={sender_id}, IG_ID={IG_ID}, text={message_text}")

                        # Игнорируем сообщения, отправленные самим ботом
                        if sender_id == IG_ID:
                            print("[WEBHOOK] Skipping own message.")
                            continue

                        if sender_id and message_text:
                            if is_injection(message_text):
                                send_message(sender_id, "Я ассистент Astana Hub и могу помочь только по теме хаба 🙂")
                            else:
                                answer = get_answer(message_text)
                                send_message(sender_id, answer)
                        else:
                            print(f"[WEBHOOK] Skipped event: no sender_id or no text")

        return 'EVENT_RECEIVED', 200

def send_message(recipient_id, text):
    url = f"https://graph.instagram.com/v25.0/{IG_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    try:
        print(f"[SEND] Sending to {recipient_id}: {text[:80]}")
        resp = requests.post(url, headers=headers, json=payload)
        print(f"[SEND] Instagram API response: {resp.status_code} — {resp.text}")
    except Exception as e:
        print(f"[SEND] Error sending message: {e}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
