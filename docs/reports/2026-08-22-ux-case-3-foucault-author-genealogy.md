# UX Case 3：研究 Foucault 死後「作者功能」的思想系譜

> 測試日期：2026-08-22  
> 角色：準備撰寫人文學 essay 的研究者  
> 狀態：完成 live field trial；Notebook 與研究期間產生的 Studio Report 已在 export 後一併刪除  
> 研究重點：我如何從文獻搜尋走到可驗證系譜，而不是評判 essay 成品

## 我為什麼使用這個 skill

我想研究 Michel Foucault 1984 年逝世後，哪些學者延續、修正、批判或跨領域重新部署「作者／作者功能」概念。

我不想得到一份只按年份排列的人名清單。我要區分：

- 直接回應 Foucault；
- 修正他的歷史斷代或理論；
- 平行發展；
- 後設綜述；
- 法律、女性主義、書籍史與數位作者性中的重新部署。

我也想測試一個新論點：作者功能是否從文本分類原理，逐漸轉成制度、法律與平台治理中的責任分配技術。

## 我實際走過的完整流程

### 1. 我先定義「不能犯的系譜錯誤」

我在 Persona 中要求：

- 保留 scholar、work、year 與概念關係；
- 不把年代先後自動當成思想影響；
- 不虛構書目或頁碼；
- 沒有直接證據時明說；
- 分開 direct response、parallel development、meta-review 與新論點。

我把「時間序列被誤寫成 influence edge」設成 Risk Watch，把我的 thesis 設成 Question Watch。

困難是 Research Profile 強制要求 `recency_days`。思想史需要 1984 至今的歷史範圍，不是「最近 N 天」。我只好填 15,340 天，最後 query 出現「Prefer evidence from the last 15340 days」，語意很機械，也不能表達 1984 是 Foucault 的逝世年份而非單純 freshness window。

### 2. 我建立 Notebook 並 Pin Foucault 原文節錄

`setup` 約 7 秒，Persona read-back 成功。加入 Foucault〈The Author Function〉英文節錄並 Pin 約 10 秒。

這份原文 seed 讓後續學者的「修正」有一個可比對基準。不過它只是節錄，不是完整版本；Skill 沒有 edition、translator、page range 或 completeness 欄位提醒我這點。

### 3. 我執行 Deep Research Preview

Preview 花了 331 秒，找到 76 個候選：

- 5 個 `propose_add`；
- 71 個 `over_budget`；
- Preview 未改變 source snapshot。

這是三案中候選最多、人工審查負擔最高的一案。preferred domains 讓 Cambridge 來源排到前面，但高排名中包含：

- 與研究問題關聯有限的書評；
- Foucault 與 Said 的殖民論述文章；
- ResearchGate、Scribd、Google Books、非正式網頁與重複二手材料；
- 只因網域權重而排前、但未被 research report 引用的來源。

我很快發現：學術來源的 domain prestige 不能代替內容相關性、全文可得性或 direct-citation evidence。

### 4. 我手動重組來源，而不是接受前五名

我從完整 pool 選了：

1. Cambridge Handbook 的作者理論章；
2. Roger Chartier 系譜修正的 SciELO 書評；
3. Peter Jaszi 的 copyright／collective creativity 論文；
4. Cheryl Walker 的 feminist author 論文頁；
5. Eric Rasmussen 的 hypertext authorship 論文。

這組來源讓我可以測試四條不同路線：文學理論綜述、書籍史、法律、女性主義與數位媒介。

但我只能根據 candidate title 與 URL 選擇。Apply 後 Export 才發現 Cambridge source fulltext 的開頭是 `Our systems – temporary disruption`，主要取得的是頁面殼層與 metadata。系統仍把它標成 ready、exported，沒有在 Apply 前警告「內容不可用」。

### 5. 我審查 digest 並 Apply

Apply Plan 有 1 個 protected seed、5 個 additions、0 retirements。Apply 花了 176 秒，是三案最久的一次。

六份來源都被標為 ready，且無刪除。此時發生本次研究最重要、但一開始被我過度定性的產品行為：

> Apply 的 delta-summary chat 期間出現了一份 Studio Report。

摘要開頭聲稱已生成報告。我原先以為這可能只是 action hallucination，因此在第二次 Ask 要求 receipt。回答給出 artifact ID。接著我繞過本 skill，使用底層 `notebooklm artifact list` 驗證：

- artifact ID：`9890c004-97f9-46bb-91d9-d075d7d7d1e0`；
- type：Report；
- status：completed；
- created at：2026-08-22T10:09:31Z。

所以 Report 不是虛構；但後續官方文件研究修正了我的解讀。Google 官方明說兩件事：第一次加入來源時「有時」會自動建立起步 Report 等 artifacts；Pro／Ultra 的 Chat 也能以 agentic actions 建立檔案與 artifacts。因此我不能再直接稱它為 NotebookLM「未經許可」或第三方 library 的異常。

目前只能確定：**這份 Report 沒有出現在本 skill 的 Apply Plan、digest 或 CLI result 中。** 現有證據不足以判定它是首次來源自動產物、Chat 自主工具動作或其他觸發。對本 skill 而言，真正需要改善的是偵測並揭露 artifact delta，讓使用者知道官方產品實際做了什麼。完整修正見 [`NotebookLM 官方行為研究`](2026-08-22-notebooklm-official-auto-summary-and-artifact-research.md)。

