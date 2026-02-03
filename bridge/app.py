"""
LINE ↔ OpenClaw 橋接服務
接收 LINE Webhook，轉發至 OpenClaw OpenResponses API，並將回覆傳回 LINE。
可部署於 Render。（若改為「同一台跑 OpenClaw + LINE」，請用專案根目錄的 README 部署 OpenClaw 並啟用 LINE 頻道。）
"""
import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
OPENCLAW_GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "").rstrip("/")
OPENCLAW_GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
OPENCLAW_AGENT_ID = os.environ.get("OPENCLAW_AGENT_ID", "main")
OPENCLAW_TIMEOUT = int(os.environ.get("OPENCLAW_TIMEOUT", "60"))

# LINE 單則訊息字數上限（官方 5000，保守用 4000）
LINE_MESSAGE_MAX_LEN = 4000

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def call_openclaw(user_id: str, user_message: str) -> str:
    """
    呼叫 OpenClaw OpenResponses API (POST /v1/responses)。
    user_id 用於 session 對應，同一 LINE 用戶會維持同一 session。
    """
    if not OPENCLAW_GATEWAY_URL or not OPENCLAW_GATEWAY_TOKEN:
        return "尚未設定 OpenClaw Gateway 位址或 Token，請在 Render 環境變數設定 OPENCLAW_GATEWAY_URL 與 OPENCLAW_GATEWAY_TOKEN。"

    url = f"{OPENCLAW_GATEWAY_URL}/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENCLAW_GATEWAY_TOKEN}",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": OPENCLAW_AGENT_ID,
    }
    # OpenResponses 格式：input 可為字串或 items 陣列；user 用於穩定 session
    payload = {
        "model": f"openclaw:{OPENCLAW_AGENT_ID}",
        "input": user_message,
        "user": f"line:{user_id}",
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=OPENCLAW_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        logger.exception("OpenClaw request timeout")
        return "OpenClaw 回應逾時，請稍後再試。"
    except requests.exceptions.RequestException as e:
        logger.exception("OpenClaw request error: %s", e)
        if hasattr(e, "response") and e.response is not None:
            try:
                err_body = e.response.json()
                msg = err_body.get("error", {}).get("message", e.response.text)
            except Exception:
                msg = e.response.text or str(e)
        else:
            msg = str(e)
        return f"無法取得 OpenClaw 回覆：{msg[:200]}"

    # OpenResponses 回傳格式：output 陣列中有 output_item，內有 content 等
    text_parts = []
    for item in data.get("output", []):
        if isinstance(item, str):
            text_parts.append(item)
            continue
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    text_parts.append(part.get("text", ""))
        if item.get("type") == "output_text":
            text_parts.append(item.get("text", ""))

    result = "".join(text_parts).strip()
    if not result:
        # 相容其他可能格式
        result = (
            data.get("output", [{}])[0].get("text", "")
            if isinstance(data.get("output"), list) and data.get("output")
            else ""
        )
        if isinstance(result, dict):
            result = result.get("text", "")
    if not (result and str(result).strip()):
        result = "（OpenClaw 未回傳文字內容）"
    return str(result).strip()


def chunk_message(text: str, max_len: int = LINE_MESSAGE_MAX_LEN) -> list[str]:
    """將長文依上限切分成多則訊息。"""
    if len(text) <= max_len:
        return [text] if text else []
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # 盡量在換行或句號處切
        cut = text[: max_len + 1]
        last_break = max(
            cut.rfind("\n"),
            cut.rfind("。"),
            cut.rfind("."),
            cut.rfind(" "),
            -1,
        )
        if last_break > max_len // 2:
            chunks.append(text[: last_break + 1])
            text = text[last_break + 1 :].lstrip()
        else:
            chunks.append(text[:max_len])
            text = text[max_len:]
    return chunks


@app.route("/")
def index():
    return "LINE ↔ OpenClaw 橋接服務運行中。Webhook: POST /callback"


@app.route("/health")
def health():
    """Render 健康檢查用。"""
    return "", 200


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK", 200


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event: MessageEvent):
    user_id = event.source.user_id
    text = (event.message.text or "").strip()
    if not text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入文字訊息。"),
        )
        return

    reply = call_openclaw(user_id, text)
    chunks = [c for c in chunk_message(reply) if c]
    if not chunks:
        chunks = ["（無回覆內容）"]
    # LINE 規定同一 reply_token 只能回覆一次，可一次回多則訊息
    line_bot_api.reply_message(
        event.reply_token,
        [TextSendMessage(text=c) for c in chunks],
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
