# notebooklm-skill 維護盤點與上游重新對齊計畫

> 日期：2026-08-22
>
> 上游基準：[`teng-lin/notebooklm-py`](https://github.com/teng-lin/notebooklm-py) `0.8.1`（2026-08-14）
> 本專案最後提交：`e77a9a4`（2026-04-07）

## 1. 結論

本專案不應繼續把主要維護成本放在 NotebookLM 網頁 DOM 與 Patchright 選擇器上。

推薦方向是：

1. **保留本專案真正獨特的產品層**：Research / Project 雙 notebook、角色路由、tone presets、來源分類與 Upload Gate、繁中使用流程。
2. **把 NotebookLM 操作層改接上游 `notebooklm-py`**：認證、建立 notebook、來源 CRUD、查詢、引用、persona、artifact 等都委派給上游 RPC/CLI。
3. **以薄整合層取代自行維護的瀏覽器自動化層**，不要複製或 fork 上游數百個模組。
4. 先維持既有 `scripts/run.py ...` 指令的相容 wrapper，再決定是否於下一個 major release 移除。

這樣可以把維護重心從「追 Google UI selector」轉回「如何讓 coding agent 管理專案知識」。

---

## 2. 現況盤點

### 2.1 目前仍有價值、應保留的能力

- Research + Project 雙 notebook 架構
- `default` / `vc` / `critic` persona presets
- 根據問題意圖路由 notebook 的 agent 指引
- Category prefix、來源權重與 `[LIVE]` 慣例
- Upload Gate：Stability → Retrievability → Irreplaceability → Signal-to-Noise
- 中英文 README 與繁中工作流
- notebook 命名品質檢查

這些是方法論與 agent orchestration，並不與上游重複。

### 2.2 技術債與已確認問題

#### P0：核心執行層脆弱

- 所有主要操作仍依賴 NotebookLM Angular DOM 與硬編碼 selector。
- `scripts/add_source.py` 已有未提交的 UI 適配修改，表示來源上傳流程已受 UI 變動影響；目前修改還混用了 generic textarea/contenteditable 與固定 selector，不能視為完整修復。
- `ask_question.py` 的 single-shot 路徑沒有傳入 `previous_answer`，有機會把舊回答誤判為新回答。
- `browser_daemon.py` 讓多個 handler thread 共用 Playwright sync context；不同 notebook 同時查詢時存在 thread-safety 風險。
- `browser_session.py` 呼叫不存在的 `StealthUtils.random_mouse_movement()`，且大部分 selector 與共用工具重複，疑似已成為未使用舊路徑。
- `create_pair()` 沒有交易式復原；第二本 notebook 或 persona 設定失敗時會留下半完成狀態，而且 persona 設定結果目前被忽略。

#### P0：缺乏可驗證的品質基線

- 沒有 `tests/`、CI、lint/type-check 設定或正式 package metadata。
- 目前只能確認 Python compile 與 CLI `--help` 通過，無法證明 NotebookLM 行為正確。
- 需求只鎖 `patchright==1.55.2`、`python-dotenv==1.0.0`；沒有 lockfile 或升級策略。

#### P1：資料與專案隔離

- `library.json`、認證與 browser profile 全部存放在 skill repo 的 `data/`。
- 已知 issue #002：symlink 安裝會讓所有專案共用 notebook library。
- JSON 寫入不是 atomic，也沒有 file lock；並行 agent 有資料毀損風險。
- notebook 移除時不會同步清理另一端的 `paired_with`；更新名稱也不重新驗證或處理 ID。

#### P1：文件與實作不一致

- README 宣稱每個 notebook 固定最多 50 sources；現在應改為**依帳號方案而異**（Standard 50、Plus 100、Pro 300、Ultra 500/600）。
- `SKILL.md` 寫 daemon log 在 `/tmp/notebooklm-daemon.log`，實作其實是 `data/daemon.log`。
- `run.py` 列出不存在的 `session_manager.py`，但沒有列出 `add_source.py`、`create_notebook.py`、`set_notebook_guide.py`。
- README 的架構樹與 Limitations 已落後 daemon/create/source 功能。
- `SKILL.md` 宣稱 naming hook 強制生效，但 hook 只存在未追蹤的 `.claude/settings.local.json`，而且包含本機絕對路徑，其他安裝者不會得到同樣保護。
- 版本紀錄停在 1.4.0；4 月的 naming harness 沒進 changelog，Git tag 也只有 `v1.3.1`。
- Google 已在 2026-07 將產品品牌改為 **Gemini Notebook**；新預設 host 是 `https://notebook.google.com`，舊 `notebooklm.google.com` 目前仍相容。

---

## 3. 與上游 `notebooklm-py` 0.8.1 的差距

上游已從「瀏覽器操作 UI」演進成以 undocumented RPC 為主的完整 Python/CLI 平台：

| 能力 | 本專案 | 上游 0.8.1 | 建議 |
|---|---|---|---|
| 認證 | Patchright profile + cookie 注入 | login、browser cookie import、profiles、refresh、doctor | 委派上游 |
| Notebook | 建立、本地 library | list/create/rename/delete/collections/metadata | 委派上游，保留 pair metadata |
| Source | 只支援貼上文字/檔案內容 | URL、YouTube、file、Drive、text、list/wait/rename/delete/refresh/fulltext/guide | 委派上游 |
| Chat | 單次文字回答 | conversation、JSON references、source scoping、history、save note | 委派上游 |
| Persona | DOM 設定 | `notebooklm configure --persona/--response-length` | 委派上游 |
| Research | 無 | fast/deep research、wait/import/cancel | 第二階段開放 |
| Artifacts | 無 | audio/video/slides/report/quiz/flashcards/infographic/table/mind map + download | 第二或第三階段開放 |
| API adapters | Claude skill scripts | CLI、Python API、MCP、REST | 先採 CLI JSON；需要時再用 Python API/MCP |
| 品質 | 無測試 | Python 3.10–3.14、大量 unit/integration tests、90% coverage gate | 不重造底層 |

上游已經完成原 roadmap 中多數內容：source refresh、fulltext/export 類能力、artifact generation/download。這些功能不應再自行以 DOM 實作。

---

## 4. 目標架構

```text
Claude / coding agent
        |
        v
SKILL.md（本專案的方法論、路由、Upload Gate）
        |
        v
compatibility wrappers / project orchestrator
  - create_pair
  - route_notebook
  - apply_tone
  - project manifest
        |
        v
notebooklm-py CLI --json（第一階段）
        |
        v
上游 RPC / auth / retry / source / chat / artifact runtime
```

### 為什麼第一階段選 CLI JSON，而非直接 Python API

- 改動最小，容易保留現在的 shell/Skill 使用方式。
- 上游 CLI 已有穩定的 JSON envelope 與 exit code。
- 避免把本專案綁到上游 private Python modules。
- 後續若需要高效批次或長生命週期 client，再把 backend adapter 換成 public Python API；上層 pair/route 邏輯不變。

---

## 5. 分階段實作

## Phase 0 — 建立安全基線（P0，0.5–1 天）

### 工作

- 保留並隔離目前未提交的 `.gitignore`、`scripts/add_source.py` 與其他研究文件，不覆蓋使用者工作。
- 建立最小測試框架：`pytest`、`ruff`、GitHub Actions。
- 記錄目前公開 CLI 與本地 manifest 格式，作為相容性測試 fixture。
- 決定支援 Python `3.10–3.14`，與上游一致。
- 初期 pin：`notebooklm-py[browser]>=0.8.1,<0.9`；升級必須經 smoke test。

### 驗收

- Unit tests 可在沒有 Google 帳號下執行。
- CI 覆蓋 Python 3.10、3.12、3.14。
- 現有 dirty worktree 不被更動或遺失。

## Phase 1 — 替換五條核心路徑（P0，2–4 天）

### 工作

新增一個薄 `backend` adapter，統一呼叫上游 CLI 並解析 JSON；遷移：

1. **Auth**
   - `auth_manager.py setup/status/validate/reauth` → `notebooklm login`、`auth check --test --json`、`auth refresh`。
2. **Create pair**
   - `notebooklm create` 建立兩本 notebook。
   - `notebooklm configure --persona ... --response-length longer` 套用 preset。
   - 任一步驟失敗時，回報 partial state；可選擇 rollback 已建立 notebook。
3. **Add source**
   - file/URL/text 走 `notebooklm source add --json`。
   - 接 `source wait`，完成後驗證 title/status；不再依靠「貼上的文字」DOM rename。
4. **Ask**
   - `notebooklm ask --json`，保留 answer、conversation ID、references。
   - 支援明確 notebook ID 與 source IDs。
5. **Configure persona**
   - 用上游 `configure`，移除 UI selector 操作。

保留 `scripts/run.py <old-script>` compatibility wrapper 一個 release，內部轉向新 adapter。

### 驗收（真實帳號 smoke test）

- `auth check --test --json` 回傳 `status=ok`。
- 能建立 `[Research] SmokeTest-*` 與 `[Project] SmokeTest-*` 並套用 persona。
- 能加入一份 Markdown，等待至 ready，並從 list 中以正確標題找到。
- 查詢回傳非空 answer，且 JSON references 至少包含 source ID。
- 清除 smoke notebook 後不留下孤兒 pair metadata。
- 核心執行路徑不再 import `patchright`。

## Phase 2 — 專案級 manifest 與遷移（P0/P1，1–2 天）

### 建議格式

在使用者專案中建立：

```text
<project>/.notebooklm/project.json
```

只存本專案獨有資料：

```json
{
  "schema_version": 1,
  "project": "Example",
  "research_notebook_id": "...",
  "project_notebook_id": "...",
  "tone": "default",
  "routing": {
    "research": ["market", "competitor", "user pain"],
    "project": ["architecture", "decision", "progress"]
  }
}
```

認證與 account profiles 完全交給上游的全局 storage；專案 manifest 不保存 cookie。

### 工作

- 實作 atomic write（temporary file + replace）與 file lock。
- 從現有 `data/library.json` 進行顯式 migration；不要靜默移動。
- 驗證 notebook IDs 仍存在，並提供 repair/relink 指令。
- 移除 notebook 時同步更新 pair 關係。

### 驗收

- 兩個不同專案各自只看到自己的 pair。
- 並行寫入不會產生壞 JSON。
- 舊 library 可 preview migration，確認後再寫入。

## Phase 3 — 開放上游高價值能力（P1，2–3 天）

優先順序：

1. Source lifecycle：list/wait/delete/rename/refresh/fulltext/guide。
2. Conversation continuity 與 citation/reference 結構化輸出。
3. 多帳號 profile 選擇與 `doctor` 診斷。
4. Deep Research + import。
5. labels/collections（可逐步取代 category prefix 的 soft filtering）。
6. artifact generate/download；先做 report、slide deck、audio，其他按需求加入。

這一階段只新增薄指令與 Skill guidance，不重新實作上游功能。

## Phase 4 — 文件、品牌與 release（P1，1–2 天）

### 工作

- README / README.zh-TW / SKILL.md 全面同步。
- 名稱採「Gemini Notebook（原 NotebookLM）」；程式與 package 名保留 `notebooklm` 相容稱呼。
- host 不再硬編碼，只由上游管理。
- 來源限額改為 plan-dependent，並提醒以 account 回傳值為準。
- 更新安裝方式為 `uv tool` / `pipx` 或專案 venv；說明 Python >=3.10。
- 修正 daemon、session、架構樹、log path、naming hook 等過期文件。
- 將 naming validation 改成程式本身的保證；hook 只能是額外 UX，不能宣稱為跨安裝強制層。
- 增加 migration guide 與 rollback 指引。

### Release 建議

- 若舊命令都由 compatibility wrapper 保留：先發 `v1.5.0`，標示 browser backend deprecated。
- 下一版移除 Patchright/daemon/舊 auth storage：發 `v2.0.0`。
- 若第一階段直接移除舊命令與 Python 3.8 支援，則直接發 `v2.0.0`。

---

## 6. 建議刪除或封存的舊模組

只有在 Phase 1 smoke test 通過後才處理：

- `browser_daemon.py`
- `browser_session.py`
- `browser_utils.py`
- DOM selectors in `config.py`
- Patchright-specific auth/profile workaround
- `set_notebook_guide.py` 的 DOM 實作
- `add_source.py` 的 DOM paste/rename 實作

`create_notebook.py`、`ask_question.py`、`auth_manager.py` 可先保留檔名，改成 compatibility wrappers，降低使用者升級成本。

---

## 7. 不建議做的事

- 不要只升級 Patchright、再繼續補 selector；這只能延後下一次 UI break。
- 不要把上游 355+ Python 模組複製進本 repo。
- 不要一次暴露上游所有 artifact/MCP/REST 功能；先修核心五條路徑。
- 不要把 auth cookie 寫進 project manifest 或 git。
- 不要在未處理目前 dirty worktree 前直接重寫 `add_source.py`。
- 不要硬編碼 plan quota、host 或 Google 內部 RPC ID；交給上游版本管理。

---

## 8. 第一個可執行工作包

建議下一步直接做 **Phase 0 + Phase 1 的垂直切片**：

1. 加入上游依賴與 backend adapter。
2. 只遷移 `auth status`、`ask`、`add source` 三條路徑。
3. 建立 unit tests（mock subprocess JSON）與一支 opt-in live smoke script。
4. 驗證成功後，再遷移 create pair/persona。
5. 最後才移除 daemon/Patchright。

完成標準不是「程式能跑」，而是：**一份來源可被加入、確認 ready、查詢並取得 citation，且全程不依賴 Notebook UI selector。**

---

## 9. 外部資料來源

本次上游資料於 2026-08-22 使用 Crawl4AI 讀取：

- 上游 `README.md`
- 上游 `SKILL.md`
- 上游 `pyproject.toml`
- 上游 `CHANGELOG.md`
- `docs/architecture.md`
- `docs/cli-reference.md`
- `docs/quota-limits.md`
- Gemini Notebook rename ADR

上游是 unofficial API，仍可能因 Google 內部 RPC 變動而中斷；採用它不是消除風險，而是把該風險集中交由活躍、已有完整測試與 release 流程的專案維護。
