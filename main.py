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
    
    # 1. 【改裝/升級/零組件專區】（需要老闆親自處理的專業問題）
    upgrade_keywords = [
        "車架", "變速器", "變數器", "大盤", "功率大盤", "功率計", "碟盤", "輪框", "輪組", 
        "改裝", "升級", "維修", "保養", "檢修", "組車"
    ]
    is_upgrade_query = any(kw in user_message for kw in upgrade_keywords)
    
    # 2. 【一般買東西/配件/預約詢問】（AI 可以直接在 LINE 回覆的常規問題）
    shop_keywords = [
        "公路車", "登山車", "預算", "萬", "元", "車款", "買車", "價格", "多少錢",
        "車衣", "安全帽", "水壺", "眼鏡", "車用眼鏡", "卡鞋", "配件", "裝備",
        "點", "明天", "今天", "週末", "平日", "上午", "下午", "晚上"
    ] or user_message.isdigit()
    is_shop_query = any(kw in user_message for kw in shop_keywords)

    if is_upgrade_query:
        # 🚨 改裝/專業問題：立刻發送 Telegram 通知老闆接手，LINE 回覆請稍等
        reply_text = "關於改裝與專業零組件的問題，我們由老闆親自為您說明，請您稍等一下喔！"
        telegram_msg = (
            f"🔴 *【客戶詢問改裝/零組件】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 屬於技術/改裝問題，**請前往 LINE 手動接手！**"
        )
        send_telegram_notification(telegram_msg)
        
    elif is_shop_query:
        # 🟢 一般買車或看配件：AI 直接在 LINE 應對，不打擾老闆
        reply_text = "有的！我們店裡有提供這類型的車款與周邊配件，歡迎直接過來店裡看看，或是告訴我您的需求與預算唷！"
        
    else:
        # ⚠️ 完全看不懂的亂碼或特殊閒聊
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
