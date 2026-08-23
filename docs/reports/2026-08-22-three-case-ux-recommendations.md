# 三案例 UX 研究後的專案修改建議

> 依據：Case 1（截止日期後規格）、Case 2（新概念 adoption）、Case 3（人文思想系譜）  
> 性質：產品／工程修改建議，不把三案的回答品質當成受控 A/B 證據

## 先說結論

三案證明目前 workflow 可以完成：

```text
Persona / Research Profile / Watchlist
→ 建立 Notebook + Pin seed
→ non-mutating Deep Research Preview
→ 人工選源
→ digest-bound Apply
→ Ask
→ Export
```

真正跨領域成立的價值是 **review boundary、Pinned protection、source provenance 與 portable export**。

三案也共同顯示：目前還不能把它稱為可信任的「開發第二大腦」。最大的缺口不是搜尋能力，而是：

1. NotebookLM 可能依官方的首次來源自動產物或 agentic Chat 功能建立 Studio artifact，但 skill 未揭露其觸發與結果。
2. Ask 缺 citation、conversation 與 action metadata。
3. `ready`／`exported` 不等於來源內容可用。
4. Watchlist 尚未產生結構化 Decision Delta。
5. 候選審查 UX 仍以大型 JSON 為主。

## 跨案例觀察

| 觀察 | Case 1 | Case 2 | Case 3 |
|---|---:|---:|---:|
| Preview 時間 | 356 秒 | 341 秒 | 331 秒 |
| 候選數 | 69 | 39 | 76 |
| 人工匯入 | 5 | 5 | 5 |
| Preview 保持 sources unchanged | 是 | 是 | 是 |
| Export fulltext | 6/6 | 6/6 | 6/6 |
| 需從 over-budget pool 選源 | 是 | 是 | 是 |
| Ask citation 可稽核 | 否 | 否 | 否 |
| Apply Plan 未揭露的 artifact creation | 無 | 無 | **有** |

這些不是控制實驗結果；它們是同一位 evaluator 代入三個角色的 field observation。

# P0：在下一輪 live test 前必修

## 1. 辨識並揭露 NotebookLM 官方的自動／代理產物

### 問題

Case 3 的 `apply` 只規劃五個來源 addition，但 delta-summary chat 期間出現一份 Studio Report。Artifact 不在 Apply Plan、digest 或 result 中。

後續官方文件研究修正了原始定性：Google 明說第一次加入來源時「有時」會自動建立起步 Report 等 artifacts；Pro／Ultra Chat 也能以 agentic actions 建立檔案，且官方警告功能仍屬實驗性、可能做出意外行為。因此不能直接把 Case 3 稱為 Google 越權或第三方 library bug，也無法只憑現有證據判定實際觸發來源。

本 skill 的真實缺口是：它宣稱 Studio generation 不在 v2 scope，卻沒有觀察、分類或揭露 provider 自己產生的 artifact delta。詳見 [`NotebookLM 官方行為研究`](2026-08-22-notebooklm-official-auto-summary-and-artifact-research.md)。

### 建議

- 每次 Ask／Apply 前後 snapshot artifacts、notes、sources 與 conversations。
- 提供 artifact policy：`text_only`、`observe`、`approve`、`allow`。若 API 支援，`text_only` 才使用 tool-disabled chat。
- 回報 exact artifact delta、ID、type、created_at、custom prompt／thinking steps（若可取得）與 cleanup choice。
- 將來源分類為 `first-source-auto`、`chat-action`、`user-requested` 或 `unknown`；證據不足時不可硬猜。
- 非破壞性新 Report 預設警告與記錄；未解釋的來源新增、刪除或既有內容修改才 fail closed。
- Source retirement 前若發生任何未解釋的破壞性 mutation，停止並重新核准。

### 驗收測試

1. 修改 Persona、加入第一份來源、一般 Ask 與 agentic Ask 分別保存 artifact before／after snapshot。
2. 若 backend 建立 artifact，CLI 輸出 ID／type／created_at 與 origin=`unknown`，而不是假裝 artifact set 不變。
3. `text_only` 模式若 provider 無法保證停用 tools，必須清楚報錯或降級為 `observe`，不可默默承諾。
4. 任何未解釋的破壞性 mutation 發生後不得執行 source retirement。

## 2. 把 Ask 升級成 fidelity interface

### 問題

三案的 `ask` 都只回 answer string。Case 1 的 self-audit 甚至否認 source fulltext 中明確存在的 `Version 2025-11-25` 與 CIMD。沒有 native references，就無法機器化判定哪一輪說法可追溯。

### 建議 API

每次 Ask 至少保存：

