import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# LINE 官方帳號設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的LINE_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的LINE_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Telegram 機器人設定 (剛剛取得的新資料)
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

def analyze_customer_intent(text):
    """
    智慧分析客戶需求、評估意願並給出燈號與建議
    """
    text_lower = text.lower()
    
    # 定義高意願紅燈關鍵字
    red_keywords = ["預算", "10萬", "車款", "現貨", "多少錢", "報價", "下單", "匯款", "急", "器材", "調整", "調校", "預約"]
    # 定義中意願黃燈關鍵字
    yellow_keywords = ["怎麼用", "差別", "規格", "比較", "推薦", "功能"]

    if any(kw in text_lower for kw in red_keywords):
        light = "🔴 *【紅燈 - 高購買意願 / 專業需求】*"
        intention = "高（有明確預算、高單價車款詢問或專業技術調校需求）"
        suggestion = "建議優先回覆，可直接切入規格、車款推薦或詢問預約調整時間。"
    elif any(kw in text_lower for kw in yellow_keywords):
        light = "🟡 *【黃燈 - 評估中 / 規格詢問】*"
        intention = "中（正在做功課、比較功能與價格）"
        suggestion = "可提供專業解答與比較優勢，建立信任感。"
    else:
        light = "🟢 *【綠燈 - 一般對話 / 諮詢】*"
        intention = "低或初步接觸"
        suggestion = "制式回覆或引導說出實際需求。"

    return light, intention, suggestion

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
    
    # 進行智慧燈號與需求分析
    light, intention, suggestion = analyze_customer_intent(user_message)
    
    # 組合要發送到 Telegram 的專業幕僚摘要報告
    telegram_msg = (
        f"{light}\n\n"
        f"📝 *【AI 智能需求分析報告】*\n"
        f"• *客戶意願*：{intention}\n"
        f"• *建議對策*：{suggestion}\n\n"
        f"💬 *最新對話*：「{user_message}」\n\n"
        f"👉 請盡快前往 LINE 官方帳號查看並回覆客人！"
    )
    
    # 發送通知到 Telegram
    send_telegram_notification(telegram_msg)

if __name__ == "__main__":
    app.run(port=5000)
