# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-03-24

**Methodology update:** This release adopts the [harness engineering](https://openai.com/index/harness-engineering/) pattern emerging in 2026 — specifically the principle that planning and execution should be explicitly separated. We restructured the skill's core architecture from "one notebook per project" to "two notebooks per project" (Research + Project) to align with this methodology. / **方法論更新：** 本版本採用 2026 年興起的 [harness engineering](https://openai.com/index/harness-engineering/) 模式 — 特別是規劃與執行應明確分離的原則。我們將 skill 的核心架構從「一個專案一個筆記本」重構為「一個專案兩個筆記本」（Research + Project）以對齊此方法論。

### Added / 新增
- **Create Notebook (`create_notebook.py`)** — Automatically create new NotebookLM notebooks via browser automation / 透過瀏覽器自動化自動建立新的 NotebookLM 筆記本
  - `--pair` mode creates Research + Project notebook pair in one command / `--pair` 模式一次建立 Research + Project 筆記本配對
  - `--tone` presets: `default` (balanced), `vc` (investment lens), `critic` (harsh) / 語氣預設：平衡、創投視角、嚴苛批評
  - Auto-configures personas for both notebooks on creation / 建立時自動設定兩個筆記本的角色
  - Snapshot-based recovery: if URL redirect fails, finds new notebook via homepage diff / 快照式復原：URL 重定向失敗時，透過首頁差異找到新筆記本
  - Notebooks are automatically registered in the library with role and linking metadata / 自動註冊到圖書館，含角色和配對資訊
- **Dual-Notebook Architecture** — Harness engineering-inspired planning/execution separation / 受 Harness Engineering 啟發的規劃/執行分離架構
  - `role` field ("research" or "project") for notebook routing / 筆記本角色欄位（research 或 project）用於查詢路由
  - `paired_with` field links Research ↔ Project notebooks / `paired_with` 欄位連結 Research ↔ Project 筆記本
  - Query routing guidance in SKILL.md for agent-driven notebook selection / SKILL.md 中的查詢路由指引
- **`[LIVE]` source prefix convention** — Mark sources that may become outdated (API docs, prompt guides) for manual refresh awareness / 標記可能過時的來源（API 文件、提示詞指南）以提醒手動更新
- **Improved category prefix guidance** — Clear decision criteria for `[用戶痛點]` vs `[競品分析]` / 改善分類前綴指引

### Fixed / 修復
- **Source rename targets correct element** — Uses `querySelectorAll` + last match instead of `querySelector` / 來源重新命名現在定位到正確的元素
- **Post-rename verification** — Confirms rename actually took effect, no more silent failures / 重新命名後驗證，不再靜默失敗

## [1.3.2] - 2026-03-22

### Fixed / 修復
- **Source Rename Targets Wrong Element / 來源重新命名定位錯誤** - When a notebook already contains sources named "貼上的文字", rename now correctly targets the most recently added source instead of the first match / 當 notebook 中已存在名為「貼上的文字」的來源時，rename 現在正確定位到最新加入的來源而非第一個匹配項
  - Changed `querySelector` (first match) to `querySelectorAll` + last element (most recent) / 將 `querySelector`（第一個匹配）改為 `querySelectorAll` + 取最後一個（最新的）
  - Added post-rename verification — checks the new name actually appears in the source list / 新增 rename 後驗證 — 檢查新名稱是否確實出現在來源清單中
  - Rename now returns `False` on verification failure instead of silent success / rename 驗證失敗時回傳 `False`，不再靜默回報成功

### Improved / 改進
- **Category Prefix Guidance / 分類前綴指引** - Added decision criteria for choosing between `[用戶痛點]` and `[競品分析]` prefixes / 新增 `[用戶痛點]` 和 `[競品分析]` 前綴的選擇標準
- **Query Workflow Prefix Hints / 查詢流程前綴提示** - Agent is now reminded to use category prefixes at both the query step and follow-up mechanism / Agent 在查詢和追問兩個流程點都會被提醒使用分類前綴

## [1.3.1] - 2026-03-21

### Fixed / 修復
- **Multi-Account Auth Bug / 多帳號認證錯誤** - Users with multiple Google accounts no longer silently authenticate as the wrong account / 多 Google 帳號用戶不再靜默登入錯誤帳號
  - New `extract_authuser()` parses `authuser` parameter from notebook URLs / 新增 `extract_authuser()` 從 notebook URL 解析 `authuser` 參數
  - New `diagnose_access_denied()` detects "needs access" pages via text pattern matching (EN/zh-TW) / 新增 `diagnose_access_denied()` 以文字比對偵測「需要存取權」頁面
  - `setup_auth()` now saves which `authuser` index was used during login / `setup_auth()` 登入後儲存使用的 `authuser` 索引
  - `validate_auth()` checks authuser mismatch before launching browser / `validate_auth()` 在啟動瀏覽器前檢查 authuser 是否匹配
  - `ask_question.py` shows actionable error with re-auth instructions instead of generic DOM errors / `ask_question.py` 顯示可操作的錯誤訊息與重新認證指示，取代無意義的 DOM 錯誤
  - Single-account users are unaffected / 單帳號用戶不受影響（所有檢查以 authuser 存在為前提）

## [1.0.0] - 2026-03-21

### Added / 新增
- **Initial public release / 首次公開發布**
- NotebookLM integration via Patchright browser automation / 透過 Patchright 瀏覽器自動化整合 NotebookLM
- Modular architecture: `config.py`, `browser_utils.py`, `browser_session.py` / 模組化架構
- Query interface (`ask_question.py`) with 120s timeout and stability detection / 查詢介面，120 秒逾時，穩定性偵測
- Notebook library management (`notebook_manager.py`) / 筆記本庫管理
- Notebook guide / persona configuration (`set_notebook_guide.py`) / 對話角色設定
- Source upload with auto-rename (`add_source.py`) / 來源上傳與自動重新命名
- Google authentication with persistent sessions (`auth_manager.py`) / Google 認證與持久 session
- Thinking message detection — waits for streaming to complete / Thinking 訊息偵測
- CSS selectors for current NotebookLM UI / 當前 NotebookLM UI 的 CSS selectors
