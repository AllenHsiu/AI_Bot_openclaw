# AI Bot — 同一 Repo 兩個服務（LINE 橋接 + OpenClaw）

本 repo 包含 **兩個可部署到 Render 的服務**，用同一個 GitHub repo、同一份 `render.yaml` Blueprint 管理：

| 服務 | 目錄 | 說明 |
|------|------|------|
| **line-bridge** | `bridge/` | Python Flask：接收 LINE Webhook，轉發到 OpenClaw OpenResponses API，回傳 LINE |
| **openclaw** | `openclaw/` | OpenClaw Gateway（[openclaw/openclaw](https://github.com/openclaw/openclaw) 以 **git submodule** 引入） |

---

## 一、Repo 結構

```
AI_Bot (本 repo)
├── bridge/           # LINE 橋接（Python）
│   ├── app.py
│   ├── requirements.txt
│   └── ...
├── openclaw/          # OpenClaw Gateway（git submodule → openclaw/openclaw）
├── render.yaml        # Render Blueprint：兩個服務
├── requirements.txt  # 根目錄，給 Render build 用（bridge）
└── README.md
```

- **bridge**：本專案程式碼。
- **openclaw**：由 `git submodule add https://github.com/openclaw/openclaw.git openclaw` 加入，指向 [openclaw/openclaw](https://github.com/openclaw/openclaw)。

---

## 二、用 Render Blueprint 一次部署兩個服務

1. **連到 Render**  
   到 [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**。

2. **連接此 repo**  
   選擇放有此專案的 GitHub repo（例如 `AllenHsiu/AI_Bot_openclaw`）。

3. **建立 Blueprint**  
   Render 會讀取根目錄的 `render.yaml`，建立兩個服務：
   - **line-bridge**（Python，Root Directory: `bridge`）
   - **openclaw**（Docker，Root Directory: `openclaw`）

4. **OpenClaw 服務務必啟用 Submodules**  
   因為 OpenClaw 程式在 `openclaw/` submodule 裡：
   - 進入 **openclaw** 服務 → **Settings** → **Build & Deploy**
   - 找到 **Submodules**（或 Git 相關選項），設為 **Clone submodules** 或等同選項，讓 Render 執行 `git submodule update --init --recursive`，否則 `openclaw/` 會是空的、Docker build 會失敗。

5. **填寫環境變數**  
   Blueprint 建立時會提示：
   - **line-bridge**：`LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET`、`OPENCLAW_GATEWAY_URL`（OpenClaw 服務網址）、`OPENCLAW_GATEWAY_TOKEN`（與 OpenClaw 的 token 一致）。
   - **openclaw**：`SETUP_PASSWORD` 等（見 OpenClaw 文件）。

6. 部署完成後：
   - **LINE Webhook URL** 設為：`https://<line-bridge 服務名>.onrender.com/callback`（或你 bridge 實際的 webhook path）。
   - **OPENCLAW_GATEWAY_URL** 設為：`https://<openclaw 服務名>.onrender.com`。

---

## 三、本機開發 / 更新 submodule

第一次 clone 本 repo 後，要拉取 submodule：

```bash
git clone --recurse-submodules https://github.com/你的帳號/AI_Bot_openclaw.git
# 若已 clone 過，補拉 submodule：
git submodule update --init --recursive
```

更新 openclaw 到上游最新：

```bash
cd openclaw
git pull origin main
cd ..
git add openclaw
git commit -m "chore: update openclaw submodule"
git push
```

---

## 四、只部署 LINE 橋接（不部署 OpenClaw）

若 OpenClaw 已在別處運行（例如另一台 Render 或自架）：

- 只建立 **line-bridge** 服務：在 Render 手動建一個 **Web Service**，Repo 選本 repo，**Root Directory** 填 `bridge`。
- Build Command：`pip install -r requirements.txt`
- Start Command：`gunicorn -b 0.0.0.0:$PORT app:app`
- 環境變數：`LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET`、`OPENCLAW_GATEWAY_URL`、`OPENCLAW_GATEWAY_TOKEN`。

詳見 `bridge/README.md`。

---

## 五、參考連結

- [OpenClaw 官方](https://github.com/openclaw/openclaw) · [文件](https://docs.openclaw.ai/)
- [Render Blueprint](https://docs.render.com/blueprint-spec) · [Monorepo / rootDir](https://docs.render.com/monorepo-support)
- [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)
