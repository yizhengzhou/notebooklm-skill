# NotebookLM Project Brain：MCP + Skill 發展企劃與實作路線圖

> 日期：2026-10-13
> 文件版本：v1.0
> 狀態：規劃基線（尚未開始本企劃的程式實作）
> 適用專案：`notebooklm-skill`
> 核心方向：以 **NotebookLM + Project Brain MCP + Agent Skill + 專案綁定檔**，把 NotebookLM 建成 Coding Agent 可主動使用、可持續維護的專案大腦。

---

## 0. 一頁摘要

本專案目前已具備可靠的 NotebookLM 操作基礎：建立／接管 Notebook、設定 Persona、詢問 Gemini、取得引用、執行 Deep Research、審查後匯入來源、保護 Pinned 來源、刷新 URL／Drive 來源及匯出狀態。

但目前仍偏向「人知道 Advisor ID，然後手動操作 CLI」。它尚未完整解決下列核心問題：

1. Coding Agent 如何知道目前專案有一顆 NotebookLM 大腦。
2. Coding Agent 如何知道應該連接哪一本 Notebook。
3. Coding Agent 在什麼情況下應主動詢問大腦。
4. 專案主要文件變更後如何安全同步。
5. 開發紀錄如何整理成可長期查詢的知識，而不是直接傾倒 raw log。
6. LLM 上下文遺失或換 Agent 時，如何快速恢復專案狀態。
7. 如何確認 Notebook 中真的包含專案本身，而不只是專案使用的外部研究資料。

本企劃採用以下分工：

| 元件 | 責任 |
|---|---|
| NotebookLM | 儲存來源、跨文件理解、Gemini 問答、Deep Research，以及原生 Studio artifacts（簡報、Podcast、資訊圖、資料表、報告、心智圖、測驗、影片等） |
| Project Brain MCP | 提供標準化的發現、查詢、恢復、研究、同步、寫回及 artifact generation 工具 |
| Project Brain Skill／AGENTS.md | 告訴 Agent 大腦何時存在、什麼時候應使用、哪些行為禁止 |
| `.notebooklm/brain.json` | 將目前 Repository 綁定到精確的 Notebook unique ID |
| Sync／Curation Engine | 掃描、過濾、比較、整理與安全同步專案知識 |
| Scheduler／Notification | 選配的定期維護、認證更新與通知 |

一句話定義：

> **MCP 負責「怎麼連接」，Skill 負責「何時使用」，專案綁定檔負責「連到哪裡」，NotebookLM 負責「記住與回答」。**

安裝策略採用：

> **Project scope 為預設；User/global scope 只是選配。**

理想的使用者只需在單一專案中執行：

```bash
cd my-project
notebooklm-brain init
```

完成後，進入該專案的相容 Coding Agent 即可自動發現 Project Brain，同時把它當作：

1. **專案顧問**：查詢歷史、恢復上下文、研究外部資料、提供具引用的想法。
2. **文件管理員**：辨識值得保存的文件與決策、建立同步計畫、維護版本與來源品質。
3. **內容製作助手**：優先重用 NotebookLM 的簡報、Podcast、資訊圖、資料表、報告、心智圖、測驗與影片能力，不讓 Coding Agent 重新實作已有的生成管線。

---

## 1. 產品願景

### 1.1 核心願景

讓任何支援 MCP、Agent Skill 或 CLI 的 Coding Agent，在進入一個已初始化的專案後，可以：

- 自動知道專案存在 NotebookLM Project Brain。
- 自動取得正確的 Notebook unique ID。
- 在知識不足、上下文遺失、需要歷史決策或外部研究時主動查詢。
- 在完成重要工作後，將長期有價值的知識整理後寫回。
- 讓下一個 Agent 即使沒有上一段聊天上下文，也能恢復方向。

### 1.2 三個同時存在的產品角色

#### 角色 A：Project Advisor（專案顧問）

負責：

- 回答「為什麼以前這樣決定」。
- 找回架構、產品、研究與事故歷史。
- 指出來源衝突、資訊缺口與不確定性。
- 透過 NotebookLM Deep Research 尋找官方文件、規格與重要論文。
- 提供想法，但不虛構已執行的程式或操作。

#### 角色 B：Project Librarian（專案文件管理員）

負責：

- 掃描經允許的專案文件。
- 判斷文件是否穩定、可檢索、不可替代且訊噪比足夠。
- 偵測新增、修改、重新命名、過期與取代關係。
- 將 raw log 整理成決策摘要、handoff、ADR 或 troubleshooting note。
- 維持 Notebook 來源的新鮮度、品質與可追溯性。
- 持續檢查 Project Brain 是否具備足夠的專案 canonical sources；若只有外部研究資料，必須標示 `research_only`，不能假裝能解釋專案本身。

#### 角色 C：NotebookLM Studio Producer（內容製作助手）

負責：

- 將已存在於 Project Brain 的可靠來源轉為簡報／slide deck。
- 產生 Audio Overview／Podcast。
- 產生 infographic、data table、mind map、report、quiz、flashcards 及 video。
- 在 NotebookLM 已具備相應能力時，避免 Coding Agent 自行重新撰寫簡報生成器、Podcast pipeline、圖表整理腳本或長篇來源摘要。
- 回傳 artifact ID、狀態與可下載格式，而不是把大型生成結果全部塞回 Agent context。

三個角色可使用同一顆 Notebook；MVP 不強迫建立 Research／Project 雙 Notebook。Studio 能力可以在早期先做 capability discovery 與 routing，完整生成／下載流程於後續 Phase 完成。

---

## 2. 非目標

本企劃不以以下項目作為 MVP 目標：

1. 不把 NotebookLM 當作 Git、原始碼、Issue tracker 或正式資料庫的替代品。
2. 不自動上傳整個 Repository。
3. 不預設上傳原始碼、terminal log、測試輸出、build artifact 或 secrets。
4. 不保證支援所有 Coding Agent；先支援具 MCP 或 Agent Skills 相容性的客戶端，其他環境保留 CLI fallback。
5. 不讓 NotebookLM 回答取代本地程式碼、測試與 runtime 證據。
6. 不預設自動刪除 Notebook 來源。
7. 不預設全域安裝或讓所有專案看到 Project Brain 工具。
8. 不在第一階段建立新的 NotebookLM backend；沿用 `notebooklm-py`。
9. 不在本專案重新實作 Studio audio、slides、video、infographic 等生成引擎；Project Brain 應偵測、說明並委派給 NotebookLM／`notebooklm-py` 的既有能力。

---

## 3. 設計原則

### 3.1 Project-local first

預設只在目前專案啟用：

```bash
notebooklm-brain init --scope project
```

User/global scope 必須由使用者明確選擇：

```bash
notebooklm-brain install --scope user
```

### 3.2 明確使用完整 Notebook ID

所有自動化呼叫必須使用完整 Notebook UUID，不依賴 `notebooklm use` 或全域「目前 Notebook」狀態。

### 3.3 Manifest 是綁定真相來源

`.notebooklm/brain.json` 負責描述「這個專案連到哪一本 Notebook」。LLM 不需要把 UUID 記在聊天上下文；每次由工具重新讀取。

### 3.4 Local-first、Brain-when-needed

Agent 應先讀取本地程式碼與目前檔案；Project Brain 用於：

- 歷史原因。
- 跨文件綜合。
- 上下文恢復。
- 外部研究。
- 難以從目前程式碼直接推導的專案知識。

NotebookLM 的舊文件不能凌駕目前程式碼與測試結果。

### 3.5 Review before external mutation

查詢可以自動執行；新增、替換、刪除 Notebook 來源預設必須經過 Plan → Review → Apply。

### 3.6 Curate, do not dump

開發紀錄必須先整理，再決定是否上傳。預設不接受 raw log 全量上傳。

### 3.7 無 manifest 就不猜

如果目前目錄及父目錄找不到 `.notebooklm/brain.json`：

- MCP 不得猜測 Notebook。
- 不得使用最近一次選取的 Notebook。
- 應回傳 `PROJECT_BRAIN_NOT_CONFIGURED` 及初始化指引。

### 3.8 認證與專案設定分離

Notebook ID 不是 Google credential。Google cookies、tokens 及 storage state 不得寫入 Repository、manifest、export 或 MCP log。

### 3.9 可恢復與可稽核

長時間研究與外部修改必須具備 run ID、狀態查詢、resume/reconcile 及 immutable operation record。

---

## 4. 使用者旅程

## 4.1 單一專案：預設旅程

### 步驟 1：進入專案

```bash
cd my-project
```

### 步驟 2：初始化 Project Brain

```bash
notebooklm-brain init
```

預設等同：

```bash
notebooklm-brain init --scope project
```

初始化精靈詢問：

1. 建立新 Notebook 或接管既有 Notebook。
2. Project Brain 名稱。
3. 主要角色：Advisor + Librarian + Studio Producer（預設三者可用，但 Studio generation 每次仍需確認）。
4. 初始來源 include／exclude。
5. 文件同步採 review 或 auto 模式；預設 review。
6. 是否更新既有 `AGENTS.md`；預設只預覽變更。
7. 要為哪些相容 Agent 安裝 project-local Skill／MCP 設定。

初始化完成後：

- 建立或接管 Notebook。
- 取得完整 Notebook UUID。
- 建立 `.notebooklm/brain.json`。
- 安裝 project-local Skill。
- 在客戶端支援時建立 project-local MCP 設定。
- 建立第一次文件掃描與同步計畫。
- 不在沒有審查的情況下直接上傳整個專案。

### 步驟 3：第一次同步

```bash
notebooklm-brain sync plan
```

輸出：

- 建議新增的文件。
- 建議跳過的文件與原因。
- 疑似重複或被取代的文件。
- secrets／敏感資料警告。
- 預估來源數量。
- Plan digest。

