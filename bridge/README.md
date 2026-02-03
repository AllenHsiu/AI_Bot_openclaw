# LINE ↔ OpenClaw 橋接（兩台服務）

此為「LINE 與 OpenClaw 分開兩台服務」時的 Python 橋接程式：接收 LINE Webhook、呼叫 OpenClaw API、回傳 LINE。

**若你要「同一台跑 OpenClaw + LINE」**，請改看專案根目錄的 README，直接部署 OpenClaw 並在該實例上啟用 LINE 頻道即可。

部署此橋接：在 Render 建立 Web Service，根目錄選 `bridge/`，Build: `pip install -r requirements.txt`，Start: `gunicorn -b 0.0.0.0:$PORT app:app`，並設定 `LINE_CHANNEL_*` 與 `OPENCLAW_GATEWAY_*` 環境變數。
