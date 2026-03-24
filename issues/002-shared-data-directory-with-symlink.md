# Issue #002: Symlink 安裝導致 data/ 全局共享

**狀態：** 開放
**嚴重程度：** 中 — 不影響功能，但破壞專案隔離
**發現日期：** 2026-03-23
**發現場景：** 將 `~/.claude/skills/notebooklm` 從獨立副本改為 symlink 指向 repo

---

## 問題描述

當 skill 以 symlink 方式安裝（`~/.claude/skills/notebooklm → /path/to/repo`）時，`data/` 目錄也被共享。這意味著：

- **library.json 是全局的** — 所有專案的 agent 都看到所有 notebook，包括與當前專案無關的
- **auth_info.json 是全局的** — 這其實是好事（只需認證一次）
- **browser_state/ 是全局的** — 也是好事（session 共享）

問題在於 library.json：一個語言學習專案的 agent 不應該看到華鋒精密的 AI 轉型策略 notebook，反之亦然。

## 影響

- Agent 在 `notebook_manager.py search` 時可能匹配到不相關的 notebook
- Notebook 清單混亂，用戶需要手動過濾
- 若兩個專案同時寫入 library.json 可能產生衝突（理論上，因為 Claude Code 單執行緒）

## 建議方案

### 方案 A：Per-project data（推薦）
讓 `library.json` 的路徑可配置，優先讀取專案目錄下的 `.notebooklm/library.json`，fallback 到 skill 目錄的全局版本。

```
專案 A/.notebooklm/library.json  → 只有專案 A 的 notebook
專案 B/.notebooklm/library.json  → 只有專案 B 的 notebook
~/.claude/skills/notebooklm/data/library.json → 全局 fallback
```

**優點：** 完全隔離，符合「一個專案一個 notebook」的哲學
**缺點：** 需要修改 notebook_manager.py 的路徑解析邏輯

### 方案 B：使用 `$CLAUDE_PLUGIN_DATA`
Thariq 的文章提到 `${CLAUDE_PLUGIN_DATA}` 作為 per-plugin 的穩定資料目錄。如果 Claude Code 支援此變數，直接用它存 library.json。

**優點：** 符合官方建議
**缺點：** 需確認此變數的可用性和行為

### 方案 C：維持現狀
library.json 裡多幾個不相關的 notebook 不影響核心功能。等用戶量增加或產生實際困擾時再處理。

## 相關檔案

- `scripts/notebook_manager.py` — library.json 的讀寫邏輯
- `scripts/config.py` — `LIBRARY_FILE` 路徑定義
- `data/library.json` — 目前的全局 notebook 清單

## 臨時解法

目前已將舊版的 notebook（華鋒精密、履歷作品集）合併到 repo 的 library.json，避免資料丟失。這些記錄對本 skill 開發專案無關，但刪除會影響其他專案的 agent 查找 notebook。
