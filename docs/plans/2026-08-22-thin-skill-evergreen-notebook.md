# Thin Skill + Evergreen Notebook 更新計畫

> 日期：2026-08-22
>
> 狀態：Phase 0–5C implemented；Phase 5D engineering additions implemented but experiment invalid；Phase 6 deferred
> 本階段目標：把舊專案縮成薄 Skill，完成 Persona 設定與手動觸發的 Evergreen 更新引擎；保留未來遷移到開源 Notebook backend 的能力。

## 1. 產品定義

新的產品不再是「專案資料夾文件管理員」，也不再自行維護 NotebookLM 的瀏覽器自動化。

新的核心是：

> 建立一個有明確 Persona 的長期參謀 Notebook，並透過週期性 Deep Research、安全的來源汰換與更新摘要，使其持續接近最新狀態。

Persona 不預設為技術角色。它可以是心理學研究顧問、哲學研究者、市場分析師、醫療顧問、產品策略師、技術架構師，或跨領域組合；Skill 只負責忠實套用使用者選擇的研究視角與證據標準。

暫定名稱：

- **常青 Notebook（Evergreen Notebook）**：長期存在、持續更新的參謀 Notebook。
- **研究設定檔（Research Profile）**：記錄長期研究主題、查詢方式和更新規則。
- **研究更新週期（Research Refresh Cycle）**：一次重新研究、比較、匯入與汰換來源的完整過程。
- **Persona／對話角色**：Gemini Notebook「設定對話 → 對話風格 → 自訂」中的角色提示；目前資料模型尚未另外保存 End-user Persona。
- **關注項目（Watch Item）**：需要長期追蹤的假設、問題、趨勢、風險或既有決策。
- **假設監測（Assumption Watch）**：檢查支持或反駁核心假設的新證據。
- **決策監測（Decision Watch）**：Assumption Watch 的一種，用於檢查既有決策成立的前提是否改變。
- **技術雷達（Technology Radar）**：技術領域可選用的輸出模板，不是 Evergreen Notebook 的通用預設。

---

## 2. 本階段範圍

### 要做

1. 使用現成 `notebooklm-py` backend，不再自行操作 Notebook UI。
2. 建立 Notebook 後立即套用 Persona 與回覆內容長度。
3. 支援把既有 Notebook 納入管理（adopt），不要求重新建立。
4. 建立 backend-neutral 的 Research Profile 與 Watch Items。
5. 手動觸發 Deep Research 更新。
6. 比較現有來源與新研究候選來源。
7. 顯示新增、更新、保留、取代與刪除建議。
8. 新來源成功處理後，才能刪除被取代的舊來源。
9. 記錄每次更新結果並產生「這次有什麼變化」摘要。
10. 提供可攜式匯出，為未來 Open Notebook backend 遷移留下入口。

### 暫停

- 掃描專案資料夾
- 自動挑選專案文件
- Git commit / PRD completion hooks
- Research / Project 雙 Notebook 強制架構
- 專案文件自動同步
- 每個 commit 自動上傳

### 本階段不做

- 完全自動排程
- 無人確認的自動刪除
- 實作 Open Notebook backend
- 自建 RAG / NotebookLM 替代品
- 複製或 fork `notebooklm-py` 的 RPC 實作
- 繼續維護 Patchright selectors、browser daemon 和 cookie workaround

---

## 3. 已確認的技術可行性

截至 2026-08-22，官方 Gemini Notebook 與 `notebooklm-py 0.8.1` 已提供本功能所需的大部分底層能力。

### 官方 Gemini Notebook

- Fast Research：從 Web / Drive 尋找來源。
- Deep Research：瀏覽大量網站、生成研究報告、列出引用與未引用來源。
- 可選擇匯入部分或全部研究結果。
- Google Drive 來源會自動同步。
- Web URL 來源是匯入時的內容副本，不會自然變成完整的主題追蹤系統。
- 可刪除來源、以標籤分類來源。

### `notebooklm-py`

