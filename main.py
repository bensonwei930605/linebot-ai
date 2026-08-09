import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# 設定變數
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
    
    # 1. 技術改裝關鍵字
    upgrade_kws = ["車架", "變速器", "變數器", "大盤", "功率", "碟盤", "輪框", "改裝", "升級", "維修"]
    is_upgrade = any(kw in user_message for kw in upgrade_kws)
    
    # 2. 商品與預算關鍵字
    items = ["公路車", "登山車", "車衣", "安全帽", "帽子", "水壺", "眼鏡", "卡鞋"]
    budget_kws = ["預算", "價格", "多少", "元", "萬"]
    is_selling = any(item in user_message for item in items) or any(bw in user_message for bw in budget_kws)
    
    # 3. 精準時間預約 (必須同時有「約/空/幾點」以及「時間詞」才判定)
    time_verbs = ["幾點", "約", "過去", "空", "預約", "確認", "時間"]
    time_nouns = ["點", "明天", "今天", "週末", "下午", "晚上"]
    is_time = any(v in user_message for v in time_verbs) and any(n in user_message for n in time_nouns)

    # 判斷邏輯
    if is_upgrade:
        reply = "關於改裝與專業零組件的問題，我們由老闆親自為您說明，請您稍等一下喔！"
        send_telegram_notification(f"🔴 *【技術諮詢】*：{user_message}")
    
    elif is_selling:
        reply = "收到您的需求！您可以直接來店裡看看實品，或是由我幫您推薦幾款店內 CP 值很不錯的選擇唷！"
        send_telegram_notification(f"🟡 *【商品詢價】*：{user_message}")
        
    elif is_time:
        reply = f"收到！您提到「{user_message}」，我已經幫您記錄下來囉，請稍等一下由老闆跟您確認！"
        send_telegram_notification(f"🟢 *【預約時間】*：{user_message}")
        
    else:
        reply = "真不好意思，您的問題比較特別，我已經請老闆來協助您，請稍等一下喔！"
        send_telegram_notification(f"⚠️ *【待處理】*：{user_message}")

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=5000)
