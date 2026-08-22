# 使用指南

本指南描述目前 v2 CLI 已實作的功能。舊 `scripts/` 是 Legacy v1，不是目前操作入口。

## 1. 安裝

需求：Python 3.11 或 3.12。

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

確認 CLI：

```bash
.venv/bin/notebooklm-evergreen --help
# 或
.venv/bin/python -m notebooklm_skill.cli --help
```

## 2. NotebookLM 登入

```bash
.venv/bin/notebooklm login
.venv/bin/notebooklm auth check --test --json
```

成功條件：

```json
{
  "status": "ok",
  "checks": {
    "token_fetch": true
  }
}
```

Google cookies／tokens 由 `notebooklm-py` 保存，不會寫入 Advisor Profile 或 export。

## 3. 建立設定檔

建立 `advisor.json`：

```json
{
  "advisor_id": "gauntlet-loop",
  "title": "Gauntlet Loop Research",
  "persona": {
    "instructions": "主要服務對象是一位正在評估 Gauntlet Loop 的開發者。根據來源回答，區分來源事實、推論與未知。",
    "response_length": "longer"
  },
  "research": {
    "enabled": true,
    "brief": "研究 Gauntlet Loop 的起源、核心方法、公開實作、使用案例、限制與近期發展。",
    "queries": [
      "Gauntlet Loop 的原始方法與必要條件是什麼？",
      "有哪些公開使用案例與可驗證結果？",
      "有哪些失敗案例、限制與反對證據？"
    ],
    "mode": "deep",
    "language": "zh-Hant",
    "recency_days": 90,
    "max_new_sources_per_run": 6,
    "preferred_domains": ["github.com"],
    "update_mode": "review",
    "deletion_mode": "confirm"
  },
  "watchlist": [
    {
      "watch_id": "watch-adoption",
      "kind": "assumption",
      "statement": "Gauntlet Loop 已有獨立實戰案例，而不只是 fork 或重新包裝。",
      "questions": ["哪些案例提供程式碼、demo 或完整紀錄？"],
      "revisit_when": ["出現新的公開案例或 postmortem"],
      "status": "active"
    }
  ]
}
```

### Persona 欄位的目前含義

`persona.instructions` 會直接設定為 NotebookLM Custom Chat instructions。它不是獨立的 End-user Persona model。使用者應自行決定要如何描述服務對象、專業視角與資訊需求。

`response_length` 支援：

- `default`
- `longer`
- `shorter`

## 4. 建立或接管 Notebook

### 建立新 Notebook

```bash
.venv/bin/notebooklm-evergreen setup --config advisor.json
```

成功輸出包含：

- `advisor_id`
- `notebook_id`
- `persona_verified: true`

如果 Notebook 已建立但 custom instructions 設定失敗，錯誤會保留 Notebook ID；不要直接重建另一個 Notebook。

### 接管既有 Notebook

```bash
.venv/bin/notebooklm-evergreen setup \
  --config advisor.json \
  --adopt-notebook-id NOTEBOOK_ID
```

接管時會把既有來源登錄為 `active`，不會自動 Pin 或刪除。

## 5. 查看本機狀態

```bash
.venv/bin/notebooklm-evergreen show --advisor-id gauntlet-loop
```

顯示 Notebook reference、Watch Item 數量、Source Registry 與 Refresh Run 數量。

## 6. 加入 canonical URL

```bash
.venv/bin/notebooklm-evergreen source-add-url \
  --advisor-id gauntlet-loop \
  --url https://github.com/robonuggets/gauntlet-loop \
  --state pinned
```

行為：

1. 驗證並 canonicalize HTTP／HTTPS URL。
2. 檢查 Registry 和 Notebook 是否已有相同 URL。
3. 沒有時才建立來源。
4. 等待來源變成 `ready`。
5. 成功後才寫入 Source Registry。
6. timeout 後重跑相同命令會優先 reconcile，不 blind duplicate。

`--state` 支援 `active` 或 `pinned`。

## 7. Pin 或分類既有來源

先用 `show` 找到 `local_id`，再執行：

```bash
.venv/bin/notebooklm-evergreen source-state \
  --advisor-id gauntlet-loop \
  --local-id src-EXAMPLE \
  --state pinned
```

支援 `active`、`pinned`、`broken`。Pinned source 不會由 Safe Apply 自動汰換。

## 8. 執行 Deep Research Preview

```bash
.venv/bin/notebooklm-evergreen preview \
  --advisor-id gauntlet-loop \
  --run-id preview-20260822 \
  --work-directory ./runs/preview-20260822 \
  --timeout 1800
```

Preview query 由以下內容組成：

- Research brief
- Research queries
- active Watch Items
- recency
- 最近成功 Refresh Run 時間

Preview 不會匯入或刪除來源。輸出：

```text
runs/preview-20260822/
├── checkpoint.json
├── preview.json
└── preview.md
```

如果 timeout，使用完全相同的 run ID 和 work directory 重跑。不要開始另一個 Deep Research task。

## 9. 審查候選來源

閱讀 `preview.md`／`preview.json`，建立 `selected-urls.json`：

```json
[
  "https://example.com/primary-source",
  "https://example.org/independent-review"
]
```

