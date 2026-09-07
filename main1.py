import os
import requests

def get_post_from_google_sheets():
    api_url = os.environ.get("GOOGLE_SCRIPT_URL")
    response = requests.get(api_url)
    data = response.json()
    return data.get("content")

def publish_content(content):
    webhook_url = os.environ.get("TARGET_WEBHOOK_URL")
    payload = {"content": content}
    
    response = requests.post(webhook_url, json=payload)
    if response.status_code in [200, 204]:
        print("發文成功！")
    else:
        raise Exception(f"發文失敗，狀態碼：{response.status_code}")

if __name__ == "__main__":
    post_content = get_post_from_google_sheets()
    if post_content:
        print(f"準備發布內容：{post_content}")
        publish_content(post_content)
    else:
        print("目前沒有待發布的文章（狀態皆為 sent）。")
