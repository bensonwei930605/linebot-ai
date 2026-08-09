import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# LINE 官方帳號設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Telegram 機器人設定
TELEGRAM_BOT_TOKEN = "8345028959:AAGp7LAqW4AEJUH1VHg8r7N0yWNjnDIMdTM"
TELEGRAM_CHAT_ID = "7468110837"

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram 推播失敗: {e}")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    # 1. 判斷是否為預算或車款詢問
    is_budget_query = any(keyword in user_message for keyword in ["公路車", "登山車", "預算", "萬", "元"])
    
    # 2. 判斷是否為時間/數字回覆（例如客戶回答幾點、8點等）
    is_time_query = any(keyword in user_message for keyword in ["點", "明天", "今天", "週末", "平日", "上午", "下午", "晚上"]) or user_message.isdigit()

    if is_budget_query:
        reply_text = "我們這裡由老闆統一回覆，請您稍等一下！"
        s1 = f"• 客戶指定了具體車款或預算（原話：{user_message}）。"
        s2 = "• 觸發精準攔截，交由老闆手動處理。"
        s3 = f"• 當前機器人回覆：「{reply_text}」"
        
        telegram_msg = (
            f"🔴 *【準客戶高意願詢問】*\n"
            f"💬 *客戶原話*：「{user_message}」\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 *【老闆專屬：應對策略】*\n\n"
            f"1️⃣ *【需求解析】*\n{s1}\n\n"
            f"2️⃣ *【引導方向】*\n{s2}\n\n"
            f"3️⃣ *【建議回覆講法】*\n{s3}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"👉 請前往 LINE 官方帳號手動回覆！"
        )
        send_telegram_notification(telegram_msg)
        
    elif is_time_query:
        # 當客戶回覆時間時，給予更合理的承接語，而不是鬼打牆
        reply_text = f"收到！您提到「{user_message}」，我已經幫您把時間記錄下來囉，請稍等一下由老闆跟您確認！"
        
        # 同時發送 Telegram 讓老闆知道客戶敲定時間了
        telegram_msg = (
            f"🟢 *【客戶已敲定時間】*\n"
            f"💬 *客戶原話*：「{user_message}」\n\n"
            f"👉 客戶正在預約時間，請盡快前往 LINE 回覆！"
        )
        send_telegram_notification(telegram_msg)
    else:
        # 一般閒聊對話
        reply_text = "有的！請問是想看哪種類型的車呢？"

    # 發送 LINE 回覆
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)
