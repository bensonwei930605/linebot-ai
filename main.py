import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

# LINE 官方帳號設定
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

def generate_three_strategies(text):
    """
    針對客戶訊息，自動生成 3 種真人化應對策略報告
    """
    text_lower = text.lower()
    
    if "10" in text or "預算" in text or "車款" in text or "推薦" in text:
        strategy_1 = "• 客戶手握 10 萬左右預算，想找高階或進階車款，目標明確且購買意願很高。"
        strategy_2 = "• 市面上這個價位帶最熱門的是碳纖車架搭配 105 電變（像是 TCR 或同級車款），車友接受度極高。"
        strategy_3 = "• 建議直接回覆：「10萬預算選擇其實非常多！店裡剛好有幾台熱門現車可以看，這週末有空直接過來店裡，順便幫你抓一下騎乘姿勢跟尺寸最準！」"
    elif "調整" in text or "調校" in text or "器材" in text or "異音" in text:
        strategy_1 = "• 客戶有實際的車輛調整、抓異音或賽事調校需求，痛點明確。"
        strategy_2 = "• 車友對 Fitting 跟異音處理通常很急，只要技術到位很容易直接黏著度拉滿。"
        strategy_3 = "• 建議直接回覆：「沒問題！我們店裡有專業的校正器材可以幫忙處理。看你平日還是週末方便，直接把車帶過來我們現場幫你檢查！」"
    else:
        strategy_1 = "• 客戶初步打招呼或隨性詢問，意圖還在摸索中。"
        strategy_2 = "• 保持輕鬆、像朋友聊天的語氣破冰，不要給人壓力。"
        strategy_3 = "• 建議直接回覆：「嗨囉！最近有打算騎車去哪裡晃晃嗎？還是有想看哪種類型的車，隨時跟我說～」"

    return strategy_1, strategy_2, strategy_3

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
    
    # 1. 模仿真人對話的 LINE 自動回覆（完全捨棄死板罐頭訊息）
    if any(kw in text_lower for kw in ["調整", "調校", "器材", "異音", "維修", "預約"]):
        reply_text = "有的！我們店裡有專門的校正器材可以處理這塊，不管是異音還是賽事調校都可以搞定。看你平日還是這週末方便，直接把車帶過來我們幫你看看！"
    elif any(kw in text_lower for kw in ["預算", "10萬", "車款", "規格", "差別", "推薦"]):
        reply_text = "10萬這個預算能選到配備很不錯的車款耶！店長晚點忙完會親自幫你挑幾台最划算的出來，或者你這週末有空直接來店裡看實車最快！"
    else:
        reply_text = "嗨囉！訊息都有收到囉～ 我先跟店長說一聲，他忙完就會馬上回覆你！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
    # 2. 生成 3 種應對策略
    s1, s2, s3 = generate_three_strategies(user_message)
    
    # 3. 推送到 Telegram 的老闆專屬報告
    telegram_msg = (
        f"🔴 *【高意願客戶詢問通知】*\n"
        f"💬 *客戶原話*：「{user_message}」\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 *【老闆專屬：3種真人化應對策略】*\n\n"
        f"1️⃣ *【客戶需求解析】*\n{s1}\n\n"
        f"2️⃣ *【市面熱門方向】*\n{s2}\n\n"
        f"3️⃣ *【建議直接切入的講法】*\n{s3}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👉 請前往 LINE 官方帳號查看詳情！"
    )
    
    send_telegram_notification(telegram_msg)

if __name__ == "__main__":
    app.run(port=5000)
