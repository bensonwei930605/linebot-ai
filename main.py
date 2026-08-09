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
    
    # 🛑 絕對防禦攔截
    is_budget_query = any(keyword in user_message for keyword in ["公路車", "登山車", "預算", "萬", "元"])
    
    if is_budget_query:
        reply_text = "我們這裡由老闆統一回覆，請您稍等一下！"
        s1 = f"• 客戶詢問預算車款（原話：{user_message}）。"
        s2 = "• 觸發絕對防禦攔截，交由老闆手動處理。"
        s3 = f"• 當前機器人回覆：「{reply_text}」"
    else:
        reply_text = "有的！這就幫您確認，看這週末或平日哪時候比較方便過來呢？"
        s1 = "• 客戶進行一般性對話。"
        s2 = "• 引導至實體賞車或預約。"
        s3 = f"• 當前機器人回覆：「{reply_text}」"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
    telegram_msg = (
        f"🔴 *【客戶對話動態通知】*\n"
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

if __name__ == "__main__":
    app.run(port=5000)
