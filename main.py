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
    
    if any(kw in text_lower for kw in ["爸", "長輩", "老人家", "父親", "公公", "媽", "老婆", "女友", "女生"]):
        strategy_1 = "• 客戶想幫家人或伴侶買車，注重舒適度、騎乘輕鬆或車身好看（非純競速）。"
        strategy_2 = "• 市面熱門推薦：舒適型公路車、平把公路車或好看的都會休閒車款。"
        strategy_3 = "• 建議直接回覆：「如果是買給另一半或長輩，通常會推薦騎起來比較舒適或車身線條好看的平把車！店裡有好幾款很適合，這週末帶她一起來店裡看看最準！」"
    elif any(kw in text_lower for kw in ["小朋友", "小孩", "兒童", "幾歲"]):
        strategy_1 = "• 客戶想尋找適合兒童/小朋友騎乘的腳踏車。"
        strategy_2 = "• 市面常見熱門推薦：12-20吋輕量化童車或變速小徑車。"
        strategy_3 = "• 建議直接回覆：「小朋友的車要看身高挑尺寸，店裡有好幾款安全又好騎的小車，這週末可以帶小朋友來看看！」"
    elif any(kw in text_lower for kw in ["調整", "調校", "器材", "異音", "維修", "預約"]):
        strategy_1 = "• 客戶有車輛專業調整、抓異音或賽事調校需求。"
        strategy_2 = "• 車友對技術支援黏著度極高。"
        strategy_3 = "• 建議直接回覆：「沒問題！我們店裡有專業校正器材，直接把車帶過來我們幫你處理！」"
    elif any(kw in text_lower for kw in ["10萬", "預算", "車款"]):
        strategy_1 = "• 客戶手握明確高預算，想找進階或高階成車。"
        strategy_2 = "• 市面熱門推薦：碳纖車架搭配 105 電變。"
        strategy_3 = "• 建議直接回覆：「10萬預算可以直接看碳纖車配電變的款式，這週末有空直接來店裡看實車！」"
    else:
        strategy_1 = "• 客戶進行一般性詢問。"
        strategy_2 = "• 保持輕鬆親切的對話節奏。"
        strategy_3 = "• 建議直接回覆：「嗨囉！有想看哪種類型的車嗎，隨時跟我說～」"

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
    
    # 優先檢查特定對象（爸、老婆、長輩等），避免被後面的推薦字眼攔截
    if any(kw in text_lower for kw in ["爸", "長輩", "老人家", "父親", "公公", "媽", "老婆", "女友", "女生"]):
        reply_text = "如果是買給家人或另一半，通常會推薦騎起來比較舒適、不用趴太低的平把車或休閒車款！店裡剛好有幾台很適合的現車，這週末有空可以帶她/他一起來店裡看看喔！"
    elif any(kw in text_lower for kw in ["小朋友", "小孩", "兒童", "幾歲"]):
        reply_text = "要看小朋友的大約身高或年齡來挑尺寸喔！店裡目前有幾款適合的小車，這週末有空可以帶小朋友來店裡試試看尺寸最準！"
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
