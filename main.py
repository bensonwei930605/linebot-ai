import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "你的GEMINI_API_KEY") # 請確保環境變數有設
TELEGRAM_BOT_TOKEN = "8345028959:AAGp7LAqW4AEJUH1VHg8r7N0yWNjnDIMdTM"
TELEGRAM_CHAT_ID = "7468110837"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def analyze_intent(text):
    prompt = f"""
    你是專業的單車店客服助手。請判斷客戶訊息意圖，僅回覆三個選項之一：
    1. "BUY": 客戶在詢問車款、預算、價格、買車意願（包含注音文、錯別字）。
    2. "TIME": 客戶在詢問時間、約看車、預約。
    3. "OTHER": 一般閒聊。
    客戶訊息："{text}"
    """
    response = model.generate_content(prompt)
    return response.text.strip()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    intent = analyze_intent(user_message)
    
    if "BUY" in intent:
        reply_text = "我們這裡由老闆統一回覆，請您稍等一下！"
        send_telegram_notification(f"🔴 *【高意願詢問】*：{user_message}")
    elif "TIME" in intent:
        reply_text = "收到！我已經幫您把時間記錄下來囉，請稍等一下由老闆跟您確認！"
        send_telegram_notification(f"🟢 *【客戶預約】*：{user_message}")
    else:
        reply_text = "有的！請問是想看哪種類型的車呢？"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)
