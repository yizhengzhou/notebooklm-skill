<div align="center">

**[English](README.md)** | **[繁體中文](README.zh-TW.md)**

# NotebookLM Claude Code Skill

**讓 NotebookLM 成為 Claude Code 的專案級 AI 文件管理員**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Experimental-orange.svg)]()

> 一個專案，兩個筆記本 — 一個研究，一個執行。各自擁有專家角色。你的 AI Agent 獲得專屬的、基於文件來源的研究夥伴——而不是通用聊天機器人。

> **注意：** 此 Skill 由 [Fork](https://fork.work) 積極開發與實驗中。我們每天在自己的專案中使用它，開源是為了分享我們所學到的。可能會有粗糙的地方——歡迎貢獻和回饋。

[安裝](#安裝) • [快速開始](#快速開始) • [設定對話](#設定對話notebook-guide角色設定) • [指令](#指令)

</div>

---

## 核心理念

大多數 NotebookLM 整合只把它當成問答工具——你問，它答。

這個 Skill 採用完全不同的思路：**NotebookLM 作為專案知識庫，規劃與執行分離。**

受 [harness engineering](https://openai.com/index/harness-engineering/) 啟發，每個專案擁有一個 **Research notebook**（為什麼要做）和一個 **Project notebook**（在做什麼）。各自有專家角色，Agent 自動根據問題類型路由到正確的筆記本。

```
MyProject
├── [Research] Notebook  → 角色：市場分析師  → 「30 篇論壇帖中前三大痛點...」
│   └── 用戶痛點、競品分析、市場數據
└── [Project] Notebook   → 角色：產品經理    → 「Auth 模組用 OAuth，3/15 決定的...」
    └── 產品規格、架構決策、版本歷史
```

**核心功能：**
- **雙筆記本架構** — 一個指令建立 Research + Project 配對（`--pair`）
- **專家角色 + 語氣預設** — 平衡、創投視角、嚴苛批評（`--tone`）
- **自動查詢路由** — Agent 根據問題意圖選擇正確的筆記本
- **無頭自動化** — 無需開啟瀏覽器即可查詢、建立和設定筆記本
- **來源組織** — 分類前綴、權重標記、`[LIVE]` 時效性追蹤
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

## 核心哲學：Notebook 作為專案介面

除了基於文件的問答之外，我們認為 notebook 在專案中扮演三個角色：

### 1. 知識庫 — Agent 的結構化記憶

雙 notebook 架構（Research + Project）給你的 agent 一個持久的、有組織的記憶。Agent 不用重複搜尋同樣的問題，直接查 notebook 就能得到有引用的答案。隨著時間推移，大部分專案問題都能從 notebook 回答 — 這就是目標。

### 2. 認知反饋迴路 — 重新審視自己想法的鏡子

當你寫了一份產品企劃書上傳到 NotebookLM，然後用 Audio Overview 聽兩個人討論它，某種東西會改變。你從第三人稱的視角聽到自己的想法。盲點浮現。假設被挑戰。這不只是換一種輸出格式 — 這是切換認知模式。閱讀你的企劃是第一人稱思考；聽別人辯論它是第三人稱思考。這兩個視角之間的落差，就是最好的改進靈感來源。

### 3. 對話入口 — 給人類的介面

專案的檔案資料夾是給開發者看的。裡面充滿了各種版本的文件、設定檔和只有寫的人才懂的 context。對任何其他人 — 新加入的團隊成員、協作者、投資人 — 這些資料夾是難以進入的。

Notebook 是專案的**人類介面**。任何人都可以打開它用自然語言提問：「這個專案在做什麼？」「為什麼選這個架構？」「主要風險是什麼？」他們不需要理解資料夾結構、git 歷史或程式碼。Notebook 在他們的位置迎接他們。

這就是為什麼我們把 notebook 當作專案的一級產物，而不是附屬工具。它是原始專案檔案和需要理解它們的人之間的橋樑。

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

### 擴展策略：雙 Notebook 架構（Harness Engineering）

受 [harness engineering](https://openai.com/index/harness-engineering/) 規劃與執行分離模式的啟發，我們建議為每個專案建立 **Research + Project notebook 配對**：

```bash
python scripts/run.py create_notebook.py --name "MyProject" --pair
```

自動建立：
- **[Research] MyProject** — 市場研究、用戶痛點、競品分析
- **[Project] MyProject** — 產品規格、版本歷史、技術決策

```
MyProject
├── [Research] Notebook     → 角色：市場分析師
│   └── 為什麼要做、誰需要、競品怎麼做
└── [Project] Notebook      → 角色：產品經理
    └── 在做什麼、做了什麼決定、版本歷史
```

**為什麼分開？** 問「用戶最大的痛點是什麼」時，你只想從研究來源得到答案，不要混入技術規格。問「auth 模組怎麼決定的」時，你想要專案決策，不是競品分析。角色路由讓回答更精準。

**額外價值：** Project notebook 可以當作活的簡報素材 — 用 NotebookLM 內建的 Audio Overview 功能隨時產出專案介紹，用於投資人簡報、客戶說明或團隊 onboarding。

#### 角色語氣預設

`--pair` 會自動替兩個 notebook 設定角色。選擇適合你專案階段的語氣：

```bash
# 平衡（預設）— 有證據支持的分析，適度挑戰假設
python scripts/run.py create_notebook.py --name "MyProject" --pair

# 創投視角 — 用投資人的眼光評估（TAM/SAM、護城河、單位經濟）
python scripts/run.py create_notebook.py --name "MyProject" --pair --tone vc

# 嚴苛批評 — 找致命缺陷，假設所有樂觀都是錯的直到證明
python scripts/run.py create_notebook.py --name "MyProject" --pair --tone critic
```

| 語氣 | Research 角色 | Project 角色 | 適合場景 |
|------|-------------|-------------|---------|
| `default` | 市場研究分析師 | 產品經理 | 日常開發 |
| `vc` | 創投分析師（投資視角） | 創投合夥人（執行審查） | 募資、簡報準備 |
| `critic` | 殘酷市場批評家 | 無情技術審查者 | 上線前壓力測試 |

**建立後可自訂：** 這些是起點。隨時用以下指令修改角色：

```bash
python scripts/run.py set_notebook_guide.py --persona "你的自訂角色..." --notebook-id ID
```

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

### 近期

- **來源匯出（`export_sources.py`）** — 將筆記本中的所有來源下載回本地專案資料夾。作為 Google [關閉服務紀錄](https://killedbygoogle.com/)的保險。你的知識不應該被鎖在任何單一平台裡。

- **即時來源更新（`refresh_sources.py`）** — 有些來源是「活的」（產業部落格、官方文件、趨勢報告）——內容會隨時間更新，但 NotebookLM 只擷取第一次添加時的內容。這個功能讓你將來源標記為 `[LIVE]`，然後定期重新匯入，讓筆記本的知識保持最新。

### 長期願景

這個 skill 背後的方法論 — 雙 notebook 架構、來源權重、分類前綴、角色驅動分析 — 被設計為**平台無關**的。NotebookLM 是目前的實作，因為它很好用而且免費，但這些模式應該能脫離工具而存在。

我們正在探索一個開源、可自建的替代方案，將相同的方法論帶到本地：
- **知識庫** — 結構化、基於來源的專案記憶，任何 agent 都能查詢
- **認知反饋** — 多格式輸出（音頻討論、簡報摘要、Q&A），從不同角度審視自己的想法
- **對話介面** — 任何人都能直接對專案提問，不需要翻閱原始檔案
- **完整資料主權** — 不依賴外部服務

在那之前，來源匯出功能確保你的資料永遠不會被鎖住。

---

## 更新紀錄

本 Skill 持續跟進最新的 AI Agent 方法論，將新的模式融入設計。

| 版本 | 日期 | 重點 |
|------|------|------|
| **1.4.0** | 2026-03-24 | 自動建立 notebook。受 [harness engineering](https://openai.com/index/harness-engineering/) 啟發的**雙筆記本架構** — 規劃（研究）與執行（專案）知識分離。角色語氣預設（`--tone vc`、`--tone critic`）。`[LIVE]` 來源時效性約定。 |
| **1.3.2** | 2026-03-22 | 來源重新命名修正。分類前綴選擇指引（`[用戶痛點]` vs `[競品分析]`）。來源權重實驗結果。 |
| **1.3.1** | 2026-03-21 | 多帳號認證修正。錯誤 Google 帳號偵測與診斷。 |
| **1.0.0** | 2026-03-21 | 首次公開發布。模組化架構、瀏覽器自動化、筆記本庫、角色設定、認證系統。 |

完整記錄請見 [CHANGELOG.md](CHANGELOG.md)。

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
