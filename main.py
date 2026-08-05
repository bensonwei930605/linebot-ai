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

# 從 Render 環境變數讀取老闆的 LINE User ID
BOSS_LINE_USER_ID = os.environ.get('BOSS_LINE_USER_ID', '')


@app.route("/", methods=['GET'])
def home():
    return "Wei IT & Bike Assistant Server is Running with Instant Notification!", 200


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
    
    # 輸入「我的ID」可隨時查詢老闆自己的 ID
    if user_text.strip() == "我的ID":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"老闆，您的 LINE User ID 是：\n{sender_id}")
        )
        return

    tz = timezone(timedelta(hours=8))
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %A")

    # 智慧大腦設定：保護老闆專業，不亂推薦車款，引導交給老闆
    system_prompt = f"""
    你現在是高雄與台南地區專業單車維修與 226 鐵人三項調校店舖的老闆專屬 AI 助理。
    店內專精高階公路車維修、保養、異音排除與賽事調校。
    溝通風格：高效率、專業、俐落、不廢話。
    當前台灣時間：{current_time}

    核心任務與規則：
    1. 【車款與購車諮詢】：當客戶詢問買車推薦、預算、規格或 CP 值時，絕對不要盲目推薦。請回覆：「這部分需要由店長（老闆）親自幫您評估現貨與最適合的搭配，我已經通知老闆了，老闆稍後會親自回覆您！」
    2. 【維修與保養諮詢】：針對異音排除、226 賽前大保養等技術問題，給予簡短初步解答。
    3. 【行程與預約管理】：當客戶有明確預約維修時間時，請幫忙整理資訊，並在回覆結尾附上 Google 日曆加入連結：
       https://calendar.google.com/calendar/render?action=TEMPLATE&text=[行程標題]&dates=[開始UTC]/[結束UTC]&details=[行程說明]&location=[地點]
       * 時間格式必須使用 UTC (台灣時間減 8 小時)，格式如：20260810T060000Z/20260810T070000Z
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

    # 1. 回覆訊息給客人
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        print(f"[LINE 回覆錯誤]: {e}")

    # 2. 智慧推播：如果客人問了推薦、預算、車款或預約，立刻發送通知給老闆本人！
    if BOSS_LINE_USER_ID and any(keyword in user_text for keyword in ["推薦", "預算", "預約", "車款", "買"]):
        boss_notification = f"""🚨 【顧客諮詢通知】
有客人傳送了需要您親自出馬的訊息：
「{user_text}」

請盡快前往官方帳號聊天室查看並回覆客人！"""
        try:
            line_bot_api.push_message(
                BOSS_LINE_USER_ID,
                TextSendMessage(text=boss_notification)
            )
            print("[主動推播] 已成功發送顧客諮詢通知給老闆！")
        except Exception as e:
            print(f"[老闆推播失敗]: {e}")


# ==================== ⏰ 每日開店主動推播任務 ====================
def daily_morning_briefing():
    """每天早上開店前主動推播給老闆的晨間提醒"""
    if not BOSS_LINE_USER_ID:
        print("[推播略過] 尚未設定 BOSS_LINE_USER_ID")
        return

    tz = timezone(timedelta(hours=8))
    today_str = datetime.now(tz).strftime("%Y年%m月%d日 (%A)")

    push_message = f"""早安，老闆！ 🚴‍♂️
今天是 {today_str}。

【今日開店提醒】：
• 記得檢查店內高壓打氣機與工作台工具。
• 今日目前暫無預約客，祝營業順利，業績長紅！"""

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