使用者核准後：

```bash
notebooklm-brain sync apply --approved-digest <digest>
```

### 步驟 4：日常開發

Agent 進入 Repository 後：

1. Skill 發現 `.notebooklm/brain.json`。
2. 呼叫 `brain_discover`／`brain_status`。
3. 驗證 Notebook 存在且帳號有權限。
4. 在需要時呼叫 Advisor 類工具。
5. 在穩定文件或重要決策出現時建立 Librarian 類 Plan。
6. 當使用者要求簡報、Podcast、資訊圖、資料表、報告、心智圖、測驗或影片時，先查 `brain_capabilities`，能由 NotebookLM 完成就優先委派，不重新造輪子。

### 步驟 5：工作結束

Agent 先建立記憶寫回草稿：

```bash
notebooklm-brain remember plan
```

內容只包含：

- 已完成事項。
- 重要決策及理由。
- 已否決方案及理由。
- 風險與未知。
- 未完成事項。
- 對應 Git commit／檔案。

使用者或政策核准後才寫入 NotebookLM。

### 步驟 6：下一個 Agent 接手

下一個 Agent 呼叫：

```text
brain_recover
```

取得具引用的專案恢復摘要，而不依賴上一段聊天內容。

---

## 4.2 User/global scope：選配旅程

經常在多個專案使用者可選擇：

```bash
notebooklm-brain install --scope user
```

這只代表 MCP Server／Skill 可在 user scope 被發現，不代表任意 Repository 已綁定 Notebook。

每個專案仍必須有：

```text
.notebooklm/brain.json
```

沒有 manifest 時，Project Brain 工具不得操作任何 Notebook。

---

## 4.3 不支援 project-local MCP 的客戶端

若某個客戶端只能在 user scope 註冊 MCP：

- MCP Server 可以 user scope 安裝。
- Skill、manifest 與啟用規則仍保持 project-local。
- MCP 每次先執行 project discovery。
- 找不到 manifest 就保持 inert，不暴露任何最近使用的 Notebook context。

---

## 4.4 Clone 到另一台機器

當使用者 clone 一個已初始化專案：

1. `.notebooklm/brain.json` 提供 Notebook UUID。
2. 使用者以自己的 Google 帳號完成 NotebookLM authentication。
3. `notebooklm-brain doctor` 驗證是否有 Notebook 存取權。
4. 若有權限，本機 Advisor state 可從 manifest 與 backend source list 重新 hydration。
5. 若無權限，回傳明確的 share／account 指引，不建立重複 Notebook。

---

## 5. 系統架構

```text
┌──────────────────────────────────────────────────────────────┐
│ Coding Agent Host                                            │
│ Pi / Claude Code / Codex / Cursor / Windsurf / Others        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                   Project-local Skill / AGENTS.md
                   「是否存在、何時呼叫、行為邊界」
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Project Brain MCP Server                                     │
│                                                              │
│ Discovery  Query  Recovery  Research  Sync  Remember  Health │
└───────────────┬───────────────────────────┬──────────────────┘
                │                           │
                │ 讀取                      │ 呼叫
                ▼                           ▼
┌──────────────────────────────┐   ┌───────────────────────────┐
│ .notebooklm/brain.json       │   │ notebooklm_skill          │
│ Project → Notebook UUID      │   │ EvergreenService / Store  │
│ Scope / Policy / Source Rule │   │ Safe Apply / Export       │
└──────────────────────────────┘   └──────────────┬────────────┘
                                                  │
                                                  ▼
                                    ┌───────────────────────────┐
                                    │ notebooklm-py             │
                                    │ Auth / API / Research     │
                                    └──────────────┬────────────┘
                                                   │
                                                   ▼
                                    ┌───────────────────────────┐
                                    │ Google NotebookLM Gemini  │
                                    └───────────────────────────┘
```

### 5.1 為何需要 Project Brain MCP，而不是只用 generic NotebookLM MCP

`notebooklm-py` 已提供 generic MCP 與完整 NotebookLM CLI。它適合：

- 建立 Notebook。
- 加入來源。
- 問答。
- 研究。
- 產生 artifacts。

但它不知道：

- Repository 對應哪一本 Notebook。
- 什麼時候 Agent 應查詢專案歷史。
- 哪些本地文件應同步。
- 如何以 Git／hash 管理來源版本。
- 如何把開發過程整理成長期記憶。

因此本專案應建立一層較薄的 Project Brain MCP，重用 `notebooklm-py`，不重寫 NotebookLM RPC。

---

## 6. 專案目錄與資料邊界

建議的 Repository 結構：

```text
my-project/
├── .notebooklm/
│   ├── brain.json
│   └── .gitignore
├── .agents/
│   └── skills/
│       └── notebooklm-project-brain/
│           └── SKILL.md
├── .mcp.json                 # 僅在客戶端支援時建立
├── AGENTS.md                 # 可選，不能覆寫既有內容
├── README.md
├── docs/
└── src/
```

### 6.1 可提交進 Git

建議提交：

- `.notebooklm/brain.json`
- project-local Skill
- project-local MCP 非秘密設定
- 經使用者核准的 `AGENTS.md` Project Brain 區塊

### 6.2 不得提交進 Git

不得提交：

- Google cookies／tokens。
- `storage_state.json`。
- 帳號 session。
- 暫存 research results。
- MCP request／response raw logs。
- 尚未審查的同步內容。
- 可能包含秘密的 scan cache。

### 6.3 Runtime state

Runtime state 仍存放在作業系統 App Data，或在 `.notebooklm/cache/` 使用 gitignored cache。它包含：

- 上次掃描時間。
- 檔案 hash。
- Notebook backend source ID。
- 最後同步 commit。
- run checkpoints。
- operation evidence。

MVP 建議沿用既有 `AdvisorStore` 作為 durable runtime state，manifest 僅保存 portable binding 與 policy。

---

## 7. `.notebooklm/brain.json` 合約

建議 schema：

```json
{
  "schema_version": 1,
  "project_id": "my-project",
  "scope": "project",
  "advisor_id": "my-project-brain",
  "backend": {
    "type": "gemini-notebook",
    "notebook_id": "b74884a1-147a-4279-ae41-a089e8ae05f7"
  },
  "roles": {
    "advisor": true,
    "librarian": true,
    "studio_producer": true
  },
  "consult_policy": {
    "on_missing_context": true,
    "on_historical_decision": true,
    "on_external_research": true,
    "before_major_architecture_change": true,
    "local_code_first": true
  },
  "source_policy": {
    "include": [
      "README.md",
      "AGENTS.md",
      "docs/**/*.md"
    ],
    "exclude": [
      ".env*",
      "**/secrets/**",
      "build/**",
      "dist/**",
      "runs/**",
      "logs/**",
      "**/*.log"
    ],
    "max_file_bytes": 2000000,
    "follow_symlinks": false,
    "required_project_roles": [
      "project_overview",
      "architecture",
      "current_status",
      "decisions"
    ]
  },
  "sync_policy": {
    "mode": "review",
    "retirement_mode": "confirm",
    "writeback_mode": "review"
  }
}
```

### 7.1 驗證規則

- `schema_version` 必須受支援。
- `scope` 只允許 `project` 或 `user`。
- Notebook ID 必須是完整 UUID，不接受自動化中的模糊 prefix。
- include／exclude 必須是 Repository-relative path pattern。
- 不接受指向 Repository 外部的 path traversal。
- 預設不 follow symlink。
- 不允許 credential 欄位。
- manifest 找到多份時，以最近 Repository root 的 manifest 為準，但必須顯示來源路徑。

---

## 8. MCP Server 規劃

## 8.1 MCP 職責

Project Brain MCP 應提供：

1. Project discovery。
2. Notebook binding validation。
3. Advisor read/query/recovery。
4. Project grounding coverage 與 source-role gap detection。
5. Deep Research preview and status。
6. Local source scan and reviewed sync。
7. Curated session memory plan and apply。
8. NotebookLM capability discovery 與 source-grounded Studio artifact delegation。
9. Health、diagnostic 與可機器解析的錯誤。

MCP 不應：

- 自己保存 Google credential。
- 自己實作 NotebookLM RPC。
- 在沒有 manifest 的情況猜 Notebook。
- 默認上傳整個 Repository。
- 繞過既有 Safe Apply invariants。

---

## 8.2 MCP Tools

### A. Discovery 與 Health

#### `brain_discover`

用途：從 `cwd` 找出 Project Brain。

輸入：

```json
{
  "cwd": "/path/to/project"
}
```

輸出至少包含：

```json
{
  "configured": true,
  "project_root": "/path/to/project",
  "manifest_path": ".notebooklm/brain.json",
  "advisor_id": "my-project-brain",
  "notebook_id": "...",
  "roles": ["advisor", "librarian", "studio_producer"]
}
```

找不到時回傳 typed error，不猜 Notebook。

#### `brain_status`

用途：顯示 binding、來源數量、最後同步、未完成 operation、文件 drift 摘要，以及目前是 `research_only`、`project_partial`、`project_ready` 或 `project_stale`。

#### `brain_grounding_check`

用途：針對即將執行的問題或 artifact，確認 Notebook 中是否存在足夠且最新的專案來源，而不是只看總來源數量。

輸入至少包含：

- user intent／question。
- requested output scope（project、external research、mixed）。
- required source roles。

輸出至少包含：

- coverage status。
- available project source roles。
- missing／stale roles。
- research-only source count。
- 是否允許繼續。
- 建議建立的 onboarding／sync plan。

#### `brain_onboarding_plan`

用途：在 Project Brain 初始化或 coverage 不足時，掃描 Repository，找出最小但足以描述專案的 canonical source set；只產生 Plan，不直接上傳。

#### `brain_capabilities`