Selection 可以從完整 candidate pool 選擇，包括 Preview 排序後標記為 `over_budget` 的候選，但數量不能超過 Research Profile 的 source budget。

系統不會因候選排名自動視為已獲核准。

## 10. 建立 Apply Plan

```bash
.venv/bin/notebooklm-evergreen plan-apply \
  --advisor-id gauntlet-loop \
  --plan-id apply-20260822 \
  --preview ./runs/preview-20260822/preview.json \
  --selection ./runs/preview-20260822/selected-urls.json \
  --output-directory ./runs/apply-20260822
```

輸出：

```text
runs/apply-20260822/
├── apply-plan.json
└── apply-plan.md
```

Plan 是 review-only，不會執行 import。使用者必須審查來源與 `plan_digest`。

### 可選 retirement file

```json
{
  "src-old": {
    "replacement_url": "https://example.com/replacement",
    "reason": "新的 primary source 已取代舊來源。"
  }
}
```

加入：

```bash
--retirements retirements.json
```

Replacement 必須是本次選入來源；Pinned source 不能進入 retirement plan。

## 11. Apply 核准 Plan

```bash
.venv/bin/notebooklm-evergreen apply \
  --advisor-id gauntlet-loop \
  --run-id refresh-20260822 \
  --plan ./runs/apply-20260822/apply-plan.json \
  --approved-digest EXACT_SHA256 \
  --evidence-directory ./runs/apply-20260822/execution
```

執行順序：

1. 驗證 digest 與 source snapshot。
2. 匯入明確選擇的來源。
3. 等待全部 ready。
4. 產生 delta summary。
5. 備份任何 retirement source 的 metadata／fulltext。
6. 重新確認 protected set。
7. 只刪除 Plan 明確核准的非 Pinned source。
8. 更新 Registry 並寫入 immutable Refresh Run。

任一步驟在刪除前失敗，都應 fail closed。以相同 run ID／digest 重跑時會 reconcile，避免重複 import 或歷史紀錄。

## 12. 檢查 URL／Drive freshness

### 建立 Refresh Plan

```bash
.venv/bin/notebooklm-evergreen refresh-plan \
  --advisor-id gauntlet-loop \
  --plan-id native-refresh-20260822 \
  --output-directory ./runs/native-refresh-20260822
```

### 執行核准 Refresh

```bash
.venv/bin/notebooklm-evergreen refresh-apply \
  --advisor-id gauntlet-loop \
  --run-id native-refresh-20260822 \
  --plan ./runs/native-refresh-20260822/refresh-plan.json \
  --approved-digest EXACT_SHA256 \
  --work-directory ./runs/native-refresh-20260822/execution
```

系統只使用 NotebookLM native freshness／refresh。Drive source 不會 delete + re-add，source ID 必須保持不變。

`missing`、`broken`、`syncing` 或 unknown 不代表 obsolete，也不會自動取得刪除許可。

## 13. Ask

直接提問：

```bash
.venv/bin/notebooklm-evergreen ask \
  --advisor-id gauntlet-loop \
  --question "根據來源，Gauntlet Loop 最重要的限制是什麼？"
```

從檔案提問：

```bash
.venv/bin/notebooklm-evergreen ask \
  --advisor-id gauntlet-loop \
  --question-file question.md
```

### 目前限制

- CLI 目前只輸出 answer string，尚未保存原生 citation/reference objects。
- 未指定 conversation ID 時會延續 Notebook 的 current conversation。
- CLI 尚未提供 explicit fresh-conversation mode。

因此這個命令目前適合基本操作，不適合需要嚴格 citation audit 或獨立實驗條件的工作。

## 14. Export

```bash
.venv/bin/notebooklm-evergreen export \
  --advisor-id gauntlet-loop \
  --destination ./exports/gauntlet-loop
```

Destination 必須不存在。Export 包含：

- Profile JSON
- Persona Markdown
- Watchlist
- Source Registry
- immutable Refresh Runs
- 可取得的 source fulltext
- unavailable／tombstone manifest

Export 不含 Google cookies、tokens 或 passwords。

## 15. State 位置

預設：

- macOS：`~/Library/Application Support/notebooklm-skill/advisors/`
- Linux：`~/.local/share/notebooklm-skill/advisors/`
- Windows：`%LOCALAPPDATA%/notebooklm-skill/advisors/`

Override：

```bash
export NOTEBOOKLM_SKILL_HOME=/path/to/notebooklm-skill-data
```

也可以在每個 CLI command 前使用：

```bash
--state-root /explicit/advisor/root
```

`--state-root` 必須放在 subcommand 前面。

## 16. 不應使用的功能

v2 不應呼叫：

- `scripts/run.py`
- Patchright browser automation
- 舊 Research／Project notebook pair workflow
- Git hook／project-folder auto upload

若明確維護 Legacy v1，才使用 `requirements-legacy.txt`。

## 17. 安全原則

- Add before delete。
- Pinned means protected。
- Missing is not obsolete。
- 不 blind import-all。
- 不 silent deletion。
- retirement 前先備份。
- timeout 後 resume／reconcile。
- Credential 不進 portable state。
- Live disposable resources 在 evidence 保存後清理。
