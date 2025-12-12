from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI
#2
# Flaskサーバー
app = Flask(__name__)

# ---- 環境変数 ----
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---- LINE / OpenAI 初期化 ----
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)


# ---- Webhook受信（LINE → Render）----
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')

    if signature is None:
        print("Signature missing")
        abort(400)

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Handler error:", e)
        abort(400)

    return "OK"


# ---- メッセージ受信時の処理 ----
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    try:
        # ChatGPT による返信生成（← 最新仕様）
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "丁寧にわかりやすく答えるAIです。"},
                {"role": "user", "content": user_text}
            ]
        )

        # ★★ 最新 OpenAI SDK の正しい取り出し方 ★★
        reply_text = response.choices[0].message.content

    except Exception as e:
        print("OpenAI error:", e)
        reply_text = "OpenAI APIでエラーが発生しました。"

    try:
        # LINE に返信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print("LINE reply error:", e)


# ---- Render 起動 ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
