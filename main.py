import os
import sys
import urllib.parse
from datetime import datetime, timezone, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = Flask(__name__)
sys.stdout.reconfigure(line_buffering=True)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/", methods=['GET'])
def home():
    return "AI Assistant Server is Running!", 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print(f"[異常] {e}")
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    
    # 取得當前台灣時間，讓 AI 知道現在是幾號，才能正確推算「明天」、「下週」的日期
    tz = timezone(timedelta(hours=8))
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %A")

    # 大腦設定：賦予 AI 專業身份與任務規則
    system_prompt = f"""
    你現在是單車維修店老闆的專屬 AI 助理。
    店內服務涵蓋高階公路車維修、226鐵人三項賽事車輛調校與日常保養，主要服務範圍在高雄與台南地區。
    你的溝通風格：高效率、專業、直指核心、不廢話。

    【當前系統時間】：{current_time}

    你的核心任務：
    1. 【單車需求諮詢】：提供專業的單車維修、保養、異音排除、改裝建議與技術解答。
    2. 【行程與預約管理】：當老闆指示要預約客戶、安排維修時間或處理業務行程時，你必須整理好資訊，並提供「Google 日曆加入連結」。

    【產生 Google 日曆連結的嚴格規則】
    請依照以下格式，直接在回覆中提供讓老闆一鍵點擊的網址。請務必將括號內的參數替換並進行 URL 編碼 (URL Encoding)。
    網址格式： https://calendar.google.com/calendar/render?action=TEMPLATE&text=[行程標題]&dates=[開始時間]/[結束時間]&details=[行程說明]&location=[地點]

    * 關於時間格式：必須使用 YYYYMMDDTHHMMSSZ (這是 UTC 時間，請將台灣時間減去 8 小時)。
      例如：預約台灣時間 2026年8月10日下午2點到3點，應轉換為 UTC 的 20260810T060000Z/20260810T070000Z。
    * 行程說明 (details) 中可以列出該次預約需要準備的零件或維修重點。

    請在回覆解答完畢後，若有行程需求，附上該超連結即可。
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
        )
        ai_reply = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI 錯誤]: {e}")
        ai_reply = "抱歉老闆，系統暫時出現連線狀況，請稍後再試。"

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        print(f"[LINE 錯誤]: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
