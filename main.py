import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# 請務必確保環境變數已設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的LINE_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的LINE_SECRET")
TELEGRAM_BOT_TOKEN = "8345028959:AAGp7LAqW4AEJUH1VHg8r7N0yWNjnDIMdTM"
TELEGRAM_CHAT_ID = "7468110837"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    # 1. 優先判斷：技術改裝 (最重要，優先攔截)
    upgrade_keywords = ["車架", "變速器", "變數器", "大盤", "功率", "碟盤", "輪框", "改裝", "升級", "維修"]
    is_upgrade = any(kw in user_message for kw in upgrade_keywords)
    
    # 2. 次要判斷：商品詢價與預算 (包含預算、價格、商品名稱)
    items = ["公路車", "登山車", "車衣", "安全帽", "帽子", "水壺", "眼鏡", "卡鞋"]
    budget_words = ["預算", "價格", "多少", "元", "萬"]
    is_selling = any(item in user_message for item in items) or any(bw in user_message for bw in budget_words)
    
    # 3. 三級判斷：時間預約
    is_time = any(kw in user_message for kw in ["點", "明天", "今天", "週末", "下午", "晚上"])

    # 執行邏輯與 Telegram 通知
    if is_upgrade:
        reply_text = "關於改裝與專業零組件的問題，我們由老闆親自為您說明，請您稍等一下喔！"
        send_telegram_notification(f"🔴 *【技術/改裝諮詢】*\n💬 「{user_message}」\n👉 請前往 LINE 處理！")
    
    elif is_selling:
        reply_text = "收到您的需求！您可以直接來店裡看看實品，或是由我幫您推薦幾款店內 CP 值很不錯的選擇唷！"
        send_telegram_notification(f"🟡 *【商品詢價/預算】*\n💬 「{user_message}」\n💡 *老闆注意*：推薦店內 CP 值高一點的給客戶！")
        
    elif is_time:
        reply_text = f"收到！您提到「{user_message}」，我已經幫您記錄下來囉，請稍等一下由老闆跟您確認！"
        send_telegram_notification(f"🟢 *【預約時間】*\n💬 「{user_message}」\n👉 請前往 LINE 確認排程！")
        
    else:
        reply_text = "真不好意思，您的問題比較特別，我已經請老闆來協助您，請稍等一下喔！"
        send_telegram_notification(f"⚠️ *【待處理詢問】*\n💬 「{user_message}」\n👉 請前往 LINE 查看！")

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)
