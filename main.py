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
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ["爸", "長輩", "老人家", "父親", "公公", "媽", "老婆", "女友", "弟", "哥", "妹", "姊", "小朋友", "小孩", "兒童"]):
        strategy_1 = "• 客戶想幫親友選車，目前缺乏具體身高、預算與騎乘習慣等細節。"
        strategy_2 = "• 漸進式引導方向：先詢問對方的大約身高、平時騎乘路段（休閒運動或通勤）以及預算範圍。"
        strategy_3 = "• 建議直接回覆：「可以先跟我透露一下對方的大約身高跟平常主要是想休閒騎還是運動嗎？這樣店長比較好幫你挑選最適合的車款跟尺寸喔！」"
    elif any(kw in text_lower for kw in ["調整", "調校", "器材", "異音", "維修", "預約"]):
        strategy_1 = "• 客戶有車輛專業調整、抓異音或賽事調校需求。"
        strategy_2 = "• 車友對技術支援黏著度極高。"
        strategy_3 = "• 建議直接回覆：「沒問題！我們店裡有專業校正器材，直接把車帶過來我們幫你處理！」"
    elif any(kw in text_lower for kw in ["10萬", "預算", "車款", "規格", "差別"]):
        strategy_1 = "• 客戶有明確預算或成車規格比較需求。"
        strategy_2 = "• 市面熱門推薦：碳纖車架搭配電變組合。"
        strategy_3 = "• 建議直接回覆：「這預算可以看性價比極高的碳纖車款，這週末有空直接來店裡看實車最快！」"
    else:
        strategy_1 = "• 客戶進行一般性詢問，意圖不明確。"
        strategy_2 = "• 以親切口語反問來破冰。"
        strategy_3 = "• 建議直接回覆：「嗨囉！最近有想幫車子升級還是看新車嗎？隨時跟我說～」"

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
    
    # 採取漸進式問答，反問客戶細節，拒絕文不對題的死板罐頭
    if any(kw in text_lower for kw in ["爸", "長輩", "老人家", "父親", "公公", "媽", "老婆", "女友", "弟", "哥", "妹", "姊", "小朋友", "小孩", "兒童"]):
        reply_text = "沒問題！想幫家人看車的話，可以先跟我透露一下對方的大約身高，以及平常主要是想輕鬆騎休閒的，還是騎帥好看的呢？"
    elif any(kw in text_lower for kw in ["調整", "調校", "器材", "異音", "維修", "預約"]):
        reply_text = "有的！我們店裡有專門的校正器材可以處理這塊，不管是異音還是賽事調校都可以搞定，直接把車帶過來我們幫你看看！"
    elif any(kw in text_lower for kw in ["10萬", "預算", "車款", "規格", "差別"]):
        reply_text = "10萬這個預算能選到配備很不錯的車款耶！店長晚點忙完會親自幫你挑幾台最划算的出來，或者你這週末有空直接來店裡看實車最快！"
    else:
        reply_text = "嗨囉！訊息都有收到囉～ 我先跟店長說一聲，他忙完就會馬上回覆你！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
    s1, s2, s3 = generate_three_strategies(user_message)
    
    telegram_msg = (
        f"🔴 *【高意願客戶詢問通知】*\n"
        f"💬 *客戶原話*：「{user_message}」\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 *【老闆專屬：漸進式應對策略】*\n\n"
        f"1️⃣ *【需求解析】*\n{s1}\n\n"
        f"2️⃣ *【引導方向】*\n{s2}\n\n"
        f"3️⃣ *【建議回覆講法】*\n{s3}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👉 請前往 LINE 官方帳號查看詳情！"
    )
    
    send_telegram_notification(telegram_msg)

if __name__ == "__main__":
    app.run(port=5000)