用途：動態回報目前 `notebooklm-py`／MCP server 真正支援的 NotebookLM 功能，避免 Skill 內的大型靜態說明過期。

輸出至少包含：

- chat／citations。
- web／Drive research。
- source types。
- artifact types。
- 每種 artifact 可用的 output formats。
- provider／package version。
- plan／quota 可得性。
- 功能是否需要長時間等待、是否需要使用者確認。

Skill 只保留精簡 routing 規則；詳細參數在需要時由 `brain_capabilities` 逐步揭露，避免每次 session 都把完整 NotebookLM 手冊放進 LLM context。

#### `brain_health`

用途：檢查：

- manifest schema。
- NotebookLM authentication。
- Notebook access。
- AdvisorStore hydration。
- MCP／Skill version compatibility。
- source registry/backend 差異。

不得在 health check 中修改來源。

---

### B. Advisor 查詢

#### `brain_ask`

用途：向目前專案大腦提問。

輸入：

```json
{
  "cwd": "/path/to/project",
  "question": "過去為什麼選擇這個架構？",
  "conversation_id": null,
  "citation_mode": "required"
}
```

輸出：

- answer。
- structured citations。
- source IDs／titles。
- conversation metadata。
- uncovered／unknown claims。
- `local_verification_recommended`。

重要規則：

- 不得以刪除共享 conversation 作為一般 fresh query 實作。
- 不得聲稱 NotebookLM 回答已由本地程式碼證實。
- 未提供 citation 的事實性主張應標記為 unsupported。

#### `brain_recover`

用途：上下文遺失、Agent 接手或 session 啟動時恢復專案方向。

固定輸出 schema：

```json
{
  "project_goal": "...",
  "current_state": "...",
  "confirmed_decisions": [],
  "constraints": [],
  "recent_material_changes": [],
  "open_questions": [],
  "known_conflicts": [],
  "recommended_next_step": "...",
  "citations": [],
  "staleness_warnings": []
}
```

`brain_recover` 回答應提示 Agent 再核對 Git、目前檔案與測試。

---

### C. Research

#### `brain_research_preview`

用途：讓 NotebookLM 搜尋官方文件、規格、重要論文與相關資料，但不立即匯入來源。

輸入：

- query。
- mode。
- source budget。
- preferred domains。
- run ID。

輸出：

- task ID。
- status。
- candidate source metadata。
- Preview artifact path／digest。

預設需使用者同意後才開始可能長時間或消耗 quota 的 deep research；政策可配置。

#### `brain_research_status`

用途：恢復／查詢既有 task，不啟動重複研究。

#### `brain_research_plan`

用途：從候選來源建立 reviewed import plan。

#### `brain_research_apply`

用途：只套用經核准 digest 的來源變更，重用現有 Safe Apply。

---

### D. Librarian 同步

#### `brain_sync_scan`

用途：掃描 manifest 允許的檔案，產生本地 inventory，不修改 Notebook。

每個檔案至少記錄：

- repository-relative path。
- content SHA256。
- size。
- Git tracked/untracked。
- current Git blob／commit（可取得時）。
- MIME／source type。
- Upload Gate 結果。
- sensitivity warning。

#### `brain_sync_plan`

用途：比較本地 inventory、Advisor registry 與 Notebook sources。

分類：

- add。
- unchanged。
- changed。
- renamed。
- superseded。
- missing-local。
- conflict。
- rejected-by-gate。
- needs-human-review。

Plan 必須有 deterministic digest。

#### `brain_sync_apply`

用途：依 approved digest 執行：

1. 重新檢查本地檔案 hash。
2. 重新檢查 Notebook source snapshot。
3. 新來源先 add 並等待 ready。
4. 驗證 hydration 品質。
5. 更新 registry。
6. 只有明確核准才 retirement 舊來源。
7. 寫入 immutable sync run。

若 Plan 已 stale，必須 fail closed 並要求重建。

---

### E. Session 記憶寫回

#### `brain_remember_plan`

用途：將本次工作整理成長期可查詢的候選記憶，不立即上傳。

候選類型：

- decision。
- architecture change。
- durable constraint。
- reusable troubleshooting lesson。
- research conclusion。
- incident postmortem。
- handoff。

預設拒絕：

- raw terminal log。
- 完整聊天轉錄。
- 單次測試輸出。
- 可直接由 Git／程式碼推導的資訊。
- 未完成且即將被取代的草稿。
- secrets。

#### `brain_remember_apply`

用途：把經核准的記憶文件加入或更新 Notebook，保存 provenance：

- generated_at。
- repository。
- Git commit。
- related files。
- source evidence。
- approval digest。

---

### F. 管理工具

#### `brain_rebind`

用途：明確將專案改綁另一個 Notebook。必須顯示前後 ID，取得確認，原子更新 manifest 與本機 registry。

#### `brain_export`

用途：沿用 backend-neutral export。

#### `brain_doctor`

用途：提供可操作修復建議；不得默默建立重複 Notebook。

---

### G. NotebookLM Studio Artifacts

#### `brain_artifact_plan`

用途：根據使用者目標與目前 Notebook sources，選擇 NotebookLM 已有的 artifact 類型，而不是讓 Agent 先自行開發生成流程。

建議 routing：

| 使用者需求 | 優先 NotebookLM artifact |
|---|---|
| 簡報／presentation／pitch deck | slide deck |
| Podcast／語音導讀 | audio overview |
| 視覺摘要／圖解 | infographic |
| 結構化資料／比較表 | data table |
| 長篇整理／briefing／study guide | report |
| 概念關係 | mind map |
| 學習與驗收 | quiz／flashcards |
| 影片摘要 | video；cinematic video 僅在方案與需求適合時 |
| 修改既有簡報單頁 | revise slide |

Plan 建立前必須先執行 `brain_grounding_check`。若使用者要求「解釋這個專案」，但 Notebook 只有外部論文、官方文件或研究資料，Plan 必須 blocked 或把輸出誠實降級為「外部研究摘要」，不得把它命名為專案解釋。

Plan 應包含：

- artifact type。
- requested scope 與 verified grounding scope。
- selected source IDs，並區分 project canonical sources 與 external research sources。
- generation instructions。
- language／format／length 等已支援參數。
- 預估為長時間 operation 或一般 operation。
- 目前 plan／quota 警告。
- 生成後的下載格式。

#### `brain_artifact_generate`

用途：使用經確認的 Plan 啟動 NotebookLM 原生生成，立即回傳 task／artifact ID；主對話不得高頻 polling。

這是外部、可能消耗 quota 且長時間的操作，預設需使用者確認。Standard 免費方案可使用部分能力，但有 usage limits；Skill 不得把「免費」描述成「無限制」或保證永遠免費。

#### `brain_artifact_status`

用途：查詢既有 artifact 狀態，不建立重複 generation。

#### `brain_artifact_download`

用途：下載已完成 artifact。因為會寫入檔案系統，必須顯示目標路徑並取得確認；不得覆寫既有檔案，除非使用者明確允許。

#### Provider delegation 原則

- 直接重用 `notebooklm-py` 已有 generate／download／artifact status 能力。
- 不在 Project Brain MCP 重新製作 PPT、音訊、影片或 infographic renderer。
- Project Brain 的價值是選對 Notebook、選對來源、選對 artifact、保存 provenance 與處理 quota／狀態，不是複製 NotebookLM Studio。
- 若來源尚未同步或品質不足，先建立 sync／research plan，不要用過期來源生成看似完整的內容。
- 大型 artifact 保留在 provider／下載檔中；MCP 只回傳摘要與 metadata，減少 Coding Agent context token。

#### 典型案例：用 Artifact 幫助人理解複雜輸出

Andrej Karpathy 在這則公開文章中建議，面對越來越複雜的模型輸出，不要只停留在長篇文字，可以依需求升級為圖解、互動網頁或 explainer video：

- <https://x.com/karpathy/status/2105819303471976479>

Project Brain 應把這類「為理解而生成的一次性成品」視為正式 routing intent：

```text
使用者想理解一批來源／研究／模型輸出
        ↓
先確認 Project Brain 已有足夠且最新的來源
        ↓
brain_artifact_plan 選擇最合適形式
        ↓
簡報／Podcast／資訊圖／資料表／報告／心智圖／影片
        ↓
使用者確認後交給 NotebookLM 生成
        ↓
Agent 只接收 artifact metadata、摘要與下載位置
```

這可以避免 Coding Agent 為一次性的理解需求重新建立：

- PPT／slide renderer。
- Podcast narration pipeline。
- 一般資訊圖生成流程。
- 大量來源摘要與排版程式。
- 通用報告／study guide／quiz 生成器。

但 Skill 必須清楚說明能力邊界：

- NotebookLM 適合 source-grounded slide deck、audio overview、infographic、data table、report、mind map、quiz／flashcards 與其支援的 video。
- 自訂互動 HTML／web app 仍應交給 Coding Agent；NotebookLM 可以先產生研究摘要、內容架構或腳本，但不能被描述成任意 web-app builder。
- 高度客製的 3Blue1Brown-style 數學動畫或 bespoke explainer video，NotebookLM 可負責 source grounding、storyboard 或初步 video overview；若需要精準動畫程式與品牌化製作，仍應轉交專門影片／前端工具。
- 「NotebookLM first」是避免重造已有能力，不代表所有內容製作都強制使用 NotebookLM。

此模式的成本優勢來自：

1. 不必把全部來源重新塞進 Coding Agent context。
2. 不必為一次性成品撰寫及維護客製生成程式。
3. 可以利用 Standard 免費方案的既有額度。
4. MCP 只傳遞 source IDs、生成目標與結果 metadata。

但不能宣稱零成本或無限使用：NotebookLM Standard 雖可免費使用，仍有來源數、AI usage、artifact generation、地區、功能 rollout 及 provider policy 限制。

---

## 8.3 MCP Resources