- 建立、取得、設定 Notebook。
- `configure --persona` 與 `--response-length`。
- `source list/get/fulltext/stale/refresh/delete/wait`。
- `source add-research --mode deep --no-wait`。
- `research status/wait/import/cancel`。
- Python API 可選擇特定 `ResearchSource` 匯入。
- `import_sources_with_verification()` 能以 URL 去重、重試並確認實際匯入結果。
- 認證可 refresh，適合未來交由 OS scheduler 呼叫。

### 尚缺的部分

以下是本 Skill 的價值所在：

- 長期研究設定檔
- 可跨領域使用的 Persona 與 Watch Items
- 何時該更新
- 新舊來源比較
- Pinned / Active / Superseded 狀態
- 安全的替換政策
- 更新摘要與歷史紀錄
- backend-neutral 匯出格式

---

## 4. 詞彙與資料模型

## 4.1 Advisor Profile

每個長期參謀以一個本地穩定 ID 管理，不直接以 Google Notebook UUID 作為主身份。

```yaml
schema_version: 1
advisor_id: app-market-watch
title: App Market Watch
backend:
  type: gemini-notebook
  notebook_id: "google-notebook-uuid"

persona:
  instructions: |
    你是資深產品情報與競爭分析顧問。
    區分已證實事實、推論與未知資訊。
    優先引用官方資料並標示資料日期。
  response_length: longer

research:
  enabled: true
  brief: |
    長期追蹤這個 App 的新功能、價格、商業模式、
    使用者反應、主要競爭者及市場定位變化。
  queries:
    - "最近三個月的新功能、產品公告與價格變化"
    - "最近三個月使用者評價與主要抱怨的變化"
    - "主要競爭者最近推出了哪些替代功能"
  mode: deep
  language: zh-Hant
  recency_days: 90
  max_new_sources_per_run: 10
  preferred_domains:
    - example.com
  update_mode: review
  deletion_mode: confirm

watchlist:
  - watch_id: watch-001
    kind: trend
    statement: "主要競爭者的能力與定位正在改變"
    questions:
      - "最近有哪些足以改變市場格局的新證據？"
    evidence_for: []
    evidence_against: []
    revisit_when:
      - "出現重要產品發布、政策變化或高品質研究"
    status: active

schedule:
  mode: manual
  suggested_interval_days: 30
```

第一版只支援 `schedule.mode: manual`。欄位先保留，後續才能加入 launchd / cron。

## 4.2 Watchlist

Watchlist 讓 Evergreen Notebook 不只是「找最近新聞」，而是持續檢查真正重要的問題。

`kind` 可為：

- `assumption`：產品、心理、商業、科學或其他核心假設。
- `decision`：既有決策及其成立前提。
- `trend`：需要長期觀察的外部變化。
- `risk`：可能增加或降低的風險。
- `question`：目前仍沒有可靠答案的問題。

每次更新應針對 Watch Item 找到：

- 新的支持證據
- 新的反面證據
- 互相矛盾的證據
- 仍然未知的部分
- 是否觸發 `revisit_when`

Watchlist 不得把尚未證實的假設寫成事實，也不得因一次 Deep Research 沒找到資料就判定假設為真或假。

## 4.3 Source Registry

```yaml
sources:
  - local_id: src-001
    backend_source_id: "google-source-uuid"
    title: "Official Release Notes"
    url: "https://example.com/releases"
    canonical_url: "https://example.com/releases"
    origin: manual
    state: pinned
    discovered_at: "2026-08-22T10:00:00Z"
    last_verified_at: "2026-08-22T10:00:00Z"
    last_modified_at: null
    research_run_id: null
```

來源狀態：

- `pinned`：核心資料，永不自動刪除。
- `active`：目前有效來源。
- `candidate`：新研究找到、尚未匯入。
- `superseded`：有更可靠或更新來源取代。
- `broken`：無法存取或處理失敗。
- `deleted`：已從 backend 移除，但本地留有稽核記錄。

## 4.4 Refresh Run

每次更新產生不可覆寫的紀錄：

```yaml
run_id: refresh-20260822-001
advisor_id: app-market-watch
started_at: "..."
completed_at: "..."
baseline_source_ids: []
research_queries: []
watch_items_evaluated: []
candidates: []
proposed_additions: []
proposed_refreshes: []
proposed_superseded: []
proposed_deletions: []
approved_actions: []
imported_sources: []
deleted_sources: []
summary: "..."
status: completed
```

