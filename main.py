import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests
import google.generativeai as genai

app = Flask(__name__)

# LINE 官方帳號設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Telegram 機器人設定
TELEGRAM_BOT_TOKEN = "8345028959:AAGp7LAqW4AEJUH1VHg8r7N0yWNjnDIMdTM"
TELEGRAM_CHAT_ID = "7468110837"

# Google Gemini API 設定（請換上你的 Gemini API Key）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "你的GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

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

def generate_ai_reply_and_strategy(user_message):
    """
    利用 Gemini 動態扮演親切專業的車店老闆，
    自動判斷客戶意圖，產出自然的對話回覆與給老闆的 Telegram 策略報告。
    """
    prompt = f"""
    你是一家專業自行車店的老闆兼小幫手。現在有一位客戶在 LINE 傳送了以下訊息：「{user_message}」
    
    請幫我用親切、口語、像真實台灣在地車店老闆的口吻（不要死板罐頭，要懂得漸進式反問、推動預約或釐清需求），產出以下兩個部分：
    
    【回覆客戶】（直接給 LINE 要回覆的文字，保持自然、熱情、口語）
    【老闆策略】（給 Telegram看的結構：1. 需求解析 2. 引導方向 3. 建議講法）
    
    格式請嚴格用以下格式回傳（不要有多餘的廢話）：
    REPLY: [你要回覆給客戶的內容]
    STRATEGY_S1: [需求解析]
    STRATEGY_S2: [引導方向]
    STRATEGY_S3: [建議講法]
    """
    
    try:
        # 使用 Gemini 模型生成智慧對話
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text = response.text
        
        # 解析 Gemini 回傳的格式
        lines = text.split('\n')
        reply = "嗨囉！訊息都有收到囉～這就幫您確認！"
        s1 = "• 客戶進行一般性詢問。"
        s2 = "• 保持親切口語互動。"
        s3 = "• 建議直接回覆：「了解！有任何問題隨時跟我說～」"
        
        for line in lines:
            if line.startswith("REPLY:"):
                reply = line.replace("REPLY:", "").strip()
            elif line.startswith("STRATEGY_S1:"):
                s1 = line.replace("STRATEGY_S1:", "").strip()
            elif line.startswith("STRATEGY_S2:"):
                s2 = line.replace("STRATEGY_S2:", "").strip()
            elif line.startswith("STRATEGY_S3:"):
                s3 = line.replace("STRATEGY_S3:", "").strip()
                
        return reply, s1, s2, s3
    except Exception as e:
        print(f"Gemini 生成失敗: {e}")
        # 若 API 發生例外時的備用口語回覆
        return "有的！這就幫您確認，看這週末或平日哪時候比較方便過來呢？", "• 客戶進行詢問，AI 生成備用邏輯。", "• 引導至預約或實體賞車。", "• 建議詢問方便的時間。"

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
    
    # 1. 透過 Gemini 動態生成最有人性化、最道地的老闆回覆
    reply_text, s1, s2, s3 = generate_ai_reply_and_strategy(user_message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
    # 2. 智慧過濾過短的洗版無意義招呼語（如單純傳「嗨」、「好」）
    ignore_words = ["嗨", "哈囉", "安安", "在嗎", "好", "嗯", "喔", "謝謝", "ok", "了解"]
    is_trivial = (len(user_message.strip()) <= 3 and user_message.strip() in ignore_words)
    
    # 只要不是純無意義洗版，就透過 Telegram 把 Gemini 整理好的策略報告推播給老闆
    if not is_trivial:
        telegram_msg = (
            f"🔴 *【客戶對話動態通知】*\n"
            f"💬 *客戶原話*：「{user_message}」\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 *【老闆專屬：Gemini 智慧應對策略】*\n\n"
            f"1️⃣ *【需求解析】*\n{s1}\n\n"
            f"2️⃣ *【引導方向】*\n{s2}\n\n"
            f"3️⃣ *【建議回覆講法】*\n{s3}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"👉 請前往 LINE 官方帳號查看詳情！"
        )
        
        send_telegram_notification(telegram_msg)

if __name__ == "__main__":
    app.run(port=5000)