若客戶端支援 MCP Resources，可提供：

- `project-brain://manifest`
- `project-brain://status`
- `project-brain://source-index`
- `project-brain://latest-handoff`
- `project-brain://open-decisions`
- `project-brain://capabilities`
- `project-brain://artifacts`

Resources 只提供讀取投影，不成為另一套獨立狀態來源。

---

## 8.4 MCP Prompts

可提供標準 prompts：

- `recover-project-context`
- `research-official-documentation`
- `challenge-architecture-decision`
- `prepare-session-handoff`
- `curate-project-documents`

Prompt 是方便入口，不取代 typed tools 與 policy。

---

## 8.5 MCP 錯誤合約

所有錯誤需機器可解析：

- `PROJECT_BRAIN_NOT_CONFIGURED`
- `MANIFEST_INVALID`
- `AUTH_REQUIRED`
- `NOTEBOOK_ACCESS_DENIED`
- `NOTEBOOK_NOT_FOUND`
- `ADVISOR_STATE_MISSING`
- `ADVISOR_STATE_DRIFT`
- `SOURCE_PLAN_STALE`
- `APPROVAL_REQUIRED`
- `DIGEST_MISMATCH`
- `SOURCE_HYDRATION_FAILED`
- `SOURCE_LIMIT_UNKNOWN`
- `SOURCE_CAPACITY_WARNING`
- `SOURCE_CAPACITY_EXHAUSTED`
- `SOURCE_ADD_NOT_COMMITTED`
- `PROJECT_GROUNDING_INSUFFICIENT`
- `PROJECT_SOURCES_STALE`
- `RESEARCH_ONLY_NOTEBOOK`
- `RESEARCH_PENDING`
- `CONVERSATION_CONFLICT`
- `PATH_OUTSIDE_PROJECT`
- `SENSITIVE_CONTENT_DETECTED`
- `UNSUPPORTED_ARTIFACT_TYPE`
- `ARTIFACT_QUOTA_EXHAUSTED`
- `ARTIFACT_GENERATION_FAILED`
- `ARTIFACT_NOT_READY`

錯誤訊息必須附下一個可執行動作，不可只回傳 generic failure。

---

## 9. Skill 規劃

## 9.1 Skill 的工作

Skill 不負責 Notebook API；它負責教 Agent：

1. 如何發現 Project Brain。
2. 什麼情況應主動詢問。
3. 什麼情況應先讀本地程式碼。
4. 何時應研究外部資料。
5. 何時應建立同步／記憶 Plan。
6. 哪些操作需要核准。
7. 如何解讀 NotebookLM 回答與引用。
8. NotebookLM 已原生提供哪些 source-grounded artifacts，並在適合時優先委派而不是重新造輪子。

---

## 9.2 Skill 觸發條件

除了使用者明確提到 NotebookLM，還應在下列 intent 啟動：

- 缺少專案背景。
- 不理解歷史決策或架構理由。
- 使用者說「之前決定」、「原本為什麼」、「找回上下文」。
- Agent 接手其他 Agent 的工作。
- Conversation context 疑似被截斷。
- 即將修改核心架構、資料模型或長期政策。
- 需要最新官方文件、標準、規格或重要論文。
- 需要把長期文件、ADR、postmortem 或 handoff 保存到專案知識庫。
- 使用者要求同步、整理或管理專案文件。
- 使用者要求簡報／presentation／slide deck、Podcast／audio overview、資訊圖、資料表、報告、心智圖、測驗、flashcards 或影片摘要。
- Agent 準備自行撰寫大量 source summarization、PPT、音訊、圖解或報告生成程式前，應先檢查 NotebookLM capabilities。

---

## 9.3 Agent 決策順序

Skill 應明確要求：

```text
1. 先檢查本地程式碼／文件能否直接回答。
2. 若問題涉及歷史、跨文件脈絡或失去上下文，呼叫 Project Brain。
3. 若 Project Brain 來源未涵蓋，標示缺口。
4. 先判斷需求是在解釋「專案本身」、「外部研究」，或兩者混合；呼叫 `brain_grounding_check` 驗證 Notebook source coverage。
5. 若缺少專案 overview、architecture、current status 或 decisions，先建立 onboarding／sync plan，不能用外部研究資料冒充專案內容。
6. 若需要外部最新資料，建立 research preview。
7. 對 NotebookLM 的答案，回到本地 repository 驗證現況。
8. 若使用者要的是 NotebookLM 已原生支援的內容成品，先呼叫 `brain_capabilities` 並提出 artifact plan，不自行重建生成管線。
9. 只有長期、穩定、可檢索的成果才建立 writeback plan。
```

---

## 9.4 Agent 自動執行與需確認的行為

### 可自動執行

- `brain_discover`
- `brain_status`
- `brain_health`
- `brain_capabilities`
- `brain_grounding_check`
- `brain_onboarding_plan`
- `brain_ask`
- `brain_recover`
- `brain_sync_scan`
- `brain_sync_plan`
- `brain_remember_plan`
- 查詢 research status

### 預設先確認

- 建立／接管 Notebook。
- 啟動長時間 Deep Research。
- 匯入研究來源。
- 上傳或替換本地文件。
- 寫回 session memory。
- 刪除／retire 來源。
- rebind Notebook。
- 啟動任何 Studio artifact generation。
- 將 artifact 下載到本地檔案系統。
- 修改 `AGENTS.md` 或客戶端 MCP config。

可由使用者在 manifest 將部分操作設為 auto，但 secrets、刪除與 rebind 不得無確認自動進行。

---

## 9.5 Project-local Skill 安裝

`notebooklm-brain init` 應偵測相容客戶端，顯示將建立的檔案，並只寫入使用者核准的 target。

不得：

- 覆寫既有 Skill。
- 整份覆寫 `AGENTS.md`。
- 假設所有 Agent 共用相同 skill directory。

若需要修改 `AGENTS.md`，使用具 marker 的最小區塊：

```markdown
<!-- notebooklm-project-brain:start -->
本專案已設定 Project Brain。需要歷史決策、上下文恢復或外部研究時，先使用 Project Brain MCP；NotebookLM 回答仍須與本地程式碼及測試核對。
<!-- notebooklm-project-brain:end -->
```

---

## 9.6 專門 Skill：Project Explainer／Karpathy Explain

### 定位

在基礎 `notebooklm-project-brain` Skill 之外，建立一個專門負責「把專案或複雜輸出轉成容易理解形式」的 orchestration Skill。

建議正式功能名稱：

```text
project-explainer
```

可提供較容易記憶的 alias／preset：

```text
karpathy-explain
```

正式名稱使用功能描述，避免把產品能力綁死在單一人物名稱；preset 則保留「不要只寫更多文字，改用圖解、簡報、Podcast、互動頁面或 explainer video」的使用理念。

### 依賴

此 Skill 不直接實作 NotebookLM API，依賴：

- `.notebooklm/brain.json`
- Project Brain MCP
- `brain_health`
- `brain_grounding_check`
- `brain_onboarding_plan`
- `brain_capabilities`
- `brain_artifact_plan/generate/status/download`

### 強制前提

完整「專案解釋」必須滿足：

```text
manifest exists
AND authentication healthy
AND notebook accessible
AND grounding status == project_ready
AND required project sources are fresh
```

僅有 Notebook ID、來源數量很多，或 Deep Research 已完成，都不能取代 `project_ready`。

預設 required roles：

- `project_overview`
- `architecture`
- `current_status`
- `decision`

依任務可增加：

- `runbook`
- `handoff`
- 特定模組／API 文件
- `external_research`

### 執行流程

```text
使用者要求「解釋這個專案／功能／模型輸出」
        ↓
brain_discover + brain_health
        ↓
分類 scope：project／module／research／mixed
        ↓
brain_grounding_check
   ┌────┴──────────┐
 coverage 不足      project_ready
   ↓                ↓
brain_onboarding_plan  brain_capabilities
或 brain_sync_plan     ↓
   ↓                選擇最適合的解釋形式
核准並同步後重試       ↓
              brain_artifact_plan
                       ↓
                使用者確認後生成
```

### 輸出模式

| Mode | 使用時機 | 執行方式 |
|---|---|---|
| `plain` | 快速、清楚的文字解釋 | NotebookLM chat／report；可要求接近 ASD-STE100 的簡明風格 |
| `slides` | 專案介紹、architecture walkthrough | NotebookLM slide deck |
| `podcast` | 通勤／語音理解 | NotebookLM audio overview |
| `infographic` | 一頁視覺摘要 | NotebookLM infographic |
| `table` | 比較、規格、狀態整理 | NotebookLM data table |
| `mind-map` | 概念與模組關係 | NotebookLM mind map |
| `video` | 一般 source-grounded explainer | NotebookLM video overview |
| `interactive-web` | 客製互動解釋 | NotebookLM 先產內容架構／腳本，再交 Coding Agent 實作 HTML |
| `bespoke-animation` | 高度客製動畫 | NotebookLM 先做 research／storyboard，交專門影片工具實作 |

### 自動選擇規則

使用者沒有指定 format 時，Skill 可以提出 1–3 個建議，但不能在未確認前啟動長時間 artifact generation。

例如：

```text
這是跨模組架構問題。建議：
1. Mind map：先看模組關係（推薦）
2. Slide deck：適合團隊 walkthrough
3. Podcast：適合非同步理解
```

### Coverage 不足時的行為

- `research_only`：拒絕命名為 Project Explainer；可改做「相關技術研究概覽」。
- `project_partial`：列出缺少的 source roles，先建立 onboarding／sync plan。
- `project_stale`：先同步關鍵文件。
- `unknown`：不猜測，要求完成 health／coverage 檢查。

不得用一句普通 warning 後繼續產生看似正式的專案 artifact。任何降級都必須改變標題與 scope metadata。

