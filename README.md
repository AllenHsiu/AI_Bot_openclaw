# 同一台 Render 跑 OpenClaw + LINE

在 **同一台 Render 服務** 上運行 **OpenClaw**，並啟用 **LINE** 頻道：LINE 訊息由 OpenClaw 內建 LINE 外掛接收，AI 回覆直接從同一 Gateway 回傳到 LINE。

架構：

```
LINE 用戶 → LINE 平台 → 你的 Render 服務 (OpenClaw) /line/webhook → OpenClaw Agent → 回覆回 LINE
```

---

## 一、一鍵部署 OpenClaw 到 Render

1. 點擊下方連結，用 **OpenClaw 官方 repo** 在 Render 建立服務（會帶入 Docker + render.yaml）：
   - **https://render.com/deploy?repo=https://github.com/openclaw/openclaw**
2. 登入或註冊 Render，選擇要用的帳號。
3. 部署時會要求設定：
   - **SETUP_PASSWORD**：自訂一組密碼（之後進設定畫面會用到）。
4. 其他如 `OPENCLAW_GATEWAY_TOKEN` 等會自動產生；需要 **持久化磁碟** 請選 Starter 以上方案。
5. 等待建置與部署完成，記下服務網址，例如：`https://你的服務名稱.onrender.com`。

---

## 二、完成 OpenClaw 設定（Model、LINE）

1. 開啟 **設定精靈**：  
   `https://你的服務名稱.onrender.com/setup`  
   輸入剛才設定的 **SETUP_PASSWORD**。
2. 依精靈完成：
   - 選擇 **Model 供應商**（如 OpenAI、Anthropic 等）並貼上 API Key。
   - 若要加 **LINE**：
     - 在設定裡安裝 LINE 外掛（若精靈有「Channels / Plugins」步驟可選 LINE，或之後用 config 啟用）。
     - 或部署完成後用 **Control UI** 或 **config** 啟用 LINE（見下方）。

---

## 三、啟用 LINE 頻道（同一台 OpenClaw）

OpenClaw 的 LINE 是 **外掛頻道**，和 OpenClaw 跑在同一個服務上。

### 1. 安裝 LINE 外掛

在部署好的 OpenClaw 環境中（若 Render 有 Shell 可用）：

```bash
openclaw plugins install @openclaw/line
```

若你用的是官方 Render 的 Docker 部署，外掛可能已內建或可透過設定匯入；沒有 CLI 時可改由 **設定匯入** 或 **Control UI** 啟用 LINE。

### 2. 取得 LINE 憑證

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)。
2. 建立 **Messaging API** Channel，取得：
   - **Channel access token**
   - **Channel secret**

### 3. 在 OpenClaw 設定 LINE

用 **環境變數**（在 Render Dashboard → 你的 OpenClaw 服務 → Environment）加入：

| 變數 | 說明 |
|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel 的 Channel access token |
| `LINE_CHANNEL_SECRET` | LINE Channel 的 Channel secret |

或寫入 OpenClaw 的 config（例如 `openclaw.json` / 設定匯出檔）：

```json
{
  "channels": {
    "line": {
      "enabled": true,
      "channelAccessToken": "你的 LINE_CHANNEL_ACCESS_TOKEN",
      "channelSecret": "你的 LINE_CHANNEL_SECRET",
      "dmPolicy": "pairing"
    }
  }
}
```

- **dmPolicy**：`pairing` = 陌生人先拿配對碼，你核准後才能對話；要完全開放可設 `open`（需自行承擔風險）。

### 4. 設定 LINE Webhook URL

在 LINE Developers Console → 你的 Messaging API Channel：

1. 開啟 **Use webhook**。
2. **Webhook URL** 設為（同一台 OpenClaw 的網址）：
   ```text
   https://你的服務名稱.onrender.com/line/webhook
   ```
3. 儲存後 LINE 會對該 URL 做驗證；確保服務已啟動且 `/line/webhook` 可被 LINE 連到。

---

## 四、配對與權限（dmPolicy: pairing 時）

若使用 `dmPolicy: "pairing"`：

1. 用戶第一次傳訊息給 LINE 機器人時，會收到一組 **配對碼**。
2. 你在有 OpenClaw 的環境執行：
   ```bash
   openclaw pairing list line
   openclaw pairing approve line <配對碼>
   ```
3. 核准後該用戶即可與 OpenClaw 對話。

（若 Render 沒有 Shell，可改用本機安裝 OpenClaw CLI 並指向同一 Gateway，或暫時設 `dmPolicy: "open"` 測試。）

---

## 五、參考：環境變數一覽（同一台 OpenClaw + LINE）

在 Render 的 OpenClaw 服務裡，可設定例如：

| 變數 | 必填 | 說明 |
|------|------|------|
| `SETUP_PASSWORD` | ✅ | 設定頁密碼 |
| `OPENCLAW_GATEWAY_TOKEN` | 自動 | Render Blueprint 可自動產生 |
| `OPENCLAW_STATE_DIR` | - | 預設 `/data/.openclaw` |
| `OPENCLAW_WORKSPACE_DIR` | - | 預設 `/data/workspace` |
| `LINE_CHANNEL_ACCESS_TOKEN` | 要 LINE 時 | LINE Channel access token |
| `LINE_CHANNEL_SECRET` | 要 LINE 時 | LINE Channel secret |

Model 的 API Key 通常在 setup 精靈或 config 裡設定，不一定用環境變數。

---

## 六、Control UI 與健康檢查

- **Control UI / 設定**：`https://你的服務名稱.onrender.com/openclaw`（依官方文件路徑為準）。
- **健康檢查**：`https://你的服務名稱.onrender.com/health`（Render 可用作 Health check path）。

---

## 若改為「兩台服務」（LINE 與 OpenClaw 分開）

若你希望 **LINE 在一台、OpenClaw 在另一台**（例如 OpenClaw 自架、LINE 用獨立 Webhook 服務），可使用專案裡的 **bridge** 程式：

- 見 **`bridge/`** 目錄：Python 橋接，接收 LINE Webhook、呼叫 OpenClaw OpenResponses API、回傳 LINE。
- 部署方式與環境變數見 `bridge/README.md`。

---

## 參考連結

- [OpenClaw 官方文件](https://docs.clawd.bot/)
- [OpenClaw 部署 Render](https://docs.clawd.bot/render)
- [OpenClaw LINE 頻道](https://docs.clawd.bot/channels/line)
- [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)
