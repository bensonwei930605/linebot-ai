import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# LINE 官方帳號設定
# 請確保在 Render 的 Environment Variables 或下方填入正確的 Token 與 Secret
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

def analyze_customer_intent(text):
    """
    智慧分析客戶需求、評估意願並給出燈號與建議
    """
    text_lower = text.lower()
    
    red_keywords = ["預算", "10萬", "車款", "現貨", "多少錢", "報價", "下單", "匯款", "急", "器材", "調整", "調校", "預約"]
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
    text_lower = user_message.lower()
    
    # 1. 根據客人的不同問題內容，給予適當且具體的 LINE 自動回覆
    if any(kw in text_lower for kw in ["調整", "調校", "器材", "異音", "維修", "預約"]):
        reply_text = "是的，我們店內擁有專業的器材，可以協助您進行腳踏車上的各類調整，包括異音排除和賽事調校。若需要預約或有特定需求，請告訴我！"
    elif any(kw in text_lower for kw in ["預算", "10萬", "車款", "規格", "差別", "推薦"]):
        reply_text = "這款車在性價比與性能上非常出色！針對您的需求，店長可以幫您做更詳細的規格對比與搭配，我已經通知店長了，稍後會親自為您說明！"
    else:
        reply_text = "收到您的詢問！這部分我已經幫您通知店長（老闆）了，老闆稍後會親自回覆您！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
    # 2. 進行智慧燈號與需求分析
    light, intention, suggestion = analyze_customer_intent(user_message)
    
    # 3. 組合發送到 Telegram 的專業幕僚摘要報告
    telegram_msg = (
        f"{light}\n\n"
        f"📝 *【AI 智能需求分析報告】*\n"
        f"• *客戶意願*：{intention}\n"
        f"• *建議對策*：{suggestion}\n\n"
        f"💬 *最新對話*：「{user_message}」\n\n"
        f"👉 請盡快前往 LINE 官方帳號查看並回覆客人！"
    )
    
    # 4. 發送通知到 Telegram
    send_telegram_notification(telegram_msg)

if __name__ == "__main__":
    app.run(port=5000)