Credential、cookie、master token 不得寫入以上檔案。

## 4.5 正式儲存契約

以上 YAML 只用於計畫書的可讀示例；正式機器資料統一使用 **versioned JSON**，可讀說明與 Persona 另提供 Markdown。這避免 YAML parser 差異與額外 runtime dependency，也便於其他 backend 驗證及遷移。

正式狀態使用各作業系統的標準 user data directory：

```text
macOS:  ~/Library/Application Support/notebooklm-skill/advisors/
Linux:  ~/.local/share/notebooklm-skill/advisors/
Windows: %LOCALAPPDATA%/notebooklm-skill/advisors/
```

實作時由 platform-aware path resolver 取得位置，不硬編碼使用者名稱。`NOTEBOOKLM_SKILL_HOME` 可覆蓋 app data root；測試一律注入暫存目錄，不讀寫正式目錄。

每個 Advisor 使用獨立目錄：

```text
advisors/<advisor_id>/
├── profile.json
├── persona.md
├── watchlist.json
├── sources.json
└── refresh-runs/
    └── <run_id>.json
```

儲存規則：

- JSON 必須包含 `schema_version`。
- 同一檔案採 temp file → flush/fsync → atomic replace。
- 同一 Advisor 的 mutation 需持有 file lock。
- Backend credential 與 Advisor state 必須分離；不得保存 cookie、token、master token 或其內容。
- Google Notebook ID 只是 provider reference；本地 `advisor_id` 才是穩定身份。
- Export destination 由每次 export 命令指定，不等於正式狀態目錄。

---

## 5. Backend 架構

```text
SKILL.md / natural-language intents
                |
                v
Evergreen Orchestrator
  - create/adopt advisor
  - apply persona
  - refresh cycle
  - review/apply plan
  - export bundle
                |
                v
NotebookBackend interface
                |
       +--------+---------+
       |                  |
GeminiNotebookBackend   Future OpenNotebookBackend
(notebooklm-py)         (本階段不實作)
```

### 最小 backend contract

```python
class NotebookBackend(Protocol):
    async def create_notebook(...): ...
    async def configure_chat(...): ...
    async def get_chat_config(...): ...
    async def list_sources(...): ...
    async def get_source_content(...): ...
    async def check_freshness(...): ...
    async def refresh_source(...): ...
    async def start_research(...): ...
    async def poll_research(...): ...
    async def import_research_sources(...): ...
    async def wait_for_sources(...): ...
    async def delete_source(...): ...
    async def ask(...): ...
```

Backend 應宣告 capabilities。未來 Open Notebook 不支援 Deep Research 時，可以改接外部 research provider，而不是讓整個 Evergreen Profile 失效。

---

## 6. Persona 建立流程

技術上，建立 Notebook 與設定 Persona 是兩個動作；Skill 對使用者呈現為一次流程。

```text
輸入 Notebook 名稱、目的、Persona
  ↓
建立 Notebook
  ↓
設定對話風格 = Custom
  ↓
寫入 Persona instructions
  ↓
設定 response length
  ↓
讀回或執行測試問題驗證
  ↓
建立 Advisor Profile
```

### 驗收

- Persona 設定失敗時，不能回報整體建立成功。
- 應保留已建立 Notebook ID，提供 retry，不重複建立第二本。
- 測試問題應確認回答遵守 Persona，但不可宣稱 Persona 會提升事實正確率。
- Studio artifacts 有自己的 generation instructions，不假設自動繼承 Chat Persona。

---

## 7. Research Refresh Cycle

## 7.1 Phase A：Preflight

1. 驗證 authentication。
2. 驗證 Notebook 仍存在且可存取。
3. 讀取 Persona、Research Profile 與 Watchlist。
4. 取得帳號 source limit 與目前 source count。
5. 若已有進行中的 research run，停止並要求 resume / cancel，不啟動第二個。

## 7.2 Phase B：Baseline Snapshot

