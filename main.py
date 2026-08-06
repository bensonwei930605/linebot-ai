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

# Google Gemini API 設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "你的GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 記錄每個 LINE 使用者對話紀錄
user_sessions = {}

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

def generate_ai_reply_and_strategy(user_id, user_message):
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    
    user_sessions[user_id].append(f"客戶: {user_message}")
    if len(user_sessions[user_id]) > 6:
        user_sessions[user_id] = user_sessions[user_id][-6:]
        
    chat_history_str = "\n".join(user_sessions[user_id])

    prompt = f"""
    你是一家專業自行車店的老闆兼小幫手。以下是與這名客戶最近的對話紀錄：
    {chat_history_str}
    
    【核心原則】
    1. **如果客戶已經在訊息中明確提到車種（例如公路車）與預算（例如 9萬），絕對不要再問「是要公路車還是登山車」這種白癡問題！**
    2. 要針對客戶當下提供的預算與車種給予熱情、專業的對應（例如：「9萬預算來看公路車選擇很豐富耶！鋁合金高階或碳纖維入門都有，請問身高大約是多少呢？這樣比較好幫你抓車架尺寸！」）。
    3. 語氣必須親切、口語、像真實台灣在地車店老闆。
    4. 懂得用漸進式反問來推進對話（如詢問身高、騎乘習慣或方便看車的時間），但千萬不要重複詢問客戶已經給過的答案。
    
    請嚴格依照以下格式回傳，不要有多餘的解釋或 Markdown 程式碼外框：
    REPLY: [你要回覆給客戶的口語對話內容]
    STRATEGY_S1: [需求解析]
    STRATEGY_S2: [引導方向]
    STRATEGY_S3: [建議講法]
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        reply = ""
        s1 = "• 客戶進行一般性詢問。"
        s2 = "• 保持親切口語互動。"
        s3 = "• 建議直接回覆：「了解！有任何問題隨時跟我說～」"
        
        lines = text.split('\n')
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("REPLY:"):
                reply = line_str.replace("REPLY:", "").strip()
            elif line_str.startswith("STRATEGY_S1:"):
                s1 = line_str.replace("STRATEGY_S1:", "").strip()
            elif line_str.startswith("STRATEGY_S2:"):
                s2 = line_str.replace("STRATEGY_S2:", "").strip()
            elif line_str.startswith("STRATEGY_S3:"):
                s3 = line_str.replace("STRATEGY_S3:", "").strip()
                
        if not reply:
            reply = text.replace("STRATEGY_S1", "").replace("STRATEGY_S2", "").replace("STRATEGY_S3", "").strip()
            if not reply:
                reply = "有的！這就幫您確認，看這週末或平日哪時候比較方便過來呢？"
                
        user_sessions[user_id].append(f"小幫手: {reply}")
                
        return reply, s1, s2, s3
    except Exception as e:
        print(f"Gemini 生成失敗: {e}")
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
    user_id = event.source.user_id
    
    reply_text, s1, s2, s3 = generate_ai_reply_and_strategy(user_id, user_message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
    ignore_words = ["嗨", "哈囉", "安安", "在嗎", "好", "嗯", "喔", "謝謝", "ok", "了解"]
    is_trivial = (len(user_message.strip()) <= 3 and user_message.strip() in ignore_words)
    
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
