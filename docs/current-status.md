# 目前開發狀態與交接說明

> 更新日期：2026-08-22
>
> 公開版本：`2.0.0`，另有尚未發版的 CLI 增量功能
> 核心測試：Python 3.11／3.12 各 66 tests

## 1. 目前產品是什麼

本專案目前是一個建立在 `notebooklm-py 0.8.1` 上的薄層 NotebookLM Skill。它不取代 NotebookLM 的研究與問答能力，而是提供：

- Notebook 建立／接管與自訂 Chat instructions read-back
- 本機 Research Profile、Watchlist、Source Registry 與更新歷史
- 不修改來源的 Deep Research Preview
- 人工審查後的選擇性來源匯入
- Pinned source protection 與 add-before-delete
- URL／Drive 原生 refresh
- backend-neutral state 與 readable source fulltext export

目前 `persona` 欄位代表 **NotebookLM Custom Chat instructions**。專案尚未建立獨立的 End-user Persona 資料模型，也尚未驗證不同使用者 Persona 的產品價值。

## 2. 已完成能力

| 能力 | 狀態 | 使用入口 |
|---|---|---|
| 建立 Notebook | 已完成並 live smoke | `setup --config` |
| 接管既有 Notebook | 已完成 | `setup --adopt-notebook-id` |
| Custom Chat instructions + read-back | 已完成 | setup config 的 `persona` |
| 顯示本機狀態 | 已完成 | `show` |
| 加入 canonical URL | 已完成、尚未發版 | `source-add-url` |
| Pin／分類來源 | 已完成 | `source-state` |
| Deep Research Preview | 已完成並 live smoke | `preview` |
| timeout resume／task reconciliation | 已完成並 live smoke | 相同 run ID／work directory 重跑 |
| 人工 URL selection | 已完成、尚未發版 | `plan-apply --selection` |
| Digest-bound safe Apply | 已完成並 live smoke | `apply --approved-digest` |
| Pinned protection | 已完成並 live smoke | Apply invariants |
| retirement fulltext backup | 已完成並 live smoke | Apply execution evidence |
| URL／Drive native refresh | 已完成並 live smoke | `refresh-plan`／`refresh-apply` |
| Immutable Refresh Run | 已完成 | successful Apply／Refresh commit |
| 直接 Ask | 已完成、尚未發版 | `ask` |
| Portable export | 已完成 | `export` |
| Readable source fulltext export | 已完成並 live smoke | `export` |
| Offline Fake Backend | 已完成 | pytest |
| Python 3.11／3.12 CI | 已完成 | GitHub Actions |

## 3. 已知限制

### Ask 仍不是完整的 NotebookLM fidelity interface

目前 `ask` 只保存 answer string，尚未保存 NotebookLM 原始：

- references／citation objects
- conversation ID
- turn metadata
- fresh conversation／follow-up 的明確選擇

`notebooklm-py` 在未指定 conversation ID 時會延續 current conversation。使用者不應把目前 CLI 的每次 `ask` 視為獨立問題。

### User Persona 尚未建模

目前的 `PersonaProfile` 是 NotebookLM Custom Chat instructions，不是使用者研究 Persona。以下能力尚未完成：

- End-user role／goal／expertise／constraints model
- 將 User Persona 轉換成 NotebookLM instructions
- 同來源下不同 Persona 的可重現比較
- Persona 效果的有效 A/B test

### 尚未實作

- 排程器（launchd／cron／Task Scheduler）
- 通知
- Open Notebook backend
- Studio artifact generation
- 專案資料夾掃描與 Git hooks
- 自動 project document upload
- 獨立的 User Persona product layer

## 4. 各計畫狀態

### `docs/plans/2026-03-24-create-notebook-dual-role.md`

- **狀態：Legacy v1 historical plan**
- 原本使用 Patchright，建立 Research／Project 雙 Notebook。
- 對應程式仍保留在 `scripts/`，但不屬於 v2 runtime。
- 不應作為目前安裝或使用指南。

### `docs/plans/2026-08-22-upstream-realignment.md`

- **狀態：重新對齊研究，已由主計畫承接**
- 確認舊 browser automation 技術債。
- 確認採用 `notebooklm-py 0.8.1`。
- 歷史決策仍有參考價值，但實作狀態以主計畫為準。

### `docs/plans/2026-08-22-thin-skill-evergreen-notebook.md`

- **狀態：目前主計畫**
- Phase 0：測試安全基線，完成。
- Phase 1：Backend／create-adopt／custom instructions read-back，完成。
- Phase 2：Profile／Registry／Refresh Run／export storage，完成。
- Phase 3：non-mutating resumable research Preview，完成。
- Phase 4：review plan 與 safe Apply，完成。
- Phase 5：native source refresh 與 release integration，完成。
- Phase 5D engineering additions：`source-add-url`、`ask`、explicit selection，完成。
- Phase 5D Persona／產品價值實驗：**無效，不可作為產品結論**。
- Phase 6 scheduling：未開始。

## 5. Phase 5D 實驗狀態

Gauntlet Loop field trial 同時改變來源數量、研究內容、問題順序與 conversation history，而且 Control／Treatment 使用相同 NotebookLM custom instructions。它不能判斷 Persona 的效果，也不能證明 Skill 相較手動 NotebookLM 的產品價值。

報告只保留作為失敗實驗與原始回答索引：

- `docs/reports/2026-08-22-gauntlet-loop-field-trial.md`

後續 Agent 不應引用該實驗作為 Persona 有效／無效、NotebookLM 改善／劣化或產品有／無價值的證據。

## 6. Live smoke 已確認的工程事實

- Persona/custom instructions 可設定並 read back。
- Deep Research task 可 timeout 後 resume，不必重跑。
- Preview 不修改 source snapshot。
- Safe Apply 可先 import、等待 ready、產生 delta、備份，再刪除明確核准的非 Pinned source。
- Drive refresh 使用 native freshness／refresh，source ID 不變。
- Disposable live resources 已清理。
- 正式 Advisor state 目前為 0。

這些是工程能力驗證，不等於終端產品價值驗證。

## 7. 給下一位 Agent 的起點

1. 先閱讀本文件與 `docs/user-guide.md`。
2. 不要使用 Legacy `scripts/` 作為 v2 runtime。
3. 不要沿用 Phase 5D 的 Persona 結論。
4. 若要做 Persona 實驗，必須先 pre-register，固定來源／問題／conversation，只改一個設定變數。
5. 若要修改 `ask`，優先保留原生 references 與 conversation metadata。
6. 所有 live resource／quota 操作仍需明確 Gate。
