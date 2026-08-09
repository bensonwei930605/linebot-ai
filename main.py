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
    
    # 1. 擴充業務/商品/零組件關鍵字（含車款、配件、專業零組件及常見注音）
    buy_keywords = [
        # 整車與預算
        "公路車", "登山車", "預算", "萬", "元", "車款", "買車", "價格", "多少錢",
        # 配件
        "車衣", "安全帽", "水壺", "眼鏡", "車用眼鏡", "卡鞋", "配件", "裝備",
        # 專業零組件與升級改裝
        "車架", "變速器", "變數器", "大盤", "功率大盤", "功率計", "碟盤", "輪框", "輪組", "零件", "改裝",
        # 注音文防護
        "ㄍㄨㄥ", "ㄌㄨˋ", "ㄔㄜ", "ㄉㄥˊ", "ㄕㄢ", "登山", "公路"
    ]
    is_buy_query = any(kw in user_message for kw in buy_keywords)
    
    # 2. 時間判斷
    is_time_query = any(kw in user_message for kw in ["點", "明天", "今天", "週末", "平日", "上午", "下午", "晚上"]) or user_message.isdigit()

    if is_buy_query:
        reply_text = "我們這裡由老闆統一回覆，請您稍等一下！"
        telegram_msg = (
            f"🔴 *【準客戶高意願詢問（車款/零件/配件）】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 請前往 LINE 官方帳號手動回覆！"
        )
        send_telegram_notification(telegram_msg)
        
    elif is_time_query:
        reply_text = f"收到！您提到「{user_message}」，我已經幫您把時間記錄下來囉，請稍等一下由老闆跟您確認！"
        telegram_msg = (
            f"🟢 *【客戶已敲定時間】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 請前往 LINE 官方帳號手動回覆！"
        )
        send_telegram_notification(telegram_msg)
        
    else:
        reply_text = "真不好意思，您的問題比較特別，我已經立刻通知老闆本人來為您解答，請您稍等一下喔！"
        telegram_msg = (
            f"⚠️ *【機器人無法辨識，已轉交老闆】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 請馬上前往 LINE 手動接手！"
        )
        send_telegram_notification(telegram_msg)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)