### 6. 我要求一張有證據強度的系譜表

第一次 Ask 花了 92 秒。我要求每列包含 scholar、work、year、relation type、concept edge、來源與證據強度，沒有直接證據就不能畫 influence edge。

回答成功產生一個可用來規劃 essay 的骨架，包含 Walker、Jaszi、Landow、Grusin、Bolter & Grusin、Poster、Rasmussen、Chartier 與後設綜述。它也提出一個有張力的 thesis：把作者功能的後續發展理解為媒介—法律—資本規訓與認同政治之間的張力。

但表格頻繁把二手綜述標成「極強」證據，也把「被後來文章討論」與「受 Foucault 直接影響」放得太近。對思想系譜而言，這個差異正是研究核心，不能只靠自然語言 confidence label。

### 7. 我執行可信度 audit

第二次 Ask 花了 82 秒。我要求核查 Studio receipt、書目、年份與 influence edges。

回答能區分：

- Walker、Jaszi、Chartier 等可直接或較直接連回 Foucault；
- Woodmansee、Rose、Hesse 比較適合列為平行收斂；
- Stougaard-Nielsen 的全文目前不足；
- 若要引用 Johns、Kaplan 等人，必須回圖書館找原文。

這種 audit 對論文流程有用，但 CLI 沒有保存 native citation objects。我仍無法從回答中的 `[29-31]` 建立穩定 bibliographic record，也無法知道某個 claim 究竟來自完整 PDF、metadata page 還是書評。

### 8. 我 Export 並清理

Export 花了 7 秒，六份來源都顯示 exported；bundle 約 252 KB。完整流程約 11 分 45 秒，不含人工閱讀。

Export 讓我看見 source hydration 品質差異，這是好事；但 `exported_sources: 6` 會讓人誤以為六份都是完整可引用全文。

保存 evidence 後，我刪除 disposable Notebook；研究期間產生的 Studio Report 也隨 Notebook 一併清除。

## 如果這是真實 essay，我會怎麼使用

### 文獻發現

1. Pin Foucault 原文與正確 edition。
2. 用研究問題分開 direct response、book history、law、feminism、digital authorship。
3. Preview 後先排除 metadata-only、登入頁、低品質轉載與疑似盜版。
4. 每條分支至少選一份 primary text 與一份可靠 reception-history source。

### 系譜建模

1. 每條 edge 記錄 `source A → scholar/work B → concept change`。
2. 只有直接引用或可靠二手文獻能標 influence。
3. 其餘標為 parallel、reception、analogy 或 unknown。
4. Notebook 先產生候選圖，我再回原文核對。

### Essay 寫作

1. 把 thesis 當待反駁假設放入 Watchlist。
2. 用反方問題找出三條最強 counterarguments。
3. 所有引文、頁碼、edition 回圖書館資料庫確認。
4. 將最後的 annotated bibliography 與 edge table 作為穩定來源，而不是上傳草稿與聊天紀錄。

## 對我有效的部分

- Persona 能把一般文獻摘要導向系譜關係與證據強度。
- Watchlist 很適合保存論文假設與因果風險。
- Preview／selection 讓我不必把 76 個候選全部匯入。
- 從 over-budget pool 自由選擇對跨領域研究非常重要。
- Export fulltext 能揭露抓取到的是 PDF、全文、metadata 還是錯誤頁。
- 反方與 audit 問答能把「名單」逐步收斂成可查證研究計畫。

## 阻礙我的部分

1. `recency_days` 不適合思想史與長時段系譜。
2. preferred domain 會把 prestigious but irrelevant source 排太高。
3. candidate 缺 publication year、author、document type、abstract、citation context 與 fulltext availability。
4. `ready`／`exported` 不代表內容完整或可引用。
5. 沒有 bibliography／DOI normalization 或 edition metadata。
6. Ask 不回傳 native citations，無法形成 claim-to-source edge。
7. conversation 延續會讓前一輪 framing 滲入後續 audit。
8. NotebookLM 官方可能自動或透過 agentic Chat 建立 Studio artifact，但 Apply 的 Plan、digest、result 都沒有揭露實際 artifact delta。
9. Artifact receipt 只能靠底層 CLI 另行驗證，本 skill 沒有 action ledger，也無法判定觸發來源。

## 我的結論

這個 skill 能把一個寬廣的人文問題轉成可管理的來源集合、Watchlist 與候選系譜。它適合作為研究發現與問題生成工具，不足以直接產出可交稿的學術系譜。

本案最重要的發現不是 essay 內容，而是兩個產品邊界：第一，學術研究需要 source hydration 與 bibliographic fidelity；第二，skill 必須辨識 NotebookLM 官方可能自動或透過 agentic Chat 產生的 Studio artifacts，提供可選的 text-only 政策、artifact delta 與 receipt。否則一個標榜 review-first 的 Apply，使用者仍看不到官方產品實際產生的全部內容。

## Evidence

```text
~/.local/state/notebooklm-skill/ux-three-cases-20260822/
├── configs/case-3-foucault-author-genealogy.json
├── runs/case-3-preview/
├── runs/case-3-apply/
├── evidence/case-3-artifacts.json
├── evidence/case-3-history.json
├── evidence/case-3-*.json
└── exports/case-3/
```
