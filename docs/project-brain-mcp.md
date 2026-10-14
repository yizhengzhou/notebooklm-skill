# Project Brain MCP（第一批 read-only tools）

## 啟動命令

```bash
/absolute/path/to/notebooklm-skill/.venv/bin/notebooklm-project-brain-mcp
```

使用 stdio transport。MCP process 的 `cwd` 應設為目標專案根目錄或其子目錄，讓 tools 能從 `.notebooklm/brain.json` 向上 discovery。

## 通用 project-local 設定範例

不同 Agent client 的設定檔位置可能不同；server definition 可使用：

```json
{
  "mcpServers": {
    "project-brain": {
      "command": "/absolute/path/to/notebooklm-skill/.venv/bin/notebooklm-project-brain-mcp",
      "args": [],
      "cwd": "/absolute/path/to/my-project"
    }
  }
}
```

不要把 NotebookLM cookies、tokens 或 browser storage 放進專案設定。Authentication 仍由 `notebooklm-py` 的本機 profile 管理。

## Tools

### `brain_discover`

從 `project_path` 向上尋找最近的 `.notebooklm/brain.json`。找不到就回傳錯誤，不猜 Notebook。

### `brain_capabilities`

回傳目前 MCP batch 支援矩陣。目前 source mutation 與 artifact generation 明確為 `false`。

### `brain_health`

檢查：

- manifest／Advisor binding 是否一致。
- Notebook 是否可存取。
- Registry source count 與 backend authoritative count。
- source capacity。
- grounding coverage。

### `brain_grounding_check`

回傳 `research_only`、`project_partial`、`project_ready`、`project_stale` 或 `unknown`。只有 `project_ready` 的 `can_explain_project` 是 `true`。

### `brain_onboarding_plan`

回傳 review-only 文件候選，不寫檔、不上傳。負責專案的 Agent 必須實際讀取候選內容後，才能提議使用 `source-add-file --role ...`。

### `brain_ask`

參數：

- `question`
- `project_path`
- `purpose`: `project_explanation`（預設）、`general`、`external_research`
- `fresh`

`purpose=project_explanation` 時，grounding 不是 `project_ready` 會以 `PROJECT_GROUNDING_INSUFFICIENT` fail closed。

### `brain_recover`

要求 NotebookLM根據 overview、architecture、current status 與 decisions 恢復專案上下文。只允許 `project_ready`。

## 邊界

- 這批 MCP tools 不新增、替換、刪除或生成 Notebook 內容。
- NotebookLM回答是 advisory evidence，不取代程式碼、Git、測試或 runtime 證據。
- `brain_onboarding_plan` 的 filename classification 只是候選，不是 canonical 判定。
- Source upload 目前仍使用 CLI，而且必須由使用者核准。
- Studio artifacts 會在後續 batch 接入，並保留 confirmation gate。
