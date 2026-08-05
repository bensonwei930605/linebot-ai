import os
import sys
from datetime import datetime, timezone, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
sys.stdout.reconfigure(line_buffering=True)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

# ==================== 🛠️ 請在這裡填入老闆（你）的 LINE User ID ====================
# 如果不知道 ID，可以先看下方的說明步驟取得
BOSS_LINE_USER_ID = os.environ.get('BOSS_LINE_USER_ID', '你的LINE_USER_ID填在這裡')


@app.route("/", methods=['GET'])
def home():
    return "AI Assistant Server is Running with Scheduler!", 200


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
    sender_id = event.source.user_id
    
    # 貼心小功能：如果老闆傳「我的ID」，機器人直接把 ID 回傳給你，方便設定
    if user_text.strip() == "我的ID":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"老闆，您的 LINE User ID 是：\n{sender_id}")
        )
        return

    tz = timezone(timedelta(hours=8))
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %A")

    system_prompt = f"""
    你現在是一位專業的自行車店技師與老闆專屬 AI 助理。
    店內服務涵蓋高階公路車維修、226鐵人三項賽事車輛調校與日常保養，主要服務範圍在高雄與台南地區。
    溝通風格：高效率、專業、直指核心、不廢話。

    當前台灣時間：{current_time}

    核心任務：
    1. 【具體車款推薦】：當客戶詢問購車預算時，絕對不要只給抽象品牌，必須直接列出 2-3 款符合預算的「具體車款型號」（包含品牌與型號），並說明理由。若是 226 三鐵需求，優先推薦空力車或三鐵車。
    2. 【單車需求諮詢】：提供專業維修、保養、異音排除等解答。
    3. 【行程與預約管理】：當預約時，必須提供 Google 日曆加入連結：
       https://calendar.google.com/calendar/render?action=TEMPLATE&text=[標題]&dates=[開始UTC]/[結束UTC]&details=[說明]&location=[地點]
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
        ai_reply = "抱歉老闆，系統暫時連線異常。"

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        print(f"[LINE 錯誤]: {e}")


# ==================== ⏰ 每日開店主動推播任務 ====================
def daily_morning_briefing():
    """每天早上開店前主動推播給老闆的晨間提醒"""
    if BOSS_LINE_USER_ID == '你的LINE_USER_ID填在這裡':
        print("[推播略過] 尚未設定老闆的 BOSS_LINE_USER_ID")
        return

    tz = timezone(timedelta(hours=8))
    today_str = datetime.now(tz).strftime("%Y年%m月%d日 (%A)")

    # 這裡未來可以對接你的資料庫或 Google 日曆 API 撈取當日行程
    # 目前先以範本呈現，讓 AI 幫忙生成一段激勵與提醒
    push_message = f"""早安，老闆！ 🚴‍♂️
今天是 {today_str}。

【今日開店提醒】：
• 記得檢查店內高壓打氣機與工作台工具。
• 今日目前暫無預約客，適合排定庫存盤點或車架保養進度。

祝今天營業順利，業績長紅！如果有任何客人的疑難雜症隨時賴我。"""

    try:
        line_bot_api.push_message(
            BOSS_LINE_USER_ID,
            TextSendMessage(text=push_message)
        )
        print("[主動推播] 成功發送早安晨報給老闆！")
    except Exception as e:
        print(f"[推播失敗]: {e}")


# 設定背景排程器：每天早上 08:30 自動執行一次
scheduler = BackgroundScheduler()
scheduler.add_job(daily_morning_briefing, 'cron', hour=8, minute=30, timezone='Asia/Taipei')
scheduler.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
