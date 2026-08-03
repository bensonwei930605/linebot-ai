import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = Flask(__name__)

# 從環境變數讀取密鑰與金鑰
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# 印出檢查金鑰是否有成功載入
print(f"--- 啟動檢查 ---")
print(f"LINE Access Token 存在: {bool(LINE_CHANNEL_ACCESS_TOKEN)}")
print(f"LINE Secret 存在: {bool(LINE_CHANNEL_SECRET)}")
print(f"OpenAI Key 存在: {bool(OPENAI_API_KEY)}")
print(f"----------------")

# 初始化 LINE API 與 OpenAI Client
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/", methods=['GET'])
def home():
    return "LINE Bot with GPT is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("[ERROR] LINE 簽名驗證失敗 (InvalidSignatureError)")
        abort(400)
    except Exception as e:
        print(f"[NOTE] Callback 邊緣異常: {e}")
        return 'OK', 200

    return 'OK', 200

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    print(f"[收到訊息] User: {user_message}")

    try:
        print("[OpenAI] 正在傳送請求給 OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個親切且專業的 AI 助理。"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response.choices[0].message.content.strip()
        print(f"[OpenAI 成功回應] {reply_text}")

    except Exception as e:
        print(f"[OpenAI 發生錯誤] {e}")
        reply_text = "抱歉，目前 AI 服務暫時無法回應，請稍後再試。"

    try:
        print("[LINE] 正在發送回覆給使用者...")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        print("[LINE] 回覆發送成功！")
    except Exception as e:
        print(f"[LINE 發送錯誤] {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