1. 列出所有現有來源。
2. 對 registry 與 backend 做 reconciliation。
3. 找出：
   - registry 有、backend 沒有的來源
   - backend 有、registry 沒有的來源
   - processing/error/broken 來源
4. 保存 source metadata snapshot。
5. Pinned source 永遠進入 protected set。

## 7.3 Phase C：Refresh Existing Live Sources

對 URL / Drive 類型且標示為 live 的來源：

1. `check_freshness()`。
2. Fresh：更新 `last_verified_at`。
3. Stale：列入 `proposed_refreshes`。
4. Broken：列入警告，不直接刪除。
5. Drive 來源優先使用原生 sync，不做 delete + re-add。

## 7.4 Phase D：Run Deep Research

由 Profile 產生時間敏感查詢：

```text
原始 brief
+ 上次成功更新日期
+ recency window
+ Watch Items 與 revisit conditions
+ 要求優先官方、第一手或該領域公認的高品質來源
+ 要求找出支持、反駁與互相矛盾的證據
+ 要求指出「自上次更新以來的變化」
```

每個 query：

1. Start deep research，記錄 task/run ID。
2. 使用 non-blocking poll。
3. Timeout 時保存 resumable state，不重開新 research。
4. 取得 report、candidate URLs、titles、snippets、citation status。

## 7.5 Phase E：Candidate Evaluation

依序判斷：

1. **Exact URL dedupe**：canonical URL 已存在則不新增。
2. **Source authority**：官方 release notes / docs 優先於轉載。
3. **Recency**：日期在 requested window 內優先；日期未知不能假裝是新資料。
4. **Relevance**：必須直接回答 Research Profile 的問題。
5. **Citation signal**：研究報告實際引用的來源優先。
6. **Near duplicate**：標題、domain、snippet 高度相似時只留較可靠版本。
7. **Budget**：不得超過 `max_new_sources_per_run` 或帳號 source limit。

第一版不允許 LLM 以「這次沒搜尋到」作為刪除舊來源的理由。

## 7.6 Phase F：Review Plan

產生一份使用者可讀的更新計畫：

```text
本次研究：3 個查詢
找到：24 個候選來源
建議新增：6
建議 refresh：2
建議保留：18
建議標記 superseded：3
建議刪除：0（或列出原因）
```

每個動作都要附理由與來源日期。第一版要求使用者確認。

## 7.7 Phase G：Apply Additions First

1. 匯入已核准 candidate。
2. `allow_duplicate=False`。
3. 等待每個新來源達到 ready。
4. Import/processing 失敗只記錄，不進入刪除階段。
5. 對實際 backend 結果 reconciliation，避免 timeout 後重複匯入。

## 7.8 Phase H：Delta Summary

新來源 ready 後，向 Notebook 提問：

- 自上次更新以來，哪些事實改變？
- Watch Items 出現了哪些新支持或反面證據？
- 哪些舊結論或核心假設現在受到挑戰？
- 哪些 revisit conditions 已被觸發？
- 哪些資訊仍然不確定？

領域專用輸出（例如技術雷達、心理學證據地圖、市場變化表）由 Persona / Profile 選擇，不硬編碼成所有 Notebook 都使用同一模板。

輸出必須區分：

- Confirmed change
- Likely change
- Conflicting evidence
- Unknown

## 7.9 Phase I：Safe Retirement

只有滿足以下全部條件才能刪除舊來源：

1. 不在 protected/pinned set。
2. 有明確 replacement，不是單純「比較舊」。
3. Replacement 已 ready。
4. 已匯出舊來源 metadata；能取得 fulltext 時一併備份。
5. 更新計畫中已說明刪除原因。
6. 使用者明確確認。

刪除後保留 tombstone record，不重用 local source ID。

## 7.10 Phase J：Commit Run Record

1. 更新 Source Registry。
2. 寫入 immutable run record。
3. 更新 `last_successful_refresh_at`。
4. 顯示新增、更新、刪除、失敗與未決項目。

---

## 8. 安全規則

以下是不可破壞的 invariants：