```json
{
  "answer": "...",
  "conversation_id": "...",
  "turn_id": "...",
  "mode": "fresh|follow_up",
  "references": [
    {
      "source_id": "...",
      "citation_number": 1,
      "quote": "...",
      "start": 123,
      "end": 456
    }
  ],
  "actions": [],
  "artifact_delta": [],
  "source_snapshot_ids": []
}
```

CLI 應提供：

```text
ask --fresh
ask --conversation-id ID
ask --require-citations
ask --no-tools
```

### 驗收測試

- Case 1 的 CIMD claim 可直接解析到 2025-11-25 source ID 與原文。
- Fresh Ask 不包含 Apply delta-summary turn。
- Follow-up Ask 明確回傳相同 conversation ID。
- 沒有 reference 的 factual claim 可被標記為 unsupported。

## 3. 加入 source hydration／content quality gate

### 問題

Case 3 的 Cambridge source 為 ready、exported，但 fulltext 主要是 `Our systems – temporary disruption` 頁面。現在的成功指標只確認「有內容」，不確認「是目標內容」。

### 建議

在 import ready 後、正式 registry commit 前執行 content inspection：

- HTTP／Notebook title 與候選 title 相似度；
- 內容長度與正文比例；
- login、cookie wall、temporary disruption、access denied、navigation shell 偵測；
- PDF／HTML／metadata-only 分類；
- author、publication date、DOI、document type 擷取；
- content hash 與同 notebook overlap；
- `usable_fulltext`、`metadata_only`、`blocked`、`suspect` 狀態。

Apply Plan 應顯示 hydration preview；blocked source 不得以普通 `active` commit。

### 驗收測試

- Cambridge temporary-disruption page 被標為 `blocked` 或 `metadata_only`。
- Export summary 不再把 metadata-only 算成 `exported_sources` 的完整全文成功。
- 使用者可以用相同 digest 替換失敗候選，不必重跑 Deep Research。

# P1：直接提升三類核心使用流程

## 4. 重新設計候選審查介面

### 問題

三案都必須從 over-budget pool 選源，但 `preview.md` 只呈現 proposed additions。審查 39–76 個候選必須手動讀 JSON 與複製 URL。

### 建議

- `preview.md` 顯示完整候選表，可依 cited、domain、date、type、fulltext、decision filter。
- 產生可編輯的 `candidate-review.csv` 或 `candidate-review.json`，每列包含 `selected` 與 `review_note`。
- CLI 增加：

```text
preview-review --preview ... --interactive
selection-build --preview ... --include 1,4,12
```

- 排名訊號分開顯示，不要讓 preferred domain 成為壓倒性第一排序。
- 同 repo、同 DOI、同文章不同 URL 應群組，而不是各占 budget。
- 顯示 source independence：primary、implementation、field report、review、repost、unknown。

## 5. 讓 Research Profile 支援歷史與事件時間範圍

### 問題

Case 3 只能用 `recency_days: 15340` 模擬 1984 至今。Case 1 需要 specification versions；Case 2 需要方法首次出現後的案例，而不是單純最近一年。

### 建議 schema

```json
{
  "time_scope": {
    "mode": "recent|since|range|all_time",
    "since": "1984-06-25",
    "from": null,
    "to": null,
    "recency_days": null,
    "event_anchor": "Foucault's death"
  }
}
```

`recency_days` 應改成可選。Query renderer 要依 mode 產生自然語言，而不是一律「Prefer evidence from the last N days」。

## 6. 將 Watchlist 變成真正的 Decision Delta

### 問題

目前 Watchlist 只被串入 Deep Research query。Apply 後沒有結構化回答：哪個 assumption 被支持、挑戰、維持未知，與上次相比改了什麼。

### 建議輸出

```json
{
  "watch_id": "watch-zero-to-one",
  "previous_status": "unknown",
  "current_status": "challenged",
  "evidence_for": ["source-id"],
  "evidence_against": ["source-id"],
  "changed": true,
  "confidence": "low|medium|high",
  "human_review": "required"
}
```

保留 immutable watch evaluations，讓 Skill 的 Evergreen 價值可被跨時間測試。

## 7. 增加顯式、審查式 project-context handoff

### 問題

Case 1 產生 migration checklist，Case 2 產生 spike plan，但 Skill 無法讀取本機穩定架構文件，也無法把研究交付成可核准的 project action。它因此停在研究與開發之間。

### 建議

不要恢復 v1 的 project-folder auto scan 或 Git hooks。改為明確命令：

```text
source-add-file --advisor-id ID --file ARCHITECTURE.md --state pinned
source-add-text --advisor-id ID --title "Decision context" --file decision.md
handoff-plan --advisor-id ID --template migration-checklist
```

