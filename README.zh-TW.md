# 常青 Gemini Notebook Skill

這是一個精簡、審查優先的 orchestration layer，用來把一本 Gemini Notebook／
NotebookLM Notebook 建成長期存在的跨領域研究參謀。

底層 Notebook 操作全部委派給
[`notebooklm-py`](https://github.com/teng-lin/notebooklm-py)。v2 不維護
NotebookLM DOM selector、browser daemon、cookie workaround、專案資料夾掃描或
Git hook。

## 能做什麼

- 建立或接管一本 Notebook。
- 套用並讀回驗證自訂 Persona 與回覆長度。
- 保存 Research Profile 與 assumption／decision／trend／risk Watchlist。
- 執行可恢復、且不修改來源的 Deep Research Preview。
- 審查後選擇性匯入候選來源。
- 保護 Pinned source，強制 add-before-delete。
- 在確認汰換前備份舊來源內容。
- 使用原生 sync 更新 URL／Drive 來源，絕不 delete + re-add。
- 保存不可覆寫的更新歷史，並匯出 backend-neutral state。

Persona 不預設為技術角色，可用於心理、哲學、醫療、市場、產品、技術或跨領域
組合。目前 `persona` 欄位代表 NotebookLM Custom Chat instructions，尚未實作獨立的
End-user Persona model。Studio artifact generation instructions 與 Chat Persona 分開處理。

## 狀態與指南

- [目前實作狀態與交接](docs/current-status.md)
- [完整使用指南](docs/user-guide.md)
- [文件索引](docs/README.md)

Phase 5D Gauntlet Loop Persona 實驗已標記為 **無效**，不得作為產品價值證據；該階段
新增的工程功能仍有測試覆蓋。

## 安裝

需求：Python 3.11／3.12、Google 帳號及 NotebookLM 使用權限。

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/notebooklm login
.venv/bin/notebooklm auth check --test --json
```

## 快速開始

建立 `advisor.json`：

```json
{
  "advisor_id": "market-watch",
  "title": "市場變化參謀",
  "persona": {
    "instructions": "你是以證據為基礎的市場研究顧問。區分事實、推論、衝突與未知。",
    "response_length": "longer"
  },
  "research": {
    "enabled": true,
    "brief": "持續追蹤重要市場與競爭變化。",
    "queries": ["最近有什麼變化？", "哪些證據挑戰既有假設？"],
    "mode": "deep",
    "language": "zh-Hant",
    "recency_days": 90,
    "max_new_sources_per_run": 10,
    "preferred_domains": [],
    "update_mode": "review",
    "deletion_mode": "confirm"
  },
  "watchlist": []
}
```

建立新 Notebook：

```bash
.venv/bin/python -m notebooklm_skill.cli setup --config advisor.json
```

接管既有 Notebook：

```bash
.venv/bin/python -m notebooklm_skill.cli setup \
  --config advisor.json --adopt-notebook-id NOTEBOOK_ID
```

加入並保護 canonical URL seed：

```bash
.venv/bin/python -m notebooklm_skill.cli source-add-url \
  --advisor-id market-watch \
  --url https://example.com/canonical-guide \
  --state pinned
```

執行不修改來源的研究 Preview：

```bash
.venv/bin/python -m notebooklm_skill.cli preview \
  --advisor-id market-watch \
  --run-id preview-20260822 \
  --work-directory ./runs/preview-20260822
```

建立 Apply Plan：

```bash
.venv/bin/python -m notebooklm_skill.cli plan-apply \
  --advisor-id market-watch \
  --plan-id apply-20260822 \
  --preview ./runs/preview-20260822/preview.json \
  --selection ./runs/preview-20260822/selected-urls.json \
  --output-directory ./runs/apply-20260822
```

審查並核准精確 digest 後才 Apply：

```bash
.venv/bin/python -m notebooklm_skill.cli apply \
  --advisor-id market-watch \
  --run-id refresh-20260822 \
  --plan ./runs/apply-20260822/apply-plan.json \
  --approved-digest SHA256 \
  --evidence-directory ./runs/apply-20260822/evidence
```

完整 Agent 操作契約見 [`SKILL.md`](SKILL.md)，儲存、Preview、Safe Apply、
Source Refresh、測試與本機 runtime 細節見 [`docs/`](docs/)。

## 安全規則

- 永遠先新增，再考慮刪除。
- Pinned 永遠受保護。
- Missing 不等於 obsolete。
- 不可 blind import-all。
- 不可 silent deletion。
- 汰換前先備份並確認。
- timeout 後 resume／reconcile，不重複執行。
- Credential 不可進入可攜 state。

Disposable 測試資源在成功保存 evidence 後自動清理；只有轉化成具名稱、用途、
owner 與維護責任的正式 regression asset 時才保留。

## 儲存與可攜性

```text
advisors/<advisor_id>/
├── profile.json
├── persona.md
├── watchlist.json
├── sources.json
└── refresh-runs/
```

預設位置：

- macOS：`~/Library/Application Support/notebooklm-skill/advisors/`
- Linux：`~/.local/share/notebooklm-skill/advisors/`
- Windows：`%LOCALAPPDATA%/notebooklm-skill/advisors/`

可用 `NOTEBOOKLM_SKILL_HOME` 覆蓋。匯出 bundle 不含 credential，並保留未來遷移
至非 Google backend 的能力。

## 開發

```bash
python3.11 -m pytest -q
python3.12 -m pytest -q
ruff check notebooklm_skill tests
```

離線測試使用 Fake Backend。Live test 必須使用 disposable 資源，並於 PASS 後自動
清理。

## Legacy v1

舊 Patchright 實作只保留在 `scripts/` 作為 migration reference，不屬於 v2 runtime，
也不再由 `requirements.txt` 安裝。只有明確維護 v1 時才安裝
`requirements-legacy.txt`。

## MVP 範圍外

排程（launchd／cron／Task Scheduler）、Open Notebook backend、專案資料夾自動上傳、
Git hooks 與 Studio artifact generation 不在 v2.0 MVP。