1. **Add before delete**：永遠先加入並確認新來源，再刪舊來源。
2. **Pinned means protected**：Pinned 永遠不由自動流程刪除。
3. **Missing is not obsolete**：這次研究沒找到，不代表舊來源已過時。
4. **No blind import-all**：第一版不得無限制匯入全部結果。
5. **No silent deletion**：第一版所有刪除都需確認。
6. **Respect limits**：執行前檢查來源與 Deep Research quota。
7. **Resume, do not duplicate**：timeout 後先 resume/reconcile，不重新啟動同一輪。
8. **Record uncertainty**：無法取得日期或判斷新舊時，必須標示 unknown。
9. **Portable state only**：核心 profile 不儲存 provider credentials。
10. **Capability-aware**：backend 不支援的功能要明確降級，不可假成功。

---

## 9. 可攜性與 Open Notebook 遷移準備

本階段不實作 Open Notebook，但所有新資料格式不得綁死 Google。

## 9.1 Export Bundle

```text
advisor-export/
├── manifest.json
├── persona.md
├── research-profile.json
├── watchlist.json
├── sources.json
├── source-content/
│   ├── src-001.md
│   └── src-002.md
├── refresh-runs/
│   └── refresh-20260822-001.json
└── README.md
```

### 保證可攜的內容

- Persona
- Research brief 與 queries
- Watch Items、revisit conditions 與證據狀態
- Source metadata / URLs
- 可讀取的 source fulltext
- Refresh history
- Pinned / Active / Superseded 狀態
- 更新摘要

### 不保證可以一對一遷移的內容

- Google 內部 Notebook / Source UUID
- 已存在的 chat conversation ID
- Google 專屬 artifact ID
- Google 無法匯出的原始二進位檔案
- 另一 backend 不支援的 Persona / Deep Research 行為

未來 OpenNotebookBackend 應讀取同一 export bundle，建立新 notebook、匯入 source content/URLs、套用 Persona，並回寫新的 backend IDs。

---

## 10. 實作階段

## 10.0 Phase Gate 協作規則

每個 Phase 都是一個獨立關卡，不會因上一階段完成就自動進入下一階段。

開始一個 Phase 前，Assistant 必須先告知：

1. 本階段要完成什麼。
2. 預計修改哪些檔案或外部資源。
3. 明確的通過條件。
4. 需要使用者提供或確認什麼。
5. 是否會使用 Google 帳號、Deep Research quota、建立或刪除 Notebook / source。
6. 失敗時如何還原或重試。

完成一個 Phase 後，Assistant 必須回報：

- 每一項通過條件的實際證據。
- `PASS`、`PARTIAL` 或 `FAIL`。
- 尚未完成或需要人工判斷的事項。
- 使用者接下來可以選擇：核准進入下一階段、要求修正，或暫停。

除非使用者明確核准，否則不得跨越 Phase Gate。使用者不需要猜下一步；每個 Gate 都必須直接說明「現在需要你做什麼」。

Phase Gate 不是把一般實作決策轉交給使用者。可由既有計畫、程式與工程慣例決定的事項，Assistant 應先自行查證、記入計畫並提出明確方案；只有產品範圍仍有真正歧義、需要 credential/quota、涉及付費或不可逆外部操作時，才要求使用者做額外選擇。若執行中發現計畫缺口，先暫停該 Phase、補齊計畫並重新提出 Gate，不得邊做邊零碎詢問。

Disposable 測試資源的建立核准應在同一個 Gate 中包含「PASS 後自動清理」。成功後不得再把無上下文的保留／刪除選擇轉交使用者；只有資源已轉化為有名稱、用途、owner 與保留期限的 regression fixture、範例或稽核資產，才可保留。FAIL 時可暫留供除錯，但報告必須說明內容、保留價值與清理條件。所有有價值的測試結果應先匯出為本機 evidence，再清除沒有持續價值的過渡資源。

### 各階段需要的使用者配合

