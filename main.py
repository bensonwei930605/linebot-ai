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
    
    # 1. 技術改裝關鍵字
    upgrade_kws = ["車架", "變速器", "變數器", "大盤", "功率", "碟盤", "輪框", "改裝", "升級", "維修", "怪怪的"]
    is_upgrade = any(kw in user_message for kw in upgrade_kws)
    
    # 2. 商品與預算關鍵字
    items = ["公路車", "登山車", "車衣", "安全帽", "帽子", "水壺", "眼鏡", "卡鞋"]
    budget_kws = ["預算", "價格", "多少", "元", "萬"]
    is_selling = any(item in user_message for item in items) or any(bw in user_message for bw in budget_kws)

    # 3. 營業時間關鍵字 (新增！)
    hours_kws = ["營業", "開門", "關門", "打烊", "幾點開", "幾點關"]
    is_hours = any(kw in user_message for kw in hours_kws)
    
    # 4. 嚴格的時間預約判定
    time_actions = ["幾點", "約", "空", "預約", "時間", "行嗎", "可以嗎"]
    time_points = ["點", "明天", "後天", "週末", "下午", "晚上", "早上", "這禮拜"]
    is_time = any(act in user_message for act in time_actions) and any(pt in user_message for pt in time_points)

    # 判斷邏輯與回覆
    if is_upgrade:
        reply = "關於改裝與專業零組件的問題，我們由老闆親自為您說明，請您稍等一下喔！"
        send_telegram_notification(f"🔴 *【技術諮詢】*：{user_message}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        
    elif is_selling:
        reply = "收到您的需求！您可以直接來店裡看看實品，或是由我幫您推薦幾款店內 CP 值很不錯的選擇唷！"
        send_telegram_notification(f"🟡 *【商品詢價】*：{user_message}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        
    elif is_hours:
        # 單純詢問營業時間，直接回覆，不發 Telegram 打擾老闆
        reply = "我們都是早上8點到晚上8點，歡迎來店裡看看！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif is_time:
        # 預約項目追問
        reply = "收到！想請問您這次想要預約什麼項目呢？（例如：車輛檢修、改裝、或是看車買裝備），我已經先幫您記錄下來囉，請稍等一下由老闆跟您確認時間！"
        
        # 預約通知加上老闆確認指引與後台快速連結
        tg_msg = (
            f"🟢 *【預約時間】*\n"
            f"客戶訊息：{user_message}\n\n"
            f"⚠️ *老闆請注意：請盡快與客戶確認預約項目與時間！*\n"
            f"👉 請至 LINE OA 後台回覆：https://manager.line.biz/"
        )
        send_telegram_notification(tg_msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        
    else:
        # 閒聊、打招呼：完全不回覆 LINE、不發 Telegram，保持對話安靜
        return

if __name__ == "__main__":
    app.run(port=5000)
    