### Token／成本原則

- Skill 本身保持短小，只保存觸發、前提與 routing。
- NotebookLM 詳細 capabilities 由 MCP 動態取得。
- 不把完整來源全文搬進 Coding Agent context。
- Artifact 只回傳 ID、狀態、摘要、來源清單與下載位置。
- 優先使用使用者既有 NotebookLM 額度，但清楚揭露 quota，不宣稱免費即無限。

---

## 10. Librarian 與來源同步設計

## 10.1 Upload Gate

每個候選文件依序通過：

1. **Stability**：一週內是否即將被取代。
2. **Retrievability**：未來是否會用自然語言查詢它。
3. **Irreplaceability**：是否已存在於 Notebook，或可直接由程式碼／Git 推導。
4. **Signal-to-noise**：可被有效引用的內容比例是否足夠。
5. **Sensitivity**：是否包含 credential、秘密、個資或不應離開本機的內容。

結果：

- `UPLOAD`
- `WAIT`
- `SKIP`
- `CURATE_FIRST`
- `MERGE`
- `BLOCK_SENSITIVE`

現有 `references/source-upload-criteria.md` 可作為初始政策來源，但必須轉成正式、測試覆蓋的產品規則。

---

## 10.2 來源 identity

本地文件來源不能再只用 title 判斷同一性。至少需要：

- repository ID。
- relative path。
- content SHA256。
- backend source ID。
- source kind。
- last synced commit。
- last synced timestamp。
- previous backend source ID（替換時）。
- policy decision。

標題相同但內容不同，不能直接視為已同步。

---

## 10.3 本地文字文件更新

NotebookLM pasted text source通常無原生 refresh；更新流程應採：

1. 上傳新版來源。
2. 等待 ready。
3. 驗證 hydration。
4. 將新版設為 active／pinned。
5. 舊版標記 superseded。
6. 只有明確核准才 retire 舊版。

不可先刪舊版再上傳新版。

---

## 10.4 Binary 與其他來源

優先重用 `notebooklm-py` 已支援的 PDF、DOCX、EPUB、圖片、音訊、影片與 URL 上傳能力。Project Brain 層負責：

- 路徑與政策。
- hash。
- provenance。
- plan／approval。
- registry reconciliation。

不要在本專案重新實作檔案解析或 NotebookLM transport。

---

## 10.5 Source Hydration Quality Gate

來源進入 ready 不代表內容正確。至少需檢查：

- fulltext 是否非空。
- 是否為 403／503／登入／驗證錯誤頁。
- 標題與內容是否合理。
- 內容長度是否異常。
- 是否與預期檔案 hash／摘要對得上（能驗證時）。

失敗時：

- 不更新 registry 為成功。
- 不 retire 舊來源。
- 保存 evidence。
- 回傳可操作錯誤。

---

## 10.6 Notebook／Source Capacity Guard

### 問題

NotebookLM 對每位使用者可建立的 Notebook 數量，以及每本 Notebook 可加入的來源數量都有上限。Project Brain 若只呼叫新增來源、卻沒有在新增前後核對容量與 backend snapshot，使用者可能持續提交文件，卻不知道新來源實際上沒有進入 Notebook。

目前本專案的 wrapper 沒有正式的 capacity preflight／warning／blocking contract。現有新增流程通常會在 backend exception 或 ready verification 失敗時中止，因此不能視為「已知會無聲成功」；但它也沒有主動顯示 used／limit／remaining、沒有在 Plan 階段預測容量，也沒有把 quota error 統一轉成清楚的產品訊息。這是 Project Brain 上線前必須補上的 P0 項目。

### Google 官方目前公布的 consumer limits

依 Google 官方 Help Center「Learn about Gemini Notebook’s plans」（查核日期：2026-10-13；官方註明 limits subject to change）：

| Plan | Notebooks | Sources per notebook |
|---|---:|---:|
| Standard／免費 | 100/user | 50/notebook |
| Google AI Plus | 200/user | 100/notebook |
| Google AI Pro | 500/user | 300/notebook |
| Google AI Ultra 20 TB | 500/user | 500/notebook |
| Google AI Ultra 30 TB | 500/user | 600/notebook |

官方來源：

- <https://support.google.com/gemininotebook/answer/16213268?hl=en>
- <https://support.google.com/gemininotebook/answer/17670842?hl=en>

補充限制：

- Google 明確說明 limits 可能變更，因此不能只把上述表格永久 hard-code 成唯一真相來源。
- 分享 Notebook 不會提高任何協作者的 per-notebook source limit。
- Workspace／Enterprise 可能有不同 entitlement；不能只依 consumer plan 名稱猜測。
- AI prompt／generation usage limit 是另一種 compute quota，與固定的 source capacity 不可混為一談。

### 可用的 live limit 訊號

目前使用的 `notebooklm-py 0.8.1` 已公開提供：

```python
limits = await client.settings.get_account_limits()
limits.notebook_limit
limits.source_limit
limits.tier
```

其 MCP `server_info(include_account=True)` 也能回傳 `notebook_limit`、`source_limit` 與 opaque `tier`。本企劃在 2026-10-13 已以真實 authenticated session 確認這些欄位可以回傳實際 account limits。

因此正式策略不是只靠靜態表格推算，而是：

1. **第一優先：live server-advertised limit。**
2. **第二優先：使用者明確設定的 plan／limit override。**
3. **最後 fallback：官方 Standard 最保守值，並清楚標示為估算值。**
4. 若 policy 不允許估算，回傳 `SOURCE_LIMIT_UNKNOWN` 並停止會增加來源的 Apply。

`tier` 是 opaque enum，不得以數字大小比較方案高低；實際 capacity 直接使用 `source_limit`／`notebook_limit`。

### Source count 真相來源

容量計算必須使用即時 backend `list_sources(notebook_id)`，不能只用本機 Source Registry，因為：

- 其他使用者或 Agent 可能直接在 NotebookLM 新增來源。
- timeout 後可能已有來源成功建立但本機尚未 commit。
- 失敗的 file upload 可能留下 `preparing` row，而且仍占 source quota。
- Registry 可能因 crash、舊版本或手動操作而落後。

最保守的 used count 應計入 backend 回傳的所有 source rows，包括 ready、processing、preparing、error 及 unknown；只有已由 backend 確認不存在的來源才不計入。

2026-10-13 的 live read-only audit 已實際發現既有 Advisor 的本機 Registry 與 Notebook backend source count 不一致（例如本機記錄 2、backend 實際 12；本機記錄 17、backend 實際 29）。這證明 Registry 只能作為管理紀錄，不能作為容量權威來源。

### Plan 階段容量公式

每一個會增加來源的 Plan 必須計算：

```text
current_used       = len(await backend.list_sources(notebook_id))
planned_additions  = 本次可能建立的新 backend source rows
peak_used          = current_used + planned_additions
remaining_after    = source_limit - peak_used
```

即使 Plan 同時打算 retire 舊來源，也不能先從 `peak_used` 扣除 retirements，因為安全流程是 add-before-delete。容量必須足以容納「舊版與新版短暫同時存在」的峰值。

如果 `peak_used > source_limit`：

- Plan 標記 `blocked_capacity`。
- Apply 不得發出 add/import RPC。
- 清楚顯示目前數量、上限、需要的空間與超出數量。
- 提供選項：審查並 retire 不需要的來源、建立新的 Notebook／archive brain，或升級方案。

如果 Notebook 已滿，系統不能假裝 add-before-delete 仍可進行。若使用者選擇先刪來源釋放空間，必須走獨立、明確核准且已備份的 capacity-recovery plan；不得在一般 sync apply 中暗中改成 delete-before-add。

### Warning thresholds

預設狀態：

| 使用率 | 狀態 | 行為 |
|---:|---|---|
| `< 80%` | `healthy` | 正常顯示 used／limit／remaining |
| `80–89%` | `warning` | 每次 status／plan 明確提醒 |
| `90–99%` | `critical` | 強烈提醒並建議先整理來源 |
| `100%` | `exhausted` | 阻擋所有會增加來源的操作 |
| planned peak `> 100%` | `blocked_capacity` | Plan 不可 apply |

閾值可配置，但「超過 live limit 必須阻擋」不可關閉。

### Preflight 與 postflight 雙重驗證

每次 `source-add-*`、research import、sync apply、remember apply 都必須：

1. 在建立 Plan 時取得 live limit 與 backend source count。
2. 在 Apply 前重新取得一次，防止 Plan 後被其他人占用容量。
3. 記錄 baseline source IDs，而不只記 count。
4. 執行新增。
5. 再次 `list_sources`。
6. 驗證預期的新 source ID 真正出現且進入 ready。
7. 只有驗證成功才更新 Registry／run 為 completed。

如果 RPC 沒有報錯，但 backend snapshot 沒有預期 delta：

- 回傳 `SOURCE_ADD_NOT_COMMITTED`。
- Operation 狀態為 failed／needs_reconciliation。
- 絕不顯示成功。
- 絕不把來源寫入本機 Registry 假裝存在。

### 對使用者與 Agent 的輸出

`brain_status`、`brain_health`、`brain_sync_plan` 與所有 Apply 結果應包含：

```json
{
  "source_capacity": {
    "used": 47,
    "limit": 50,
    "remaining": 3,
    "planned_additions": 2,
    "peak_used": 49,
    "utilization": 0.94,
    "status": "critical",
    "limit_source": "live_server",
    "tier": 1,
    "preparing_orphans": 0
  }
}
```

Agent Skill 必須要求：

- `warning`／`critical` 不得省略不報。
- `exhausted`／`blocked_capacity` 時直接告訴使用者「新增不會執行」，而不是繼續嘗試。
- 不建議使用者盲目刪除；先列出可合併、被取代、低品質與 orphaned sources，再建立 reviewed cleanup plan。

