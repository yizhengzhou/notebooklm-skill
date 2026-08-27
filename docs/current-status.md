# 目前開發狀態與交接說明

> 更新日期：2026-08-27
>
> 公開版本：`2.0.0`，另有已推上 `main` 但尚未發版的 CLI 增量功能
> 核心測試：77 tests (100% PASS)，`ruff check` clean

## 1. 目前產品是什麼

本專案目前是一個建立在 `notebooklm-py 0.8.1` 上的薄層 NotebookLM Skill。它不取代 NotebookLM 的研究與問答能力，而是提供：

- Notebook 建立／接管與自訂 Chat instructions read-back
- 本機 Research Profile、Watchlist、Source Registry 與更新歷史
- 不修改來源的 Deep Research Preview
- 人工審查後的選擇性來源匯入
- Pinned source protection 與 add-before-delete
- URL／Drive 原生 refresh
- backend-neutral state 與 readable source fulltext export
- **結構化 Citation & Highlight 原文對照表渲染 (Ask Fidelity Interface)**
- **內建 Strict Grounding 高可信度防幻覺與因果約束範本**
- **本地檔案文字來源匯入（`source-add-file`，2026-08-26 新增）**

目前 `persona` 欄位代表 **NotebookLM Custom Chat instructions**。

## 2. 已完成能力

| 能力 | 狀態 | 使用入口 |
|---|---|---|
| 建立 Notebook | 已完成並 live smoke | `setup --config` |
| 接管既有 Notebook | 已完成 | `setup --adopt-notebook-id` |
| Custom Chat instructions + read-back | 已完成 | setup config 的 `persona` |
| 顯示本機狀態 | 已完成 | `show` |
| 加入 canonical URL | 已完成、尚未發版 | `source-add-url` |
| 加入本地檔案（文字來源） | **已完成並通過真實 Notebook live smoke** | `source-add-file` |
| Pin／分類來源 | 已完成 | `source-state` |
| Deep Research Preview | 已完成並 live smoke | `preview` |
| timeout resume／task reconciliation | 已完成並 live smoke | 相同 run ID／work directory 重跑 |
| 人工 URL selection | 已完成、尚未發版 | `plan-apply --selection` |
| Digest-bound safe Apply | 已完成並 live smoke | `apply --approved-digest` |
| Pinned protection | 已完成並 live smoke | Apply invariants |
| retirement fulltext backup | 已完成並 live smoke | Apply execution evidence |
| URL／Drive native refresh | 已完成並 live smoke | `refresh-plan`／`refresh-apply` |
| Immutable Refresh Run | 已完成 | successful Apply／Refresh commit |
| 直接 Ask（含 Citation 對照表） | **已升級完成並通過實測** | `ask` |
| 強制全新 conversation（`--fresh`）／指定既有 conversation | **2026-08-27 新增** | `ask --fresh`／`ask --conversation-id` |
| Portable export | 已完成 | `export` |
| Readable source fulltext export | 已完成並 live smoke | `export` |
| Offline Fake Backend | 已完成 | pytest (77 tests) |
| Python 3.11／3.12 CI | 已完成 | GitHub Actions |

## 3. 已知限制與後續規劃

### Provider-side artifact 行為已釐清並納入 Policy 規劃

Google 官方說明指出，第一次加入來源時有時會自動建立起步 artifact；Pro／Ultra Chat 也具有建立檔案與修改 artifact 的 agentic actions。目前 Ask／Apply 已明確建立 Artifact Snapshot & Observe 規劃。研究與修正建議見 `docs/reports/2026-08-22-notebooklm-official-auto-summary-and-artifact-research.md`。

### `source-add-file` 目前只支援單檔，沒有批次／自動分類

`source-add-file` 一次只加一個檔案，靠使用者或呼叫端自己決定要加哪些檔案、下什麼
title。**沒有**專案資料夾掃描、沒有依內容自動分類、沒有像 `docs/onboarding-existing-projects.md`
描述的「654 個檔案 → 過濾 → 合併 → 批次匯入」流程——那份文件描述的批次能力
在 v2 下不存在，只是現在多了一個檔案層級的手動入口。

### Onboarding 文件已標示 Legacy v1，尚未有對應 v2 文件

`docs/onboarding-existing-projects.md` 與 `docs/verifyai-import-plan.md` 描述的是
雙 Notebook、`scripts/run.py`（`--pair`、`add_source.py`）架構，違反本文件 v2
Runtime Contract（見 SKILL.md「Runtime contract」節）。兩份文件開頭都已加上
Legacy v1 警語，**不要照裡面的指令執行**；但目前沒有對應的、真正描述 v2 單一
Advisor 流程的「既有專案 onboarding」文件——如果要做，`source-add-file` 已經
是可用的地基。

### 待推進功能

