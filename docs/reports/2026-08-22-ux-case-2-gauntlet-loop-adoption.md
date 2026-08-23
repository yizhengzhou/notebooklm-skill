# UX Case 2：第一次遇到 Gauntlet Loop 的 Three.js 團隊

> 測試日期：2026-08-22  
> 角色：三人遊戲開發團隊的 Tech Lead  
> 狀態：完成 live field trial；Notebook 已在 export 後刪除  
> 研究重點：我如何在開發途中理解新概念、辨識使用邊界並規劃 adoption spike

## 我為什麼使用這個 skill

我的團隊已有 playable Three.js baseline，但沒有人熟悉 Gauntlet Loop。我聽到的說法是：讓 Builder 與 Critic 不斷比較，AI 就能把遊戲做得像 AAA 作品。

我真正需要回答的不是「Gauntlet Loop 是什麼」，而是：

- 它需要哪些工程前置條件？
- 它適合 zero-to-one，還是只適合 scoped polish？
- 公開案例有沒有 code、run log、成本與失敗紀錄？
- 視覺品質提升時，如何避免 FPS、功能或操控退化？
- 三人團隊是否值得投入兩週？

我把「它適合從零做完整遊戲」設為 Assumption Watch，把「視覺勝出可能破壞可玩性」設為 Risk Watch。

## 我實際走過的完整流程

### 1. 我先定義使用者情境，而不是直接問名詞

我在 Persona 中寫明：我是三人團隊 Tech Lead、已有 Three.js prototype、要做兩週 spike。回答必須分開原作者主張、獨立案例、推論、反證與未知，且不能聲稱已改 code 或跑測試。

這一步對後面的回答影響很大。Notebook 不只給定義，而會嘗試把研究落到 hard gates、evidence artifacts 與 go/no-go。

但 Persona、Research Profile、Watchlist 之間仍有大量手動重複。我也無法在設定階段看到最後組合出的 Deep Research query，只能到 Preview 後才看到。

### 2. 我建立 Notebook 並 Pin canonical repo

`setup` 約 7 秒，Persona read-back 成功。加入 `robonuggets/gauntlet-loop` 並 Pin 約 11 秒。

這個 seed 讓我可以分辨「canonical 方法說了什麼」與「社群案例後來加了什麼」，而不是讓搜尋結果自行定義概念。

### 3. 我執行 Preview

Preview 花了 341 秒，共找到 39 個候選：

- 5 個 `propose_add`；
- 1 個 `already_present`；
- 33 個 `over_budget`；
- source snapshot 保持不變。

GitHub preferred domain 把 Claude-of-Duty、ARCHITECTURE.md 與 The Long Silence 排到前面。這看似合理，但也暴露 ranking 問題：GitHub repo 只能證明 code 或文件存在，不等於它證明 Gauntlet Loop 的因果效果。

系統也把 The Long Silence 列為高排名案例，後續反方問答卻承認它沒有明確使用 Builder-Critic Gauntlet Loop。也就是說，搜尋相關性很容易被「同模型、同類型遊戲、同時期」誤當成方法採用證據。

### 4. 我人工建立來源組合

我選入五份來源：

1. Claude-of-Duty repo；
2. Claude-of-Duty `ARCHITECTURE.md`；
3. The Long Silence repo；
4. Ruben Marcus 的實踐文章；
5. Crazystack 的成本與失敗評論。

第五份來自 `over_budget` pool。我刻意補一份反面來源，因為系統前五名偏向成功展示與同源轉述。

這一步讓我感受到 skill 的 review-first 價值，也讓我看到它沒有 source independence、evidence type 或「直接採用此方法」的標記。我必須自己判斷哪些是 primary、implementation artifact、field report、評論或 echo。

### 5. 我審查 Plan 並 Apply

Apply Plan 列出 1 個 protected seed、5 個 additions、0 retirement，並綁定 digest。Apply 花了 121 秒，最後六份來源均 ready，無刪除。

Delta summary 很長，快速把來源內容轉成工程建議，但它把多個 repo 的工程技巧歸納為「生產級 Gauntlet Loop」，有明顯過度整合風險。

### 6. 我要求一份 Day 1–10 adoption spike

第一次 Ask 花了 87 秒。回答提供：

- 每天的人類工作；
- NotebookLM 使用點；
- Builder／Critic 分工；
- hard gates；
- evidence artifacts；
- stop conditions；
- Day 10 go/no-go。