| Phase | 通過條件摘要 | 使用者需要做什麼 |
|---|---|---|
| 0 | 現有修改受保護；離線測試基線可重現 | 原則上不需提供帳號；只需在報告後決定是否進入 Phase 1 |
| 1 | create/adopt、Persona 設定與驗證成功 | Live test 時完成 Google login，並核准使用 disposable Notebook 或指定測試 Notebook |
| 2 | Profile/Watchlist/Registry 可依正式儲存契約安全保存與匯出 | 不需選擇技術路徑；只需審查 Gate 報告並決定是否進入 Phase 3 |
| 3 | Deep Research 能產生不修改來源的 preview plan | 核准消耗一次測試 quota，並提供或核准一個測試主題 |
| 4 | 新增成功後才能汰換；失敗時零刪除 | 審查一次 addition/retirement plan；刪除動作需明確確認 |
| 5 | URL/Drive refresh 與更新報告正確 | 指定或核准一個可安全測試的 live source |
| 6 | 排程可重現且預設不自動刪除 | 選擇執行頻率、作業系統 scheduler 與通知方式 |

## Phase 0：保護現況與建立測試基線（0.5–1 天）

- 保存目前 dirty worktree，不覆蓋 `scripts/add_source.py` 等未提交內容。
- 將現有 Patchright backend 標記 legacy，不立即刪除。
- 加入 pytest、ruff、CI。
- 建立 fake backend，讓 orchestration tests 不消耗 Google quota。

**完成條件：** 無 Google 帳號也能跑 unit tests；現有檔案沒有遺失。

## Phase 1：薄 Backend + Persona（1–2 天）

- 加入 `notebooklm-py>=0.8.1,<0.9`。
- 實作 `NotebookBackend` 與 `GeminiNotebookBackend`。
- 實作 auth preflight、create、adopt、configure persona、config verification。
- 保留舊 CLI wrapper 一段遷移期。

**完成條件：** 能建立或 adopt Notebook、套用 Persona、驗證設定，全程除首次 login 外不操作網頁 DOM。

## Phase 2：Profile、Registry、Export（1–2 天）

- 定義 schema 與 schema version。
- 實作 platform-aware app data path 與 `NOTEBOOKLM_SKILL_HOME` override。
- 實作 Advisor Profile / Watchlist / Source Registry / Refresh Run store。
- Atomic write + file lock。
- 實作 JSON + Markdown export bundle。

**完成條件：** Profile 可 round-trip；測試只使用暫存目錄；export 不含 credential；既有 Notebook 可 adopt。

## Phase 3：Evergreen Preview Engine（2–4 天）

- Baseline snapshot。
- Deep Research start/poll/resume。
- Candidate normalization、dedupe、scoring、budget。
- 產生 review plan，尚不自動 apply。

**完成條件：** 對 disposable Notebook 跑一次 research，輸出穩定、可讀、可解析的更新計畫，不修改來源。

## Phase 4：Safe Apply Engine（2–3 天）

- Selective import。
- Wait/reconcile。
- Delta summary。
- Pinned protection。
- Export-before-delete。
- Confirmed deletion + tombstone record。

**完成條件：** 新來源失敗時零刪除；成功時能完成 add → ready → summarize → confirmed retire。

## Phase 5：Source Refresh（1–2 天）

- URL / Drive freshness check。
- Native refresh/sync。
- Broken source handling。
- 與 Deep Research cycle 合併為一份 update report。

**完成條件：** 同 URL 更新不必重複新增；Drive source 使用 sync。

## Phase 5C：MVP Release Integration

- 改寫 `SKILL.md` 與 README，使 v2 Agent 不再進入 Patchright 路徑。
- 提供單一正式 CLI，串接 setup/adopt、Watchlist query composition、preview、apply、refresh 與 export。
- Adopt 時註冊既有來源，並提供明確 pin/classify 操作。
- Apply/refresh 成功後更新 Source Registry、tombstone 與 immutable Refresh Run。
- Backend-aware export 匯出可讀 fulltext，無法取得時明確標示 unavailable。
- 將 `scripts/` 與 Patchright dependency 隔離為 Legacy v1。

**完成條件：** v2 entry docs、CLI、formal state commit、portable content export 與 package smoke 全部通過；核心路徑不 import Patchright。

## Phase 5D：Gauntlet Loop Field Trial

