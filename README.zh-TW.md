<div align="center">

# NotebookLM Claude Code Skill

**讓 NotebookLM 成為 Claude Code 的專案級 AI 文件管理員**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Experimental-orange.svg)]()

> 一個專案，一個筆記本。一個領域，一個專家角色。你的 AI Agent 獲得一位專屬的、基於文件來源的研究夥伴——創投分析師、軟體架構師、產品經理——而不是通用聊天機器人。

> **注意：** 此 Skill 由 [Fork](https://fork.work) 積極開發與實驗中。我們每天在自己的專案中使用它，開源是為了分享我們所學到的。可能會有粗糙的地方——歡迎貢獻和回饋。

[安裝](#安裝) • [快速開始](#快速開始) • [設定對話](#設定對話notebook-guide角色設定) • [指令](#指令)

</div>

---

## 核心理念

大多數 NotebookLM 整合只把它當成問答工具——你問，它答。

這個 Skill 採用完全不同的思路：**NotebookLM 作為專案級文件管理員。**

每個專案擁有自己的筆記本和專屬的專家角色。市場研究專案對接創投分析師、API 文件專案對接軟體架構師、產品筆記本則以產品經理的思維回答。Agent 不只是檢索資訊——它透過你設定的領域專家視角，對你的文件進行推理分析。

```
專案 A（市場研究）  → 筆記本 A → 角色：創投分析師  → 「進入門檻低，TAM 顯示...」
專案 B（API 遷移）  → 筆記本 B → 角色：架構師      → 「這會破壞合約介面...」
專案 C（用戶研究）  → 筆記本 C → 角色：產品經理    → 「RICE 評分建議...」
```

**核心功能：**
- **一專案一筆記本** — 在專案設定中綁定 notebook ID，一次設定
- **專家角色** — 設定 NotebookLM 針對不同領域的回答方式
- **無頭自動化** — 無需開啟瀏覽器即可查詢和設定筆記本
- **筆記本庫管理** — 標籤、搜尋、切換筆記本
- **一次性驗證** — 登入一次，Session 持續有效

---

## 為什麼選擇 NotebookLM？

| 方法 | 幻覺問題 | 設定成本 | Token 消耗 |
|------|----------|----------|------------|
| 直接餵文件給 Claude | 有——會用臆測填補空白 | 即時 | 極高 |
| 網路搜尋 | 高——來源不可靠 | 即時 | 中等 |
| 本地 RAG | 中等——檢索遺漏 | 數小時 | 中等 |
| **NotebookLM Skill** | **極低——基於文件來源** | **5 分鐘** | **極低** |

NotebookLM 不是檢索片段——它**理解**你的文件。它能交叉關聯 50+ 個來源、提供引用出處，並在不確定時回答「我不知道」而非瞎掰。

---

## 安裝

```bash
cd ~/.claude/skills
git clone https://github.com/yizhengzhou/notebooklm-skill notebooklm
```

完成。首次使用時，Skill 會自動建立 `.venv`、安裝依賴、設定 Chrome。

**環境需求：** Python 3.8+、本機 [Claude Code](https://github.com/anthropics/claude-code)（非網頁版——沙箱會封鎖網路存取）

---

## 快速開始

### 1. 驗證身份（僅需一次）

```
「設定 NotebookLM 驗證」
```

Chrome 視窗會自動開啟，用你的 Google 帳號登入。

### 2. 建立筆記本

前往 [notebooklm.google.com](https://notebooklm.google.com) → 建立筆記本 → 上傳文件（PDF、Google Docs、網站、YouTube 影片）。

### 3. 加入筆記本庫

```
「把這個 NotebookLM 加到我的資料庫：https://notebooklm.google.com/notebook/...」
```

### 4. 開始提問

```
「我的研究資料中關於競爭護城河分析說了什麼？」
```

Claude 會自動選擇正確的筆記本、查詢、並將答案用於當前對話脈絡中。

---

## 設定對話（Notebook Guide）— 角色設定

這是最具影響力的功能。NotebookLM 的**設定對話（Notebook Guide）**功能定義了 AI 的角色和專業領域。路徑：`對話 → 設定筆記本 → 設定對話`。沒有設定，你只會得到通用回答；有了設定，你會得到領域專家級的分析。

### 差異對比

| 未設定指南 | 設定指南後 |
|-----------|-----------|
| 「以下是你的文件中的一些市場趨勢...」 | 「根據你研究中的 TAM/SAM 分析，目標市場在工具類 App 區段有 23% 的缺口。交叉比對競爭密度數據，進入難度分數低於 30，顯示有適合 MVP 優先策略的可行窗口。」 |

### 使用方式

```bash
# 透過 CLI 設定角色
python scripts/run.py set_notebook_guide.py \
  --persona "你是一位資深創投分析師..." \
  --response-length long \
  --notebook-id my-research

# 或直接告訴 Claude
「設定對話為專精行動應用市場的創投分析師」
```

**參數說明：**
| 參數 | 必填 | 說明 |
|------|------|------|
| `--persona` | 是 | 角色/專業描述（最多 10,000 字元） |
| `--response-length` | 否 | `default`、`long` 或 `short` |
| `--notebook-url` | 否 | 目標筆記本 URL |
| `--notebook-id` | 否 | 筆記本庫中的 ID |
| `--show-browser` | 否 | 顯示瀏覽器視窗（除錯用） |

### 角色範本

**市場研究 / 創投分析師：**
```
你是一位資深創投分析師和智庫策略家。
你的知識庫包含市場研究報告、趨勢分析和競爭分析。
你使用投資框架來評估機會：TAM/SAM/SOM 市場規模估算、
競爭護城河分析、以及單位經濟模型驗證。
回答時請挑戰假設——質疑數據是否在問對的問題，
而非接受表面結論。
所有建議應以可衡量成果的 MVP 驗證為目標。
```

**技術架構審查者：**
```
你是一位擁有 15 年分散式系統經驗的首席軟體架構師。
你的知識庫包含 API 文件、系統設計規格和技術 RFC。
從可擴展性、可維護性、營運成本和團隊能力限制
的角度評估技術決策。
標記反模式，並提出具體權衡分析的替代方案。
```

**產品經理：**
```
你是一位專注於以用戶為中心設計和數據驅動決策的資深產品經理。
你的知識庫包含用戶研究報告、分析數據和產品規格。
使用 RICE 評分法（觸及率、影響力、信心、工作量）排定優先級。
所有建議必須以用戶行為數據為基礎，而非假設。
```

### 擴展策略：當一個筆記本不夠用時

NotebookLM 每個筆記本有來源數量限制。當專案規模龐大時，依功能或領域拆分多個筆記本，而不是把所有東西塞進同一個：

```
大型專案
├── 筆記本 A（核心架構）    → 角色：系統架構師
├── 筆記本 B（用戶研究）    → 角色：UX 研究員
└── 筆記本 C（競爭情報）    → 角色：市場分析師
```

在專案設定中將每個筆記本綁定到對應的功能分支或模組。Agent 會根據查詢內容自動選擇正確的筆記本。

### 最佳實踐

1. **角色要具體** — 「資深創投分析師」 > 「有用的助手」
2. **說明知識庫內容** — 告訴它上傳了哪類文件
3. **定義分析框架** — TAM/SAM、RICE、SWOT 等
4. **設定挑戰程度** — 應該附和還是挑戰假設？
5. **對齊輸出格式** — 你的專案需要什麼樣的回答？
6. **大專案要拆分** — 達到來源限制時，一個功能/領域一個筆記本

### 專案整合

在專案設定中儲存角色描述，實現自動化設定：

```python
# config.py 或 .env
NOTEBOOKLM_NOTEBOOK_ID = "your-notebook-id"
NOTEBOOKLM_PERSONA = """你的角色描述..."""
NOTEBOOKLM_RESPONSE_LENGTH = "long"
```

Agent 在建立新專案時，會根據專案目標自動生成角色描述、存入設定檔、並透過 `set_notebook_guide.py` 套用。

---

## 指令

| 你說的話 | 執行動作 |
|---------|---------|
| 「設定 NotebookLM 驗證」 | 開啟 Chrome 進行 Google 登入 |
| 「把 [連結] 加到我的 NotebookLM 資料庫」 | 儲存筆記本及其描述 |
| 「顯示我的 NotebookLM 筆記本」 | 列出所有已儲存的筆記本 |
| 「問我的文件關於 [主題]」 | 查詢對應筆記本 |
| 「使用 [名稱] 筆記本」 | 設定當前使用的筆記本 |
| 「設定對話為 [角色]」 | 設定筆記本角色（Notebook Guide） |
| 「清除 NotebookLM 資料」 | 重新開始（保留筆記本庫） |

### 腳本參考

```bash
# 查詢
python scripts/run.py ask_question.py --question "..." [--notebook-id ID] [--show-browser]

# 設定角色
python scripts/run.py set_notebook_guide.py --persona "..." [--response-length long] [--notebook-id ID]

# 筆記本庫管理
python scripts/run.py notebook_manager.py list
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py notebook_manager.py activate --id ID
python scripts/run.py notebook_manager.py remove --id ID

# 驗證管理
python scripts/run.py auth_manager.py setup    # 初始設定
python scripts/run.py auth_manager.py status   # 檢查狀態
python scripts/run.py auth_manager.py reauth   # 重新驗證
```

---

## 架構

```
~/.claude/skills/notebooklm/
├── SKILL.md                      # Claude Code 的指令檔
├── scripts/
│   ├── run.py                    # 入口（自動建立 venv）
│   ├── ask_question.py           # 查詢 NotebookLM
│   ├── set_notebook_guide.py     # 設定筆記本角色
│   ├── notebook_manager.py       # 筆記本庫管理
│   ├── auth_manager.py           # Google 驗證
│   ├── browser_utils.py          # 瀏覽器工廠 + 擬人化工具
│   ├── browser_session.py        # Session 管理
│   └── config.py                 # 選擇器、路徑、常數
├── data/                         # 本地儲存（已 git-ignore）
│   ├── library.json              # 筆記本描述資料
│   ├── auth_info.json            # 驗證狀態
│   └── browser_state/            # 瀏覽器設定檔 + Cookie
└── .venv/                        # 獨立 Python 環境（自動建立）
```

**運作方式：**
1. 當你提到 NotebookLM 時，Claude Code 載入 `SKILL.md`
2. 透過 `run.py` 執行對應的 Python 腳本
3. Patchright 開啟帶有持久驗證的無頭 Chrome
4. 與 NotebookLM 的 DOM 互動（輸入問題、讀取答案、設定角色）
5. 將結果回傳給 Claude Code

**技術棧：**
- [Patchright](https://github.com/nickhath/patchright) — Playwright 分支，具反偵測能力
- 真實 Chrome（非 Chromium）— 與 Google 服務相容性更好
- 擬人化互動模式 — 模擬真實打字速度、隨機延遲

---

## 推薦工作流：NotebookLM 作為專案文件中心

我們圍繞一個特定的理念打造了這個 Skill：**NotebookLM 應該成為你專案累積知識的單一事實來源。**

不用在散落各處的 markdown 檔案、git log 和聊天紀錄中翻找，在產出關鍵文件時就上傳到 NotebookLM。隨著時間推移，你的筆記本會成為一個可查詢的知識庫，記錄專案的完整發展歷史。

### 實際運作方式

```
你撰寫了一份文件（規格、研究、會議紀錄、架構決策）
    ↓
透過 add_source.py 上傳到 NotebookLM
    ↓
用分類前綴標記：[產品規劃]、[用戶研究]、[競品分析] 等
    ↓
之後直接問你的筆記本，而不是翻檔案：
  「我們對 auth 模組做了什麼決定？為什麼？」
  「根據 [用戶研究] 的來源，前 3 大痛點是什麼？」
```

### 來源管理技巧

- **隨做隨傳** — 每份新文件需要一次 `add_source.py` 呼叫。目前沒有自動同步功能。
- **先整合再上傳** — 30 則關於同一主題的小筆記應該整合成 1 份帶權重標註的結構化來源，而不是分 30 次上傳。
- **使用分類前綴** — 在來源標題加上 `[分類]` 前綴（例如 `[用戶痛點] 論壇分析`）。查詢時引用該分類以聚焦答案。
- **控制來源數量** — 每個筆記本最多支援 50 個來源。品質重於數量。
- **無法原地更新** — 要更新來源，需先移除舊的再重新添加。

### 分類前綴範例

| 前綴 | 用途 |
|------|------|
| `[用戶痛點]` | 用戶反饋、論壇討論、社群回饋 |
| `[競品分析]` | 競品評測、功能比較 |
| `[學術研究]` | 學術論文、教學研究 |
| `[市場數據]` | 市場規模、趨勢、人口統計 |
| `[產品規劃]` | 產品規格、架構文件、決策紀錄 |

```bash
# 帶分類上傳
python scripts/run.py add_source.py \
  --category "產品規劃" \
  --title "Auth 模組架構決策" \
  --file docs/auth-decision.md \
  --notebook-id my-project

# 依分類查詢
python scripts/run.py ask_question.py \
  --question "只根據 [產品規劃] 的來源，我們做了哪些架構決策？" \
  --notebook-id my-project
```

---

## 限制

- **僅限本機 Claude Code** — 網頁版沙箱會封鎖網路存取
- **無 Session 持久化** — 每次提問開啟新的瀏覽器
- **NotebookLM 速率限制** — 免費版有每日查詢上限
- **手動上傳** — 每份文件需要一次 `add_source.py` 呼叫（尚無自動同步）

---

## 疑難排解

| 問題 | 解決方案 |
|------|---------|
| 找不到 Skill | 確認 `~/.claude/skills/notebooklm/SKILL.md` 存在 |
| 驗證失敗 | `「重設 NotebookLM 驗證」` |
| 瀏覽器崩潰 | `「清除 NotebookLM 瀏覽器資料」` |
| 達到速率限制 | 等待或切換 Google 帳號 |
| 依賴損壞 | 刪除 `.venv/`，下次執行時自動重建 |

---

## 安全性

- 所有資料留在本機
- Google 憑證儲存在 `data/browser_state/`（已 git-ignore）
- 無外部 API 呼叫——僅對 notebooklm.google.com 進行瀏覽器自動化
- 建議：使用專用 Google 帳號進行自動化

---

## 開發藍圖

我們計畫中但尚未實作的功能：

- **來源匯出（`export_sources.py`）** — 將筆記本中的所有來源下載回本地專案資料夾。作為 Google [關閉服務紀錄](https://killedbygoogle.com/)的保險。你的知識不應該被鎖在任何單一平台裡。

- **即時來源更新（`refresh_sources.py`）** — 有些來源是「活的」（產業部落格、官方文件、趨勢報告）——內容會隨時間更新，但 NotebookLM 只擷取第一次添加時的內容。這個功能讓你將來源標記為 `[LIVE]`，然後定期重新匯入，讓筆記本的知識保持最新。將 NotebookLM 從靜態檔案庫變成活的知識庫。

---

## 致謝

- [NotebookLM MCP Server](https://github.com/PleasePrompto/notebooklm-mcp) by **PleasePrompto** — 啟發本 Skill 的原始實作
- **[@blazingzebra](https://x.com/blazingzebra)** — 來源分類前綴技巧
- **[@Tool_Drop_1](https://youtube.com/@Tool_Drop_1)** — NotebookLM 技巧與工作流
- **[Steven Johnson](https://x.com/stevenbjohnson)** — NotebookLM Editorial Director，他對產品的願景影響了我們思考 source-grounded AI 的方式

---

## 授權

MIT

</div>
