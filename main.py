import os
import sys
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = Flask(__name__)

# 強制將 print 印出到 stdout，確保 Render Logs 隨時看得到
sys.stdout.reconfigure(line_buffering=True)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

print(f"=== [系統啟動] 金鑰狀態檢查 ===")
print(f"LINE_CHANNEL_ACCESS_TOKEN: {bool(LINE_CHANNEL_ACCESS_TOKEN)}")
print(f"LINE_CHANNEL_SECRET: {bool(LINE_CHANNEL_SECRET)}")
print(f"OPENAI_API_KEY: {bool(OPENAI_API_KEY)}")
print(f"================================")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/", methods=['GET'])
def home():
    return "LINE Bot Server is Running!", 200

@app.route("/callback", methods=['POST'])
def callback():
    # 抓取 LINE 的 Signature Header
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    print(f"\n[Webhook 觸發] 收到來自 LINE 的請求！")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("[錯誤] LINE 簽名驗證失敗！請檢查 LINE_CHANNEL_SECRET 是否貼錯。")
        abort(400)
    except Exception as e:
        print(f"[異常] 處理 Webhook 時發生錯誤: {e}")
        return 'OK', 200

    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    print(f"[收到用戶訊息]: {user_text}")

    # 1. 呼叫 OpenAI API
    try:
        print("[OpenAI] 正在生成回答...")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個樂於助人且專業的 AI 助理。"},
                {"role": "user", "content": user_text}
            ]
        )
        ai_reply = completion.choices[0].message.content.strip()
        print(f"[OpenAI 回應成功]: {ai_reply}")
    except Exception as e:
        print(f"[OpenAI 發生錯誤]: {e}")
        ai_reply = "抱歉，目前 AI 服務處理失敗，請稍後再試。"

    # 2. 透過 LINE API 回覆訊息
    try:
        print("[LINE] 正在將訊息推回 LINE...")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
        print("[LINE] 訊息發送成功！")
    except Exception as e:
        print(f"[LINE 發送失敗]: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
