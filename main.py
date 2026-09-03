import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# 設定變數 (請確保在部署環境中設定了這四個環境變數)
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
    
    # 1. 專業療程與技術關鍵字 (取代原本的改裝)
    service_kws = ["卸甲", "延甲", "接睫毛", "保養", "款式", "指定", "設計", "痛", "過敏", "重做", "光療", "凝膠"]
    is_service = any(kw in user_message for kw in service_kws)
    
    # 2. 服務詢價關鍵字 (取代原本的商品與預算)
    price_kws = ["預算", "價格", "多少錢", "費用", "價目表", "怎麼算", "打折", "優惠"]
    is_pricing = any(pw in user_message for pw in price_kws)

    # 3. 營業時間關鍵字
    hours_kws = ["營業", "開門", "關門", "打烊", "幾點開", "幾點關", "休息", "店休", "公休"]
    is_hours = any(kw in user_message for kw in hours_kws)
    
    # 4. 嚴格的時間預約判定
    time_actions = ["幾點", "約", "空", "預約", "時間", "行嗎", "可以嗎", "過去", "排", "做指甲"]
    time_points = ["點", "明天", "後天", "週末", "下午", "晚上", "早上", "禮拜", "星期", "週", "號", "今天"]
    is_time = any(act in user_message for act in time_actions) and any(pt in user_message for pt in time_points)

    # ---------------- 核心修改邏輯開始 ----------------
    # 建立空清單，用來收集要回覆給客人的話，以及要推播給老闆的標籤
    reply_texts = []
    tg_alerts = []

    # 判斷一：營業時間 (不需推播老闆)
    if is_hours:
        reply_texts.append("🌸 我們的營業時間是週一至週六 10:00 - 20:00（週日公休）喔！")

    # 判斷二：專業療程諮詢
    if is_service:
        reply_texts.append("關於款式細節或是特定療程（如卸甲/延甲），因為每個人的狀況不同，我已經先幫您記錄下來，稍等一下由設計師親自評估後回覆您會比較準確喔！💅")
        tg_alerts.append("🔴 *【療程細節諮詢】*")

    # 判斷三：服務詢價
    if is_pricing:
        reply_texts.append("✨ 我們的單色凝膠是 $999、造型光療是 $1,399 起！如果有他店的卸甲需求，會酌收 $300 喔。如果您有喜歡的款式圖片，也可以直接傳過來讓設計師幫您報價！")
        tg_alerts.append("🟡 *【服務詢價】*")

    # 判斷四：預約時間
    if is_time:
        reply_texts.append("收到您的時間需求！為了幫您準確評估需要的時長，想請問您這次想做什麼項目呢？（例如：單色、造型光療、需不需要卸甲？）請稍等一下，設計師看完行事曆馬上為您確認空檔喔！💕")
        tg_alerts.append("🟢 *【預約時間確認】*")

    # 執行回覆與推播
    if reply_texts:
        # 將所有符合的答案，用換行符號合併成一大段訊息傳給客人
        final_reply = "\n\n".join(reply_texts)
    else:
        # 如果都沒有命中關鍵字，給予預設回覆
        final_reply = "收到您的訊息！如果您有比較急的問題，或是想詢問特定的美甲美睫款式，請稍等我們一下，設計師忙完會立刻回覆您喔！✨"
        
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=final_reply))
        
    if tg_alerts:
        # 如果有多個需求，將標籤串接起來
        tags = " & ".join(tg_alerts)
        tg_msg = (
            f"{tags}\n"
            f"客戶訊息：{user_message}\n\n"
            f"⚠️ *老闆請注意：請盡快至後台回覆與確認！*\n"
            f"👉 https://manager.line.biz/"
        )
        send_telegram_notification(tg_msg)

if __name__ == "__main__":
    app.run(port=5000)