### Notebook count guard

`brain init` 建立新 Notebook 前也應讀取 live `notebook_limit`，計算目前使用者擁有的 Notebook 數量。若已達上限：

- 不呼叫 create。
- 建議接管既有 Notebook、整理舊 Notebook，或升級方案。
- 不把 shared Notebook 錯算為使用者擁有的 Notebook；若 ownership 無法可靠判定，狀態應標示 unknown，並以 backend create failure 作最終權威拒絕。

---

## 10.7 Project Grounding Coverage Gate

### 為什麼來源很多仍可能不是 Project Brain

NotebookLM 只會根據實際加入的來源回答。如果一本 Notebook 只有：

- 官方技術文件。
- 外部論文。
- 市場研究。
- 競品資料。
- 某項技術的教學。

它可以很好地解釋研究主題，但不一定知道目前 Repository 的：

- 真正產品目標。
- 現行架構。
- 主要模組。
- 已確認決策。
- 現在進度。
- 不得違反的限制。
- 已知問題與下一步。

因此「Notebook 裡有來源」不等於「Notebook 能解釋專案」。如果 Agent 要製作專案簡報、Podcast 或 explainer，卻只選到 external research sources，成品會變成研究主題介紹，而不是專案介紹。這是語意錯誤，不只是內容不完整。

### Source roles

每個已管理來源都應具有明確角色：

| Source role | 用途 |
|---|---|
| `project_overview` | README、PRD、產品目標與使用者價值 |
| `architecture` | 架構圖、模組責任、資料流與邊界 |
| `current_status` | 現在完成度、正在進行事項與已知缺口 |
| `decision` | ADR、重大決策、取捨與被否決方案 |
| `runbook` | 操作、部署、維護與故障處理 |
| `handoff` | 經整理的開發交接與下一步 |
| `external_research` | 官方文件、論文、市場與競品研究 |
| `reference` | 補充規格、術語與背景資料 |

一個來源可以有多個角色，但不能只因 title 像專案文件就自動視為 canonical；需要 path、provenance、hash 及 policy evidence。

### Project readiness states

| 狀態 | 定義 | 可做什麼 |
|---|---|---|
| `research_only` | 只有 external research／reference，沒有足夠專案來源 | 只能回答研究問題，不得聲稱解釋專案 |
| `project_partial` | 有部分專案文件，但 required roles 缺漏 | 可回答有來源部分，專案 artifact 前需補齊 |
| `project_ready` | required project roles 齊全且未過期 | 可產生專案問答與 artifacts |
| `project_stale` | 曾完整但關鍵文件落後目前 Git／狀態 | 先同步再產生正式專案解釋 |
| `unknown` | 無法驗證來源角色或新鮮度 | 顯示不確定，預設不產生正式專案 artifact |

來源數量不能取代 readiness 判斷。50 份論文仍可能是 `research_only`；4 份高品質 canonical docs 反而可能足以達成 `project_ready`。

### 初始化時的最小專案來源集合

`brain init` 不應只建立空 Notebook 或加入研究來源。它必須先執行 `brain_onboarding_plan`，尋找：

1. Project overview：README／PRD／產品說明。
2. Architecture：架構文件、模組圖、資料流或 API 邊界。
3. Current status：最新 roadmap、status、release state 或 handoff。
4. Decisions：ADR、正式決策或清楚記錄的取捨。

可選但常有價值：

- Runbook。
- Troubleshooting guide。
- Security／privacy constraints。
- Domain glossary。
- 近期穩定的 postmortem。

如果 Repository 沒有這些文件，Agent 不應直接把整個 source tree 上傳。它應：

1. 讀取本地程式碼與 Git。
2. 產生一份有 provenance、對應 commit 的 Project Dossier 草稿。
3. 清楚標示哪些內容是程式碼事實、哪些是推論。
4. 讓使用者審查。
5. 核准後才上傳成 canonical project source。

### 問答與 Artifact 前置檢查

在下列 intent 前強制執行 coverage check：

- 「解釋這個專案」。
- 「為這個專案做簡報／Podcast／影片／資訊圖」。
- 「目前做到哪裡」。
- 「為什麼採用這個架構」。
- 「讓下一個 Agent 接手」。

判斷流程：

```text
辨識 requested scope
        ↓
列出所需 source roles
        ↓
比對 Notebook source inventory + freshness
        ↓
完整 → 繼續 ask／artifact plan
缺漏 → 先 onboarding／sync plan
只有研究資料 → 標示 research_only，禁止冒充 project explanation
```

### 不允許的無聲降級

系統不得：

- 使用 external research sources 生成內容，卻把標題寫成「本專案架構」。
- 在缺少 current status 時，根據舊架構文件猜測現況。
- 因 NotebookLM 生成成功，就宣稱 grounding scope 正確。
- 只顯示總 source count，不顯示 project／research source composition。

若使用者選擇在 coverage 不足時繼續，輸出必須明確改名，例如：

- 「相關技術研究概覽」。
- 「依現有外部來源製作的背景簡報」。
- 「不包含目前專案實作的初步說明」。

---

## 11. Context Recovery 與記憶寫回

## 11.1 Recovery 不是一般摘要

`brain_recover` 必須固定回答：

1. 專案主要目標。
2. 目前完成狀態。
3. 已確認決策。
4. 不得違反的限制。
5. 最近實質變更。
6. 未完成工作。
7. 已知風險與資料過期警告。
8. 下一個可驗證步驟。
9. 每項資訊的來源。

---

## 11.2 Writeback 文件格式

建議生成：

```markdown
# Project Brain Handoff

## Scope

## Completed

## Confirmed decisions

## Rejected alternatives

## Constraints

## Evidence and verification

## Open questions

## Recommended next step

## Provenance
- Repository:
- Git commit:
- Related files:
- Generated at:
```

### 禁止事項

- 不把模型推測寫成 confirmed decision。
- 不聲稱測試通過，除非有實際輸出。
- 不保存 secrets。
- 不用 Notebook 記憶替代 Git commit 或正式文件。
- 不把所有 session 都寫回；沒有長期價值時應跳過。

---

## 12. 多 Agent 與 Conversation 設計

目前以刪除「目前 conversation」實現 fresh query，不適合作為多 Agent 預設。

Project Brain MCP 必須：

1. 不依賴共享 current notebook context。
2. 每次呼叫使用完整 Notebook ID。
3. 保存每個 Agent／task 的 conversation ID。
4. 不因另一個 Agent 要獨立問題而刪除共享 conversation。
5. 對 conversation conflict 回傳 typed error。
6. 將 durable knowledge 寫入來源／note 前先整理與核准，不把 chat history 當 durable state。

若 NotebookLM backend 無法真正平行隔離 conversation，MVP 必須序列化 Ask 或使用明確的新 conversation 策略，不能假裝已隔離。

---

## 13. 安全與隱私

### 13.1 Credential

- Credential 只由 `notebooklm-py` profile／storage 管理。
- MCP 不回傳或記錄 cookie 值。
- `brain.json` 不含 credential。
- Debug log 必須遮蔽 auth header、cookie、token 及本地秘密。

### 13.2 Path safety

- 所有 project-relative path 必須解析後仍位於 project root。
- 預設拒絕 symlink escape。
- 拒絕 `../` traversal。
- 不掃描 `.git`、virtualenv、node_modules、build、dist 等預設噪音目錄。

### 13.3 Secret detection

在同步 Plan 前檢查常見：

- `.env`。
- private key。
- API token。
- cookie／session。
- cloud credentials。
- database DSN。
- credential JSON。

偵測到敏感內容時預設阻擋，而不是只警告後繼續。

### 13.4 Notebook ID

Notebook UUID 不是登入憑證，通常可提交；但取得 ID 不代表取得存取權。所有 backend 操作仍需 Google authentication 與 Notebook share permission。

---

## 14. 現有能力重用

以下現有能力應直接重用：

| 現有能力 | 新架構用途 |
|---|---|
| `setup` | `brain init` 的 create/adopt backend |
| `list-advisors` | discovery／diagnostic |
| `update-config` | 更新 Project Brain Persona／Research Profile |
| `source-add-url` | URL source apply |
| `source-add-file` | 初期文字來源加入；後續需補 hash/update contract |
| `ask` + citations | `brain_ask` 核心 |
| `preview` | `brain_research_preview` 核心 |
| `plan-apply`／`apply` | research safe apply |
| `refresh-plan`／`refresh-apply` | URL／Drive refresh |
| `export` | `brain_export` |
| `AdvisorStore` | durable runtime state |
| `notebooklm-py` | NotebookLM transport、auth、binary sources、MCP 基礎能力 |

不應直接重用：

- Legacy `scripts/` browser automation。
- `data/library.json`。
- 舊 Project／Research notebook pair 假設。
- 依 title 判斷本地文件未變更的現行做法。

---

## 15. CLI 規劃

MCP 之外仍保留 CLI，方便初始化、故障排查及不支援 MCP 的 Agent。

建議入口：

```text
notebooklm-brain init
notebooklm-brain discover
notebooklm-brain status
notebooklm-brain doctor
notebooklm-brain ask
notebooklm-brain recover
notebooklm-brain capabilities
notebooklm-brain artifact plan|generate|status|download
notebooklm-brain research preview|status|plan|apply
notebooklm-brain sync scan|plan|apply
notebooklm-brain remember plan|apply
notebooklm-brain rebind
notebooklm-brain export
notebooklm-brain install --scope user
notebooklm-brain uninstall
```

CLI 與 MCP 必須呼叫相同 service layer，不能形成兩套邏輯。

---

## 16. 實作階段

## Phase 0：整理與凍結現有基線

### 工作

