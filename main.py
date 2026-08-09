import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
import requests

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

TELEGRAM_BOT_TOKEN = "8345028959:AAGp7LAqW4AEJUH1VHg8r7N0yWNjnDIMdTM"
TELEGRAM_CHAT_ID = "7468110837"

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram 推播失敗: {e}")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    # 1. 專業改裝/升級關鍵字（技術問題 ➡️ 通知老闆）
    upgrade_keywords = [
        "車架", "變速器", "變數器", "大盤", "功率大盤", "功率計", "碟盤", "輪框", "輪組", 
        "改裝", "升級", "維修", "保養", "檢修", "組車"
    ]
    is_upgrade_query = any(kw in user_message for kw in upgrade_keywords)
    
    # 2. 商品/配件關鍵字
    items = ["公路車", "登山車", "車衣", "安全帽", "帽子", "水壺", "眼鏡", "車用眼鏡", "卡鞋", "輪框", "大盤", "變速器"]
    has_mai = "賣" in user_message
    has_item = any(item in user_message for item in items)
    
    # 3. 預算/出價關鍵字（包含「預算」、「萬」、「元」、或直接包含數字，代表客戶要買東西了！）
    has_budget_word = any(kw in user_message for kw in ["預算", "萬", "元", "價格", "多少"])
    is_budget_amount = has_budget_word or user_message.isdigit()

    # 4. 綜合判定：只要有問商品、有講賣、或是講預算/金額，都視為買東西/詢價
    is_selling_inquiry = has_mai or (has_item and has_budget_word) or is_budget_amount

    # 5. 時間/預約判斷
    is_time_query = any(kw in user_message for kw in ["點", "明天", "今天", "週末", "平日", "上午", "下午", "晚上"]) or user_message.isdigit()

    if is_upgrade_query:
        # 🔴 技術改裝：通知老闆
        reply_text = "關於改裝與專業零組件的問題，我們由老闆親自為您說明，請您稍等一下喔！"
        telegram_msg = (
            f"🔴 *【客戶詢問改裝/零組件】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 屬於技術/改裝問題，請前往 LINE 手動接手！"
        )
        send_telegram_notification(telegram_msg)
        
    elif is_selling_inquiry:
        # 🟢 詢問商品或回報預算：AI 友善回覆，並通知老闆推薦高 CP 值商品
        reply_text = "收到您的預算與需求！您可以直接來店裡看看實品，或是由我幫您推薦幾款店內 CP 值很不錯的選擇唷！"
        telegram_msg = (
            f"🟡 *【客戶已給出預算/詢問商品】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"💡 *老闆注意*：客戶正在洽談預算與購買，**推薦店內 CP 值高一點的**，請前往 LINE 接手！"
        )
        send_telegram_notification(telegram_msg)
        
    elif is_time_query:
        # 🟢 預約時間
        reply_text = f"收到！您提到「{user_message}」，我已經幫您把時間記錄下來囉，請稍等一下由老闆跟您確認！"
        telegram_msg = (
            f"🟢 *【客戶已敲定時間】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 請前往 LINE 官方帳號手動接手！"
        )
        send_telegram_notification(telegram_msg)
        
    else:
        # ⚠️ 真正的無關閒聊或亂碼
        reply_text = "真不好意思，您的問題比較特別，我已經請老闆來協助您，請稍等一下喔！"
        telegram_msg = (
            f"⚠️ *【機器人無法辨識】*\n"
            f"💬 *客戶原話*：「{user_message}」\n"
            f"👉 請前往 LINE 看看狀況！"
        )
        send_telegram_notification(telegram_msg)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)