這種結構對規劃 workshop 很有用，也有把未知數標成 `[待校準]`。但它同時提出大量來源未必支持的固定做法，例如 25 項 rubric、特定檔名、特定字元長度、900 秒 timeout、固定工具與架構模式。

我會把這份回答當成「spike backlog 草案」，不會把它當成最佳實務清單。

### 7. 我改用反方 reviewer 提問

第二次 Ask 花了 56 秒。我要求逐一說明每個來源能證明與不能證明什麼，並檢查 The Long Silence 是否真的使用 Gauntlet Loop。

這輪是整個案例最有用的時刻。回答指出：

- canonical repo 主要證明 prompt pattern，不證明 production outcome；
- Claude-of-Duty 有架構與結果，但缺少完整 orchestrator；
- The Long Silence 不足以證明 Gauntlet Loop；
- 多個來源其實共享同一概念源頭；
- 真正缺的是 orchestration logs、成本帳、跨模型測試與人類介入紀錄。

即使細節仍需引用稽核，這種「先產生方案，再要求反方拆證據」比單次問答更接近我在開發決策中的真實工作方式。

### 8. 我 Export 並清理

Export 花了 7 秒，六份來源全文都可匯出。完整自動化流程約 10 分 30 秒，不含人工審查。

我保存 evidence 後刪除了 disposable Notebook。

## 如果這是真實專案，我會如何嵌入開發流程

### Discovery 階段

1. Pin canonical method。
2. 用 Watchlist 寫下「zero-to-one 可行」與「視覺優化不傷功能」兩個假設。
3. Preview 後強制選入至少一份 failure／cost source。
4. 先問「各來源能證明什麼」，再問「最佳使用方式」。

### Spike 階段

1. 人類先決定一個小範圍，例如材質、HUD 或粒子效果。
2. 把 deterministic capture、功能測試、FPS／frame-time gate 放在 visual critic 之前。
3. 將所有非來源明定的 threshold 標為團隊待校準值。
4. 保留每輪 prompt、diff、capture、metrics、winner、token 與人工介入。
5. 到 budget、停滯輪次或 hard-gate failure 時停止。

### Decision 階段

1. 只以 spike 的第一手 evidence 決定 go/no-go。
2. 將 field result 回寫成穩定研究來源。
3. 下次 Refresh 檢查是否有新案例挑戰原本判斷。

目前 skill 能協助 Discovery，但沒有把專案 context、spike artifacts 或 decision delta 接回 Notebook 的完整 UX。

## 對我有效的部分

- canonical seed 與研究來源角色清楚分開。
- Watchlist 迫使我預先寫下可被反駁的採用假設。
- 人工 selection 讓我能補進負面案例。
- 問答能從名詞理解推進到可驗收的 spike 結構。
- 反方 reviewer prompt 能揭露來源同源性與歸因錯誤。
- Export 讓後續工程師可離線檢查全文。

## 阻礙我的部分

1. 搜尋相關不等於方法採用證據，系統沒有 relation／evidence-type 標記。
2. preferred domain 排名會讓 GitHub presence 壓過獨立、負面或成本證據。
3. 同一 repo 首頁與 `ARCHITECTURE.md` 會占兩個 source budget，但系統不提示內容重疊。
4. 來源之間是否互相轉述沒有 provenance graph。
5. 回答容易把案例特有技巧升格為普遍「最佳實務」。
6. 所有 Ask 延續 Apply delta summary 的 conversation，沒有獨立反方實驗條件。
7. Skill 無法加入本機穩定架構文件或 spike report；目前只有 URL seed 的 user-facing CLI。
8. Watchlist 只進入 research query，沒有輸出結構化的「supported／challenged／unknown」變化。

## 我的結論

我確實能用這個 skill 從「第一次聽過 Gauntlet Loop」走到「知道如何設計一個受控 spike」。對我最有價值的是來源審查、反證搜尋與採用邊界，不是 Notebook 產生的十天計畫本身。

我不認為本次證明了 Gauntlet Loop 的最佳實務，也不認為它證明 skill 優於手動 NotebookLM。它證明的是：目前 workflow 可以支援新概念 discovery，但還需要 source relationship、project-context handoff、fresh conversation 與 Watchlist delta，才能真正成為開發團隊的第二大腦。

## Evidence

```text
~/.local/state/notebooklm-skill/ux-three-cases-20260822/
├── configs/case-2-gauntlet-loop.json
├── runs/case-2-preview/
├── runs/case-2-apply/
├── evidence/case-2-*.json
└── exports/case-2/
```