- 整理目前未提交的 Ask-only、`list-advisors`、`update-config`、ad-hoc query 變更。
- 將產品文件、實驗產物及 runtime artifact 分類。
- 更新 `docs/current-status.md` 的測試數字與未發布狀態。
- 建立乾淨 commit 與明確版本基線。
- 在任何新 Project Brain source mutation 上線前，先為現有 `source-add-url`、`source-add-file`、research apply 補上共用 Capacity Guard：live limit、backend count、preflight、postflight 及 typed error。
- 讓現有 `show`／新 `status` 同時揭露 Registry count 與 backend authoritative count；兩者不一致時明確標示 drift。

### 驗收

- Git working tree 可辨識，不把實驗資料混入產品 release。
- 全量 pytest PASS。
- Ruff PASS。
- 現有 live 能力不回歸。
- Source 已滿或 planned peak 超限時，現有新增入口在 RPC 前 fail closed。
- 新來源未出現在 backend snapshot 時，不得回報成功或寫入 Registry。
- Local Registry 與 backend count 不一致時，使用者可直接看到差異。

---

## Phase 1：Project binding 與 `brain init`

### 工作

- 定義 manifest schema。
- 實作 project root discovery。
- 實作 create/adopt/rebind。
- 實作 Advisor state hydration。
- 實作 `brain discover/status/doctor`。
- 實作初始 `brain_onboarding_plan` 與 project readiness classification。
- Project scope 為預設；user scope 選配。

### 驗收

- Project A、B 各自綁定不同 Notebook，不能交叉。
- 無 manifest 時不能使用最近 Notebook。
- clone 到新環境可驗證 access 並 hydration。
- 完整 UUID 在所有操作中明確傳遞。
- 只有外部研究來源時必須顯示 `research_only`，不能顯示 Project Brain ready。

### 預估產品完成度

約 55–60%。

---

## Phase 2：Read-only Project Brain MCP + Skill

### 工作

- 建立 Project Brain MCP server。
- 實作 `brain_discover/status/health/capabilities/grounding_check/ask/recover`。
- 建立 project-local Skill installer。
- 定義基礎 Skill triggers、local-first policy 與引用規則。
- 建立 `project-explainer` 專門 Skill skeleton 與 `karpathy-explain` preset；完整 artifact execution 由 Phase 5 接通。
- 實作不刪除共享 conversation 的 query strategy。

### 驗收

- 相容 Agent 進入專案後能自動發現大腦。
- 使用者不必再提供 Advisor ID／Notebook ID。
- 上下文遺失測試可取得具引用 recovery output。
- Notebook 回答與本地現況驗證責任清楚分離。
- Agent 能發現 NotebookLM 原生 artifact capabilities，不需把完整 provider 手冊永久塞入 Skill context。
- 專案問答與 artifact 前會驗證 required project source roles；coverage 不足時先提出 onboarding／sync plan。
- `project-explainer` 在 `research_only`／`project_partial`／`project_stale` 狀態不會直接產生正式專案解釋。

### 預估產品完成度

約 70%。

---

## Phase 3：Librarian Scan／Sync

### 工作

- 檔案 inventory、path、SHA256、Git provenance。
- Source role classification 與 project／research composition。
- Upload Gate。
- sensitive content detection。
- sync scan／plan／apply。
- 文字與 binary source 支援。
- 本地文件新版 add-before-retire。
- Source Hydration Quality Gate。
- Live account limit lookup 與官方 conservative fallback。
- Source capacity warning／critical／exhausted 狀態。
- Plan-time peak capacity 與 apply-time preflight。
- Post-add backend snapshot verification，禁止無聲成功。

### 驗收

- 同 title 但內容改變必須被偵測。
- unchanged 文件不得重複上傳。
- raw logs 與 secrets 預設被拒絕。
- stale plan 不得 apply。
- 新來源未 ready／hydration 失敗時舊來源不得刪除。
- Backend source count 已滿時，不得發出新增 RPC，且使用者收到 used／limit／remaining。
- Replacement 的 peak count 必須以 add-before-delete 計算，不能先扣 retirement。
- RPC 回傳但 source snapshot 無預期新增時，結果不得標記成功。
- `preparing` orphan 必須計入 quota 並在 health/status 顯示。
- `project_overview`、`architecture`、`current_status`、`decision` 缺漏時 readiness 不得為 `project_ready`。
- Project Dossier 若由程式碼推導，必須附 commit provenance、區分事實與推論並經審查。

### 預估產品完成度

約 80–83%。

---

## Phase 4：Remember／Handoff 閉環

### 工作

- `brain_remember_plan/apply`。
- 標準 handoff schema。
- Git commit／related files provenance。
- 無長期價值時的 skip 路徑。
- `brain_recover` 使用最近 handoff 與正式來源。

### 驗收

- 一個 Agent 完成工作後，另一個全新 Agent 可從大腦恢復方向。
- raw conversation 不會被直接保存。
- 未驗證推測不會被標記為 confirmed decision。

### 預估產品完成度

約 87–90%。

---

## Phase 5：Research 與 Studio Artifact MCP 完整閉環

### 工作

- research preview／status／resume。
- candidate review plan。
- approved import。
- 官方文件／論文偏好規則。
- `brain_artifact_plan/generate/status/download`。
- NotebookLM artifact capability／format discovery。
- artifact source selection、provenance、quota／long-running operation handling。
- 通知與長時間任務 handoff。

### 驗收

- Agent 可以在知識缺口時提出研究，而不是直接猜測。
- Preview 不改來源。
- timeout 後不建立重複 task。
- 只有選定來源被匯入。
- 使用者要求簡報、Podcast、資訊圖、資料表、報告、心智圖、測驗或影片時，Agent 會先提出 NotebookLM artifact plan，而不是直接重造生成系統。
- Generate 只啟動一次並立即回傳 task／artifact ID；status 不重複生成。
- Download 不覆寫既有檔案，且大型 artifact 不回灌整份 Agent context。
- 免費／付費方案與 usage limit 清楚揭露，不宣稱免費即無限制。

### 預估產品完成度

約 90–92%。

---

## Phase 6：多 Agent、排程與通知

### 工作

- per-agent conversation identity。
- operation locks／leases。
- auth refresh。
- optional scheduled scan／refresh。
- source drift／capacity／failure notification。
- metrics 與 audit records。

### 驗收

- 兩個 Agent 同時查詢不會刪除彼此 conversation。
- 同一 sync plan 不會重複 apply。
- 排程失敗不會造成來源刪除或狀態假成功。

### 預估產品完成度

約 93–95%。

---

## Phase 7：Release、跨客戶端支援與文件

### 工作

- project-local install matrix。
- user-scope fallback。
- Claude／Agent Skills／MCP 相容文件。
- migration guide。
- package version與 release notes。
- end-to-end onboarding tutorial。

### 驗收

- 新使用者可只依 README 完成單一專案初始化。
- 不要求預先全域安裝。
- 不同 scope 的檔案與副作用清楚顯示。
- uninstall 不刪除 Notebook 或專案知識，除非另行明確確認。

---

## 17. 必須通過的端到端案例

### E2E-01：單一專案初始化

- 在沒有 Project Brain 的 Repository 執行 `init`。
- 建立 Notebook、manifest、Skill／MCP config。
- 第一次 scan 不直接上傳。
- 核准後同步來源。

### E2E-02：接管既有 Notebook

- 採用完整 Notebook ID。
- 不建立重複 Notebook。
- 既有來源登記為 active，不自動 pin／delete。

### E2E-03：兩個專案隔離

- A、B 使用不同 Notebook。
- 從 A 呼叫時永遠不能命中 B。
- 不依賴最近使用 Notebook。

### E2E-04：上下文遺失恢復

- 啟動全新 Agent session。
- 只有 Repository 與 manifest。
- `brain_recover` 回傳目標、決策、限制、下一步與引用。

### E2E-05：文件修改同步

- 上傳 `docs/ARCHITECTURE.md` v1。
- 修改成 v2，檔名不變。
- scan 必須偵測 content hash 改變。
- add v2 成功前不得 retire v1。

### E2E-06：開發 log 管理

- 提供 raw terminal log。
- Upload Gate 拒絕直接上傳。
- 產生 curated handoff 草稿。
- 核准後只上傳整理後文件。

### E2E-07：外部研究

- Agent 發現來源未涵蓋最新 API。
- 建立 research preview。
- timeout 後 resume。
- 僅匯入核准官方來源。

### E2E-08：Secrets 防護

- 候選文件含 API key／private key。
- Plan 必須 block。
- Notebook source count 不變。

### E2E-09：無權限 Notebook

- manifest ID 存在，但目前帳號沒有存取權。
- 回傳 access denied 指引。
- 不建立新 Notebook，不改 manifest。

### E2E-10：多 Agent

- Agent A、B 同時 ask。
- 兩者 conversation 不互相刪除。
- 同一 apply digest 最多 commit 一次。

### E2E-11：Source capacity 與無聲失敗防護

- Fake／live limit 分別設定為 50、100、300、500、600。
- 在 80%、90%、100% 時驗證 warning／critical／exhausted。
- 49/50 來源時，包含 2 additions 的 Plan 必須 blocked。
- 50/50 時所有新增入口在 RPC 前被阻擋。
- 48/50 且 replace 2 個來源時，peak 仍為 50；不能因預計 retirement 而低估。
- 模擬 add RPC 無例外但 source snapshot 不變，操作必須回傳 `SOURCE_ADD_NOT_COMMITTED`。
- `preparing` orphan 必須算入 used count。
- live limit 不可用時，清楚標示 fallback／unknown，不能默認成無上限。

### E2E-12：NotebookLM 原生 Artifact 重用