- 使用 canonical GitHub URL 建立 Control 與 Evergreen Advisor disposable Notebooks。
- 新增 ready-verified、Pinned、timeout-reconcilable `source-add-url`。
- 執行一次 Deep Research，人工從完整 candidate pool 選擇六個多樣化來源。
- 新增 `ask` CLI 與 digest 前 explicit candidate selection。
- 以假設性 Three.js racing developer Persona 執行 Control/Advisor 問答。
- 匯出 7/7 可讀來源全文，完成體驗型報告後清理兩個 Notebook。

**工程結果：** `source-add-url`、`ask` 與 explicit candidate selection 已完成；來源 lifecycle 與 cleanup invariants 通過。

**實驗結果：INVALID。** Control／Treatment 使用相同 custom instructions，且同時改變來源數量、問題順序與 conversation history；沒有 pre-registered hypotheses、metrics 或 PASS／FAIL。不得用此結果判斷 Persona、NotebookLM 或 Skill 的產品價值。詳見 `docs/reports/2026-08-22-gauntlet-loop-field-trial.md`。

## Phase 6：排程（未列入第一版）

- launchd / cron / Task Scheduler。
- `auth refresh --quiet`。
- Scheduled mode 預設只能研究並產生 review plan，不自動刪除。

---

## 11. 測試計畫

### Unit tests

- Profile 與 Watch Item schema validation。
- Persona 不預設或注入技術角色。
- URL canonicalization。
- Exact/near duplicate detection。
- Source budget。
- Pinned protection。
- Add-before-delete invariant。
- Timeout resume/reconciliation。
- Export 不包含 credentials。
- Backend capability downgrade。

### Contract tests

同一組測試套用 FakeBackend 與 GeminiNotebookBackend：

- create/configure/get config
- list/refresh/delete source
- research start/poll/selective import
- ask with citations

### Live E2E（opt-in）

使用 disposable Notebook：

1. 建立並套用 Persona。
2. 加入一個 pinned source。
3. 執行小型 research。
4. Preview 不修改來源。
5. 核准一個 addition。
6. 驗證 source ready。
7. 嘗試刪除 pinned source，必須被阻止。
8. 匯出 bundle。
9. 清理 disposable Notebook。

---

## 12. Release 與遷移

這是產品範圍與 backend 的重大變更，建議發 `v2.0.0`。

### v2.0.0 第一版

- Thin Skill
- GeminiNotebookBackend
- Notebook create/adopt
- Persona configuration
- Manual Evergreen refresh preview
- Confirmed safe apply
- Export bundle

### Legacy

- v1.x 保留 tag/branch。
- 不在 v2 繼續承諾 Patchright browser backend。
- 提供簡短 migration guide：舊 notebook ID → adopt → 建立 profile。
- 暫不遷移舊的 project-folder library 功能。

---

## 13. 最終驗收標準

第一版只有在以下全部成立時才算完成：

1. 使用者可建立或 adopt 一本 Notebook。
2. 可在建立時指定 Persona 與 response length。
3. Persona 失敗不會被回報成成功。
4. 可保存長期 Research Profile 與跨領域 Watch Items。
5. 手動觸發一次 Deep Research 更新。
6. 更新前先產生 preview。
7. 能 selective import 並確認 ready。
8. 能產生「自上次更新以來有什麼變化」摘要，並分開呈現支持、反駁、衝突與未知證據。
9. Persona 可以是任意領域；技術雷達只作為可選模板。
10. Pinned source 不會被刪除。
11. 新來源失敗時不會刪除任何舊來源。
12. 所有刪除都需確認並先備份可取得內容。
13. 可匯出 backend-neutral bundle。
14. 除首次登入外，核心流程不依賴 UI selector 或可見瀏覽器。

---

## 14. 研究來源

本計畫於 2026-08-22 使用 Crawl4AI 檢查：

- Gemini Notebook 官方「在筆記本加入或探索新來源」說明。
- `teng-lin/notebooklm-py` 0.8.1 README、SKILL、CLI Reference、Python API。
- Research selective import、verified import、source freshness/refresh public API。
- 本專案 README Roadmap、`[LIVE]` 設計與既有 freshness 討論記錄。

官方與 unofficial RPC 都可能變動，因此 Evergreen Orchestrator 必須只依賴 backend public contract，並以 capability flags 處理功能差異。