- Source Hydration Quality Gate（Commit 前過濾 503 錯誤頁）
- 排程器（launchd／cron／Task Scheduler）
- 通知
- Open Notebook backend
- 候選來源互動式審查表（免手改 JSON）
- v2 版「既有專案 onboarding」文件（批次匯入／自動過濾／分類，目前為空缺）

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
- 正式 Advisor state 目前為 2：`notebooklm-official-product-watch`（追蹤 Google 官方產品行為，4 份 Help 核心來源為 Pinned，2 份官方 Blog 為 active）；`localedit-global-local-sites`（外部試用專案 LocalEdit，2026-08-25 用 `source-add-file` 加入第一份 pinned 本地文字來源，實測成功）。
- `source-add-file` 已在真實帳號、真實 Notebook 上驗證成功（非 FakeBackend），含 `--state pinned`。
- **診斷技巧**：要查一個 Notebook 目前的 Deep Research 任務狀態，不需要知道我們自己 CLI 用的 `--run-id`／`--work-directory`，可以直接用底層套件的
  `notebooklm research status -n <notebook_id> --json`（`.venv/bin/notebooklm`），會回傳該 Notebook 目前任務的
  `task_id`／`status`／`sources`／`report`，不受本機 checkpoint 遺失影響。2026-08-26 用這個方法確認 `localedit-global-local-sites`
  的研究任務狀態是 `completed`（55 個候選來源、完整報告），並非卡住。
- **一個已修正的錯誤推論，記錄下來避免重犯**：不能拿「來源加入時間」與「事後查詢時間」的差距，去推論 Deep Research 實際跑了多久——中間可能包含人工暫停（例如等待使用者允許 agent 繼續執行的權限提示），這段時間不是後端處理時間。目前沒有可靠數據顯示 Deep Research 實際耗時超過 Case 1-3 建立的 331-356 秒基準；上述完成的任務唯一能確認的是「有完成、沒有卡死」，耗時本身未知。
- **一個已修好、但過去所有 live 測試都未曾避開的污染源**：`notebooklm-py` 本身的行為是「`ask()` 不指定 conversation_id 就一定延續現有對話」，唯一能開新對話的方式是先 `delete_conversation()`。這件事 Case 1 報告就已經懷疑過（「Apply 的 delta summary 與後續 Ask 共用同一 conversation」），但從未修過——`EvergreenService.ask()` 之前雖然收了 `conversation_id` 參數，實際上呼叫後端時卻沒有傳過去，形同虛設。2026-08-27 已修好並補上 `ask --fresh`。**這代表在這之前的所有 live 測試（Case 1-3、strict-grounding 重現實驗等）裡，同一個 Notebook 上連續問的第二題以後，都不能保證是獨立提問**，回頭引用那些報告的多輪對話結果時要把這個列入考量，不能當作互相獨立的量測。

這些是工程能力驗證，不等於終端產品價值驗證。

## 7. 給下一位 Agent 的起點

1. 先閱讀本文件與 `docs/user-guide.md`。
2. 不要使用 Legacy `scripts/` 作為 v2 runtime。
3. 不要沿用 Phase 5D 的 Persona 結論。
4. 若要做 Persona 實驗，必須先 pre-register，固定來源／問題／conversation，只改一個設定變數。
5. 若要修改 `ask`，優先保留原生 references 與 conversation metadata。
6. 所有 live resource／quota 操作仍需明確 Gate。
7. `docs/onboarding-existing-projects.md` 與 `docs/verifyai-import-plan.md` 是 Legacy v1，不要照著執行；需要匯入本地檔案時用 `source-add-file`（見第 3 節限制）。
8. 要查某個 Notebook 的 Deep Research 任務是否卡住，先用 `notebooklm research status -n <notebook_id> --json` 直接問後端，不要憑本機時間戳猜測耗時（見第 6 節）。
9. 修改後，若涉及對外溝通或使用者已在測試的功能，**當天結束前更新本文件**，不要只留在對話紀錄或散落的 `docs/reports/*.md` 裡——下一位 agent 預設只讀本文件。
10. 任何需要「這一題的答案不能被前一題影響」的測試（重複試驗、self-audit、對照組實驗），一定要用 `ask --fresh`，不要假設不指定 conversation ID 就是新對話——預設行為是延續現有對話。
11. **在設計任何新的 live 實驗之前，先讀 `docs/reports/2026-08-27-methodology-lessons.md`。** 2026-08-27 做 Persona 效果實驗時，一路犯過並修正過的方法論錯誤（pilot 沒做就放大規模、評分工具本身未驗證、把「有出現差異」直接當「有因果效果」、對隨機系統講「每次都」、想用樣本數解決外部效度問題）都記在那份文件，不要重蹈覆轍。
12. **Persona 的建議寫法與設計原則已經寫進 SKILL.md**（domain／互動姿態／輸出格式／不確定時要不要給建議／decision-history-awareness 五個維度，以及「只有對整個 Notebook 每一題都成立的東西才放 Persona，其餘放進單一問題」的判斷原則）。修改 Persona 相關文件前先讀那一段，不要重新發明。
13. **2026-08-27 的 Persona 效果實驗結論是「有限觀察，非定論」**（見 `2026-08-27-persona-effect-experiment-final-report.md`）：這次 27 次呼叫裡沒有捏造案例；Persona 強度對引用支撐率／因果跳躍率沒有測到符合預先門檻的效果；Strict Grounding 唯一一致的差異是讓誠實揭露更結構化。這是這一次、這批來源的觀察，不能推廣，不要在其他文件裡把它包裝成「已驗證」的通則。
