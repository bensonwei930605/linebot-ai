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

    # 3. 營業時間關鍵字
    hours_kws = ["營業", "開門", "關門", "打烊", "幾點開", "幾點關", "休息", "店休"]
    is_hours = any(kw in user_message for kw in hours_kws)
    
    # 4. 嚴格的時間預約判定
    time_actions = ["幾點", "約", "空", "預約", "時間", "行嗎", "可以嗎", "過去"]
    time_points = # 更新後的（加入星期、週、禮拜、號）
time_points = ["點", "明天", "後天", "週末", "下午", "晚上", "早上", "禮拜", "星期", "週", "號", "今天"]
    is_time = any(act in user_message for act in time_actions) and any(pt in user_message for pt in time_points)

    # ---------------- 核心修改邏輯開始 ----------------
    # 建立空清單，用來收集要回覆給客人的話，以及要推播給老闆的標籤
    reply_texts = []
    tg_alerts = []

    # 判斷一：營業時間 (不需推播老闆)
    if is_hours:
        reply_texts.append("我們都是早上8點到晚上8點，歡迎來店裡看看！")

    # 判斷二：技術改裝
    if is_upgrade:
        reply_texts.append("關於改裝與專業零組件的問題，我們由老闆親自為您說明，請您稍等一下喔！")
        tg_alerts.append("🔴 *【技術諮詢】*")

    # 判斷三：商品詢價
    if is_selling:
        reply_texts.append("收到您的需求！您可以直接來店裡看看實品，或是由我幫您推薦幾款店內 CP 值很不錯的選擇唷！")
        tg_alerts.append("🟡 *【商品詢價】*")

    # 判斷四：預約時間
    if is_time:
        reply_texts.append("收到！想請問您這次想要預約什麼項目呢？（例如：車輛檢修、改裝、或是看車），我已經先幫您記錄下來囉，請稍等一下由老闆跟您確認時間！")
        tg_alerts.append("🟢 *【預約時間】*")

    # 執行回覆與推播
    if reply_texts:
        # 將所有符合的答案，用換行符號合併成一大段訊息傳給客人
        final_reply = "\n\n".join(reply_texts)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=final_reply))
        
    if tg_alerts:
        # 如果有多個需求，將標籤串接起來 (例如: 🔴 *【技術諮詢】* & 🟢 *【預約時間】*)
        tags = " & ".join(tg_alerts)
        tg_msg = (
            f"{tags}\n"
            f"客戶訊息：{user_message}\n\n"
            f"⚠️ *老闆請注意：請盡快至後台回覆與確認！*\n"
            f"👉 https://manager.line.biz/"
        )
        send_telegram_notification(tg_msg)
