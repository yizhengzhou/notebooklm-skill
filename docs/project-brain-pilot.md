# Project Brain 第一階段測試指南

> 目前範圍：project-local Notebook binding、向上 discovery、live backend status、Registry drift、source capacity guard、review-only onboarding plan、明確 source roles、grounding coverage，以及第一批 read-only MCP tools。自動同步與 NotebookLM Studio artifact tools 尚未接通。

## 1. 確認 NotebookLM authentication

```bash
.venv/bin/notebooklm auth check --test --json
```

成功條件：`status == "ok"` 且 `checks.token_fetch == true`。

## 2. 列出已登記 Advisor

```bash
.venv/bin/python -m notebooklm_skill.cli list-advisors
```

若要建立新的 Advisor，先準備 config 並執行：

```bash
.venv/bin/python -m notebooklm_skill.cli setup --config advisor.json
```

## 3. 在自己的專案建立 project-local binding

```bash
.venv/bin/python -m notebooklm_skill.cli brain-init \
  --project-root /absolute/path/to/my-project \
  --advisor-id MY_ADVISOR_ID
```

這只會建立：

```text
my-project/.notebooklm/brain.json
```

不會上傳、刪除或修改 Notebook sources，也不會改寫 `AGENTS.md`。

如果 manifest 已綁定同一 Advisor，命令可安全重跑；若已綁定另一個 Notebook，命令會拒絕覆寫。

## 4. 從專案任意子目錄測試 discovery

```bash
cd /absolute/path/to/my-project/src/some/nested/folder
/path/to/notebooklm-skill/.venv/bin/python \
  -m notebooklm_skill.cli brain-discover
```

預期：向父目錄找到 `.notebooklm/brain.json`，回傳完整 Notebook ID；找不到 manifest 時不得猜最近使用的 Notebook。

## 5. 檢查 live status

```bash
/path/to/notebooklm-skill/.venv/bin/python \
  -m notebooklm_skill.cli brain-status
```

輸出包含：

- project root／manifest path。
- Advisor ID／Notebook ID／Notebook title。
- 本機 Registry source count。
- NotebookLM backend authoritative source count。
- Registry/backend drift。
- live source limit、remaining、tier、warning state。
- grounding coverage、缺少角色、stale roles 與是否允許解釋專案。

## 6. 由負責該專案的 Agent 產生 onboarding 候選計畫

```bash
/path/to/notebooklm-skill/.venv/bin/python \
  -m notebooklm_skill.cli brain-onboarding-plan
```

預設產生：

```text
.notebooklm/plans/onboarding-plan.json
.notebooklm/plans/onboarding-plan.md
```

這一步只用保守的檔名規則尋找 README、architecture、status、ADR／decision、runbook 與 handoff 候選，不會上傳任何檔案。每筆候選都是 `review_required: true`。

**負責專案的 Agent 必須實際讀取候選內容**，確認它是目前有效的 canonical project document、沒有 secrets，而且角色正確；不能把檔名分類結果直接當成事實。

## 7. 核准後，以明確角色加入專案文件

例如：

```bash
/path/to/notebooklm-skill/.venv/bin/python \
  -m notebooklm_skill.cli source-add-file \
  --advisor-id MY_ADVISOR_ID \
  --file /absolute/path/to/my-project/README.md \
  --role project_overview \
  --state pinned
```

可用角色：

- `project_overview`
- `architecture`
- `current_status`
- `decisions`
- `runbook`
- `handoff`
- `external_research`
- `reference`

Project source 會保存 repository-relative path、內容 SHA-256 與目前 Git commit。若同名 backend source 的實際內容不同，命令會以 `SOURCE_CONTENT_MISMATCH` 拒絕把它標成 canonical source。

`source-add-file` 會真正新增 Notebook source，執行前應由使用者核准文件內容。

## 8. 執行 grounding coverage gate

```bash
/path/to/notebooklm-skill/.venv/bin/python \
  -m notebooklm_skill.cli brain-grounding-check
```

狀態：

- `research_only`：只有外部研究，禁止冒充專案解釋。
- `project_partial`：至少有一種 project role，但缺少必要角色。
- `project_ready`：必要角色都有明確來源，而且本地 hash 仍一致。
- `project_stale`：必要來源的本地檔案已變更或消失。
- `unknown`：沒有足夠分類或無法證明 freshness。

只有 `project_ready` 會回傳 `can_explain_project: true`。

## 9. 在新增來源前預估容量

```bash
/path/to/notebooklm-skill/.venv/bin/python \
  -m notebooklm_skill.cli source-capacity \
  --advisor-id MY_ADVISOR_ID \
  --planned-additions 5
```

容量規則：

- `<80%`：healthy。
- `80–89%`：warning。
- `90–99%`：critical。
- `100%`：exhausted。
- planned peak 超限：blocked_capacity。

`source-add-url`、`source-add-file` 與 reviewed research Apply 現在都會在 source-add RPC 前做 capacity preflight。新增後還會重新檢查 backend snapshot；來源沒有真正出現並 ready 時，不會寫入 Registry或回報成功。

## 10. 移除本地 binding

第一階段尚未提供正式 uninstall command。若只想取消 project-local binding，可刪除：

```bash
rm /absolute/path/to/my-project/.notebooklm/brain.json
```

若 `.notebooklm/` 已空，可再刪除該目錄。這不會刪除 Notebook、Advisor state 或任何 Notebook sources。

## 目前限制

- `brain-init` 目前只能綁定已存在的 Advisor；之後會整合成單一 create/adopt onboarding。
- Project-local MCP／Skill 可由 Agent installer 安裝；新設定需要 client reload／restart，Pi 還要求 project trust。
- 核心文件候選目前只靠保守檔名 heuristic；正式主詞仍是負責專案且實際讀過內容的 Agent。
- 尚未自動上傳、替換或同步核心專案文件。
- 已提供 Agent-direct project-local installer，目前支援 Pi、Claude Code 與 generic Agent Skills + MCP layout；其他 client 需明確選擇相容 layout 或後續擴充。
- MCP source mutation 與 Studio artifact generation 尚未開放。
- `project_ready` 目前證明角色完整與本地 hash 一致；更完整的 Git lineage／sync policy 仍待實作。
- 不要把這個 pilot 當成已完成的 Project Brain。
