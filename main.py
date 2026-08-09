import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

TELEGRAM_BOT_TOKEN = "8345028959:AAGp7LAqW4AEJUH1VHg8r7N0yWNjnDIMdTM"
TELEGRAM_CHAT_ID = "7468110837"

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram 推播失敗: {e}")

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
    
    # 1. 專業改裝/升級關鍵字（需要老闆技術處理）
    upgrade_keywords = [
        "車架", "變速器", "變數器", "大盤", "功率大盤", "功率計", "碟盤", "輪框", "輪組", 
        "改裝", "升級", "維修", "保養", "檢修", "組車"
    ]
    is_upgrade_query = any(kw in user_message for kw in upgrade_keywords)
    
    # 2. 判斷是否包含「賣」字，且同時包含商品/配件名稱
    items = ["公路車", "登山車", "車衣", "安全帽", "水壺", "眼鏡", "車用眼鏡", "卡鞋", "輪框", "大盤", "變速器"]
    has_mai = "賣" in user_message
    has_item = any(item in user_message for item in items)
    is_selling_inquiry = has_mai and has_item

    # 3. 時間/預約判斷
    is_time_query = any(kw in user_message for kw in ["點", "明天", "今天", "週末", "平日", "上午", "下午", "晚上"]) or user_message.isdigit()

    if is_upgrade_query:
        # 技術改裝問題：通知老闆
        reply_text = "關於改裝與專業零組件的問題，我們由老闆親自為您說明，請您稍等一下喔！"
        telegram_msg = (
            f"🔴 *【客戶詢問改裝/零組件】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 屬於技術/改裝問題，請前往 LINE 手動接手！"
        )
        send_telegram_notification(telegram_msg)
        
    elif is_selling_inquiry:
        # 🟢 同時有「賣」跟「商品」：AI 回覆客氣話，並發送 Telegram 提醒老闆推薦高 CP 值商品
        reply_text = "有的！您可以直接來我們店裡看看實品唷，有任何需求都可以幫您介紹！"
        telegram_msg = (
            f"🟡 *【客戶詢問商品販售】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"💡 *老闆注意*：客戶在詢問商品，**推薦店內 CP 值高一點的**，請前往 LINE 接手！"
        )
        send_telegram_notification(telegram_msg)
        
    elif is_time_query:
        # 預約時間
        reply_text = f"收到！您提到「{user_message}」，我已經幫您把時間記錄下來囉，請稍等一下由老闆跟您確認！"
        telegram_msg = (
            f"🟢 *【客戶已敲定時間】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 請前往 LINE 官方帳號手動接手！"
        )
        send_telegram_notification(telegram_msg)
        
    else:
        # 其他閒聊
        reply_text = "真不好意思，您的問題比較特別，我已經請老闆來協助您，請稍等一下喔！"
        telegram_msg = (
            f"⚠️ *【機器人無法辨識】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 請前往 LINE 看看狀況！"
        )
        send_telegram_notification(telegram_msg)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)