- 使用已同步來源提出「製作簡報」，Agent 選擇 slide deck 而非自行產生 PPT pipeline。
- 使用者要求 Podcast 時選擇 audio overview，並在啟動前提示 quota／時間。
- 使用者要求圖表時，Agent能區分 infographic、data table、mind map，而不是宣稱 NotebookLM 有不存在的任意 chart engine。
- generation 回傳 task ID 後不在主流程高頻 polling。
- 完成後只回傳 metadata／摘要，使用者確認後才下載。
- capability 不支援或 quota exhausted 時回傳 typed error 並提供替代方案，不假裝成功。

### E2E-13：研究來源不能冒充專案來源

- 建立只含官方文件與論文的 Notebook，狀態必須為 `research_only`。
- 要求「解釋這個專案」時回傳 `PROJECT_GROUNDING_INSUFFICIENT` 或 onboarding plan。
- 加入 project overview 但缺 architecture／current status／decisions 時，狀態為 `project_partial`。
- required roles 齊全且 freshness 通過後，狀態才可為 `project_ready`。
- 在 `research_only` 狀態要求專案簡報時，不能直接產生標題為專案簡報的 artifact。
- 使用者明確要求繼續時，輸出名稱必須降級為外部研究／背景概覽並揭露缺少專案實作來源。

### E2E-14：Project Explainer 專門 Skill

- `project_ready` 專案要求「幫我理解這個專案」時，Skill 先檢查 coverage，再提出適合的 plain／slides／podcast／infographic／mind-map 選項。
- 使用者未指定 format 時只提出建議，不直接啟動長時間 generation。
- 選擇 slides 後，Skill 透過 NotebookLM artifact tools 生成，不建立自製 PPT pipeline。
- 選擇 interactive web 時，NotebookLM 只負責內容架構／腳本，實際 HTML 交 Coding Agent。
- `research_only` 狀態不得通過完整 Project Explainer precondition。
- `project_stale` 狀態必須先建立 sync plan。

---

## 18. 測試策略

### 18.1 Offline tests

- Manifest schema／discovery。
- path containment／symlink。
- Upload Gate。
- secret detection。
- hash inventory。
- plan digest。
- stale plan。
- source reconciliation。
- account limit parsing、fallback 與 tier opaque mapping。
- capacity thresholds、peak calculation 與 post-add delta verification。
- capability discovery、artifact routing、generation idempotency 與 download no-clobber。
- source-role coverage、readiness state、staleness 與 research-only blocking。
- MCP tool schema與 typed errors。
- Skill installation no-clobber。
- multi-project isolation。

### 18.2 Contract tests

- CLI 與 MCP 呼叫相同 service 結果。
- Project Brain MCP 對 backend capabilities 正確 fail closed。
- Notebook ID 每次明確傳入。
- credential 不進 output／log／state。

### 18.3 Live smoke

只使用 disposable 或專用測試 Notebook：

- init create/adopt。
- text／binary source upload。
- ask with citations。
- recover。
- modified file replacement。
- deep research preview/resume。
- one disposable artifact plan/generate/status/download flow（在 quota 與使用者 Gate 允許時）。
- cleanup evidence。

### 18.4 Release gate

- 支援 Python 版本全量測試。
- Ruff PASS。
- package build/install PASS。
- project scope clean-room onboarding PASS。
- user scope optional onboarding PASS。
- migration與uninstall smoke PASS。

---

## 19. Release 與遷移策略

### 19.1 不破壞現有 Evergreen Advisor

現有 AdvisorStore 與 CLI 繼續可用。Project Brain 是較高層的 project binding 與 Agent interface。

### 19.2 現有 Advisor 轉 Project Brain

提供：

```bash
notebooklm-brain init \
  --adopt-advisor-id existing-advisor \
  --scope project
```

它只建立 manifest 與 project integration，不重建 Notebook、不重複上傳來源。

### 19.3 版本建議

- v2.1：整理目前 DX／Ask-only 增量。
- v3.0-alpha：manifest + init + read-only MCP + Skill。
- v3.0-beta：Librarian sync + remember。
- v3.0：通過完整 Project Brain E2E。

實際版本號可在 Phase 0 基線整理後再確認。

---

## 20. 成功指標

### 20.1 核心產品指標

1. 新專案從 `init` 到第一次可問答所需人工步驟。
2. Agent 不需使用者提供 Notebook ID 即正確查詢的比例。
3. Project A／B cross-binding 錯誤數，目標為 0。
4. Context recovery 回答中具有效引用的決策比例。
5. 本地修改文件被正確偵測的比例。
6. 未變更文件的重複上傳數，目標為 0。
7. secrets 誤上傳數，目標為 0。
8. raw log 被直接上傳數，目標為 0。
9. stale plan 被錯誤套用數，目標為 0。
10. source capacity 已滿但仍發出新增 RPC 的次數，目標為 0。
11. 新來源未出現在 backend snapshot 卻被回報成功的次數，目標為 0。
12. 只有外部研究來源卻被標記為 `project_ready` 的次數，目標為 0。
13. 缺少專案 canonical sources 卻生成「專案解釋」artifact 的次數，目標為 0。
14. 新 Agent 接手後能找到正確下一步的 E2E 成功率。

### 20.2 不採用的虛榮指標

- Notebook 來源越多越好。
- 每次 session 都寫回越好。
- Agent 呼叫 NotebookLM 次數越多越好。
- Persona 越長越好。

目標是提高正確恢復、有效查詢與知識品質，不是增加工具呼叫量。

---

## 21. 風險與對策

| 風險 | 對策 |
|---|---|
| Agent 看得到 MCP 但不呼叫 | Project-local Skill + 明確 triggers + E2E 驗證 |
| Agent 呼叫錯 Notebook | manifest + 完整 UUID + 無 manifest 不猜 |
| Notebook 文件落後 | hash scan + staleness + sync plan |
| 只有研究來源卻冒充專案知識 | source roles + grounding coverage gate + readiness state |
| raw log 污染檢索 | Upload Gate + curated remember |
| secrets 上傳 | path denylist + content detection + default block |
| 多 Agent conversation 衝突 | explicit conversation identity + 不刪共享 conversation |
| Google auth 過期 | health/doctor + optional auth refresh |
| NotebookLM 非正式 API 改變 | backend adapter 邊界 + contract tests |
| 專案 scope 不被客戶端支援 | user-level MCP fallback，但 project manifest 控制啟用 |
| 文件與程式碼衝突 | local code first + staleness warning + source provenance |
| 來源上限 | source budget + merge／supersede／retire review |
| 工作目錄既有修改被覆寫 | installer no-clobber + preview diff + bounded markers |

---

## 22. 已決定的預設值

1. 預設 scope：`project`。
2. User/global scope：選配。
3. 預設角色：Advisor + Librarian + Studio Producer 同時可用；Studio generation 仍需逐次確認。
4. 預設 sync/writeback：review。
5. 預設不自動刪除來源。
6. 預設不 follow symlink。
7. 預設排除 secrets、logs、build、dist、runs。
8. 所有 Notebook 操作使用完整 UUID。
9. 找不到 manifest 時不猜 Notebook。
10. Query 可以自動；外部來源修改需核准。
11. NotebookLM 回答必須附引用，並回到本地程式碼驗證。
12. Generic `notebooklm-py` MCP 可重用，但不取代 Project Brain MCP 語意層。
13. 只有 external research sources 時 readiness 為 `research_only`，不得生成或回答成「專案本身」。
14. 專案問答、recovery 與 artifacts 前先檢查 required project source roles 與 freshness。

---

## 23. 尚待實作前確認的細節

以下不阻擋企劃成立，但在對應 Phase 開始前需定案：

1. 第一批正式支援的 Agent client 清單與 project-local MCP config 格式。
2. Project-local Skill 的標準安裝目錄矩陣。
3. NotebookLM 新 conversation 的可用 backend contract。
4. Local source replacement 在 NotebookLM source type 上的精確行為。
5. Binary source hydration 驗證的最低可靠訊號。
6. Runtime hash index 最終放在 App Data 或 project-local gitignored cache。
7. 是否提供可選、可提交的 source lock manifest。
8. 排程由本專案管理，或只產生 launchd／cron／Task Scheduler 設定。

---

## 24. 最終產品判定標準

本專案只有在以下旅程可成立時，才能稱為「Project Brain」，而不只是 NotebookLM CLI wrapper：

```text
使用者在單一專案執行 init
        ↓
專案保存精確 Notebook ID 與使用政策
        ↓
新 Agent 自動發現 Project Brain
        ↓
確認 canonical project sources 齊全且最新
        ↓
缺少背景時主動詢問並取得引用
        ↓
需要外部知識時建立研究 Preview
        ↓
重要文件變更時產生安全同步 Plan
        ↓
任務完成時整理長期記憶，而非傾倒 raw log
        ↓
下一個失去上下文的 Agent 可以恢復方向
```

如果只有「可以呼叫 NotebookLM」，但 Agent 不知道何時呼叫、連哪一本、如何更新及如何恢復上下文，則仍不算完成。

---

# 結論

本企劃的正式發展方向是：

> **以 project-local 為預設的 NotebookLM Project Brain，透過 MCP 提供標準操作能力，透過 Skill 提供主動使用規則，透過 `.notebooklm/brain.json` 綁定精確 Notebook UUID，並以 Librarian Sync／Remember 工作流維持長期知識品質。**

它不是單純增加一個 MCP，也不是單純撰寫一份 Skill；完整產品必須同時具備：

1. NotebookLM knowledge backend。
2. Project Brain MCP。
3. Project-local Agent Skill。
4. Project → Notebook manifest。
5. Reviewed document sync。
6. Curated memory writeback。
7. Context recovery。
8. Project grounding coverage 與 research-only 防誤用。
9. NotebookLM Studio artifact reuse。
10. Multi-agent、security 與可恢復操作邊界。

依此路線完成 Phase 1–4 後，產品即可達到真正可用的專案大腦核心；Phase 5–7 則補齊常青研究、多 Agent、排程與跨客戶端發布能力。
