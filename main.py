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
    
    if any(kw in text_lower for kw in ["調整", "調校", "器材", "異音", "維修", "預約", "週末", "店", "今天"]):
        strategy_1 = "• 客戶有具體預約、看車或技術調整需求，意圖非常明確。"
        strategy_2 = "• 引導確認到店時間，加速預約成交。"
        strategy_3 = "• 建議直接回覆：「沒問題！我們店裡有專門器材可以處理，那您看今天或是這週末大約什麼時候方便過來呢？」"
    elif any(kw in text_lower for kw in ["女生", "女性", "女孩", "女友", "老婆"]):
        strategy_1 = "• 客戶詢問女性適合的車款，未提及身高或預算。"
        strategy_2 = "• 漸進式引導方向：詢問身高與騎乘用途。"
        strategy_3 = "• 建議直接回覆：「女生騎的話，主要看身高還有是要輕鬆休閒騎還是運動流汗居多！可以先透露一下身高，店裡有幾款車身好看又好騎的車款很推薦喔！」"
    elif any(kw in text_lower for kw in ["價格", "多少錢", "大約價", "費用", "怎麼賣"]):
        strategy_1 = "• 客戶詢問籠統價格，未指定具體車款。"
        strategy_2 = "• 漸進式引導方向：反問對方的預算範圍。"
        strategy_3 = "• 建議直接回覆：「這主要看您的預算大概抓多少喔！從幾千元的代步車到十幾萬的高階車我們都有，可以先跟我說您的預算範圍～」"
    elif any(kw in text_lower for kw in ["爸", "長輩", "老人家", "父親", "公公", "媽", "弟", "哥", "妹", "姊", "小朋友", "小孩", "兒童", "推薦", "想買"]):
        strategy_1 = "• 客戶想詢問買車推薦，但未明講車款類型與預算。"
        strategy_2 = "• 漸進式引導方向：詢問公路車、登山車還是兒童車。"
        strategy_3 = "• 建議直接回覆：「那您是想要公路車、登山車還是兒童車呢？可以先跟我說一下大概的需求或身高，我來幫您推薦！」"
    elif any(kw in text_lower for kw in ["10萬", "預算", "車款", "規格", "差別"]):
        strategy_1 = "• 客戶主動提及具體預算或規格比較。"
        strategy_2 = "• 提供對應預算級距的熱門配置建議。"
        strategy_3 = "• 建議直接回覆：「這預算可以看性價比極高的車款，這週末有空直接來店裡看實車最快！」"
    else:
        strategy_1 = "• 客戶進行一般性詢問或補充對話。"
        strategy_2 = "• 保持親切口語互動，持續收集需求。"
        strategy_3 = "• 建議直接回覆：「了解！這部分沒問題，店長晚點幫你詳細說明～」"

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
    
    # 1. 針對預約、維修調整加入「您什麼時候方便」的自然反問
    if any(kw in text_lower for kw in ["調整", "調校", "器材", "異音", "維修", "預約", "週末", "店", "今天"]):
        reply_text = "有的！我們店裡有專門的校正器材可以處理這塊。那您看今天或是這週末大約什麼時候方便把車帶過來呢？"
    elif any(kw in text_lower for kw in ["女生", "女性", "女孩", "女友", "老婆"]):
        reply_text = "女生騎的話，主要會看身高還有平常是想輕鬆休閒騎、還是運動流汗居多！可以先透露一下身高嗎？店裡有幾款車身好看又好騎的車款很適合喔！"
    elif any(kw in text_lower for kw in ["價格", "多少錢", "大約價", "費用", "怎麼賣"]):
        reply_text = "這主要看您的預算大概抓多少喔！從幾千元的代步休閒車到十幾萬的高階車款我們都有，可以先跟我說一下您的預算範圍嗎？"
    elif any(kw in text_lower for kw in ["爸", "長輩", "老人家", "父親", "公公", "媽", "弟", "哥", "妹", "姊", "小朋友", "小孩", "兒童", "推薦", "想買"]):
        reply_text = "那您是想要公路車、登山車還是兒童車呢？可以先跟我說一下對方的大約身高或需求，我來幫您推薦最適合的款式！"
    elif any(kw in text_lower for kw in ["10萬", "預算", "車款", "規格", "差別"]):
        reply_text = "這個預算能選到配備很不錯的車款耶！店長晚點忙完會親自幫你挑幾台最划算的出來，或者你這週末有空直接來店裡看實車最快！"
    else:
        reply_text = "嗨囉！訊息都有收到囉～ 我先跟店長說一聲，他忙完就會馬上回覆你！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
    # 2. 智慧過濾洗版訊息，確保高意願對話確實推播給老闆
    ignore_words = ["嗨", "哈囉", "安安", "在嗎", "好", "嗯", "喔", "謝謝", "ok", "了解"]
    is_trivial = (len(user_message.strip()) <= 3 and user_message.strip() in ignore_words)
    
    has_digit = any(char.isdigit() for char in user_message)
    
    valuable_keywords = [
        "女生", "女性", "女孩", "價格", "多少錢", "大約價", "費用", "怎麼賣",
        "爸", "長輩", "老人家", "父親", "公公", "媽", "弟", "哥", "妹", "姊", 
        "小朋友", "小孩", "兒童", "推薦", "想買", "調整", "調校", "器材", "異音", "維修", 
        "預約", "10萬", "預算", "車款", "規格", "差別", "週末", "店", "公路車", "登山車", "今天"
    ]
    
    has_valuable_intent = has_digit or any(kw in text_lower for kw in valuable_keywords)
    
    if not is_trivial and has_valuable_intent:
        s1, s2, s3 = generate_three_strategies(user_message)
        
        telegram_msg = (
            f"🔴 *【客戶預約與對話進度通知】*\n"
            f"💬 *客戶最新回覆*：「{user_message}」\n\n"
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