- File source 先通過 stability、retrievability、irreplaceability、signal-to-noise gate。
- Handoff 只產生 proposed Markdown／JSON，不直接改 repo。
- 若未來 apply 到 repo，必須有獨立 digest、diff preview、user approval 與 tool receipt。

## 8. 讓 Preview 與 Apply 有可見進度

### 問題

三次 Preview 都約 5.5–6 分鐘，期間無進度；Apply 約 1.9–2.9 分鐘，也沒有 import／ready／summary 階段提示。

### 建議

- 每次 poll 顯示 task ID、elapsed、status、candidate count。
- Apply 顯示 `importing 2/5`、`waiting ready 4/5`、`generating summary`。
- 保留 JSONL event log，CLI text 與 automation 共用。
- Ctrl-C 後明確提示 resume command。

## 9. 修正 runtime onboarding 與版本契約

### 問題

User guide 要求 Python 3.11／3.12，`pyproject.toml` 卻宣告 `>=3.11`。本專案現有 `.venv` 是 Python 3.14，且沒有安裝 `notebooklm-py` 或 `notebooklm-evergreen` entry point；照 user guide 的第一個 smoke command立即失敗。

### 建議

- 若只支援 3.11／3.12，將 `requires-python` 改成 `>=3.11,<3.13`。
- CI 增加 clean install smoke，確認 console script 存在。
- `doctor` 檢查 interpreter、package version、entry point、auth home、state root。
- User guide 統一 `.venv` 與 isolated runtime 的推薦方式，不要同時留下兩條互相不完整的路徑。

# P2：提高研究品質與可維護性

## 10. 加入 claim／source graph 與 bibliographic metadata

Case 2 需要辨識 echo chamber；Case 3 需要 influence edge。建議建立通用 graph：

- source cites source；
- source reports project；
- scholar directly responds to scholar；
- claim supported／opposed by source；
- primary／secondary／repost 關係。

人文案例再加 DOI、author、work、year、edition、translator、pages 與 access status。

## 11. 將 delta summary 從自由聊天改成受約束產物

目前 Apply 用一般 chat 產生 summary，會承接 conversation、可能呼叫工具，也容易把案例技巧升格成普遍規則。

建議：

- 使用 fresh conversation，並依 artifact policy 選擇 tool-disabled 或可觀察的 agentic mode；
- JSON schema constrained output；
- 每個 claim 必須附 source ID；
- 無 reference 就歸入 inference／unknown；
- summary 失敗不應阻止已 ready additions 的安全 reconciliation，但不得開始 retirement。

## 12. 提供正式 live-test harness 與 cleanup command

本次手動建立三份 config、記錄 timing、查 artifact、export、再用底層 CLI cleanup。建議提供：

```text
field-trial start --manifest trial.json
field-trial snapshot
field-trial export
field-trial cleanup --approved-manifest trial.json
```

Manifest 應預先登錄 notebook 數、Deep Research quota、source budget、預期 mutation set 與 cleanup policy。

# 建議實作順序

## Milestone A：Trust boundary

1. Artifact policy／provider mutation snapshot／action receipt。
2. Ask references + conversation metadata + action receipt。
3. Source hydration quality gate。
4. 對應 regression tests。

## Milestone B：Research review UX

1. 完整候選 review table。
2. Source type／independence／duplicate grouping。
3. 歷史 time scope。
4. Preview／Apply progress events。

## Milestone C：Evergreen product value

1. Structured Watch Evaluation。
2. Decision Delta。
3. Reviewed project-context file source。
4. 第二時間點 A/B/C 測試：普通 LLM vs 手動 NotebookLM vs Evergreen Skill。

# 下一輪成功標準

在下一次三案例回歸中，我會要求：

- 三次 Apply 的 source mutation 與 Plan 一致；任何官方自動／agentic artifact 都有 delta、來源分類與使用者處置選項；
- 每個 Ask 都有 conversation ID 與 native references；
- Case 1 可從 migration claim 直接跳到版本原文；
- Case 2 能辨識 The Long Silence 不是 Gauntlet Loop primary evidence；
- Case 3 在 Apply 前標出 Cambridge source 為 metadata-only／blocked；
- 歷史研究不再出現 15,340 天 recency workaround；
- Watchlist 輸出可比較的 previous → current decision delta；
- 使用者不需手改大型 `preview.json`；
- disposable resources 可由 manifest 一次驗證與清理。

達成這些條件後，才適合測試「這個 Skill 是否比手動 NotebookLM 更能成為跨時間、可追溯的專案第二大腦」。
