# 測試辯證流程總覽：從「無效實驗」到「程式碼修正」

> 日期：2026-08-23
> 性質：跨報告綜合整理，回顧 2026-08-22～2026-08-23 期間為了確認本 Skill 是否真的有產品價值所走過的完整測試流程
> 涵蓋報告：
> - [`2026-08-22-gauntlet-loop-field-trial.md`](2026-08-22-gauntlet-loop-field-trial.md)
> - [`2026-08-22-ux-case-1-post-cutoff-knowledge.md`](2026-08-22-ux-case-1-post-cutoff-knowledge.md)
> - [`2026-08-22-ux-case-2-gauntlet-loop-adoption.md`](2026-08-22-ux-case-2-gauntlet-loop-adoption.md)
> - [`2026-08-22-ux-case-3-foucault-author-genealogy.md`](2026-08-22-ux-case-3-foucault-author-genealogy.md)
> - [`2026-08-22-notebooklm-official-auto-summary-and-artifact-research.md`](2026-08-22-notebooklm-official-auto-summary-and-artifact-research.md)
> - [`2026-08-22-three-case-ux-recommendations.md`](2026-08-22-three-case-ux-recommendations.md)
> - [`2026-08-22-three-case-ux-recommendations-plain-language.md`](2026-08-22-three-case-ux-recommendations-plain-language.md)
> - [`2026-08-23-strict-grounding-reproduction-experiment.md`](2026-08-23-strict-grounding-reproduction-experiment.md)
> - [`2026-08-23-evaluation-synthesis-and-architecture-corrections.md`](2026-08-23-evaluation-synthesis-and-architecture-corrections.md)

---

## 為什麼要寫這份文件

這兩天的測試不是一次性的「跑一跑、寫報告」，而是一個明確的「正—反—合」辯證過程：每一份報告都在挑戰、甚至推翻前一份報告的結論。這份文件把散落在九份報告裡的流程串成一條時間線，方便未來回來查「我們是怎麼走到現在這個判斷的」，也避免之後有人只看最後一份報告，誤以為結論是一步到位得出的。

---

## 時間線

### 第一階段（正）：Gauntlet Loop 智囊團實驗 → 自我推翻
**`gauntlet-loop-field-trial.md`（08-22 15:25）**

最早的測試想證明「Advisor Notebook 能當開發智囊團」。報告開頭就自行標注「**狀態：INVALID**」——因為 Control 組與 Treatment 組同時改變了來源數量、問題順序，且沒有預先定義假設與評分標準，實驗設計本身不成立。

但這次失敗帶出兩個關鍵發現，成為後續所有測試的出發點：

1. Notebook 會**虛構動作**——宣稱已建立 Studio report、已寫入專案檔案，但實際上沒有執行。
2. 沒辦法證明「價值是來自 Skill，還是來自 NotebookLM 本身」，因為只跑了一個時間點，Skill 主打的 Evergreen（跨時間追蹤假設變化）完全沒被測到。

這份報告自己提出了「下一次必須怎麼測才算數」的設計：需要三組對照（A：一般 LLM／B：手動 NotebookLM／C：我們的 Evergreen Skill），且必須跨兩個時間點比較。

### 第二階段（反）：三個真實 UX 案例 → 系統性挑出問題
**Case 1**（MCP 授權規格追新）、**Case 2**（Gauntlet Loop 技術評估）、**Case 3**（Foucault 作者功能思想系譜）—— 08-22 18:23–19:53

這次改用嚴謹的「角色代入＋完整流程走一遍」方法：Persona → Deep Research Preview → 人工選源 → digest-bound Apply → Ask → Export。三案共同暴露的核心信任問題：

- **Ask 沒有可查核的引用**：Case 1 最嚴重——模型在 self-audit 時，反過來否認來源中明明存在的文字（2025-11-25 版本號、CIMD），使用者只能靠事後 export 全文才抓到矛盾。
- **來源品質假陽性**：Case 3 的 Cambridge 來源被系統標記為 `ready`／`exported`，實際抓到的只是一頁 `Our systems – temporary disruption` 錯誤頁。
- **NotebookLM 官方自己會建立 Studio artifact，但 Skill 完全沒揭露**：Case 3 的 Apply Plan 只規劃了五個來源新增，過程中卻多出一份 Studio Report，一開始被誤判為「未經授權的越權行為」。
- **候選來源審查全靠讀大型 JSON**（39–76 個候選只能手動看 preview.json）。
- **`recency_days` 不適合歷史／思想史研究**：Case 3 為了模擬 1984 年至今，只能填 15,340 天，語意很機械。

`three-case-ux-recommendations.md`（19:53）把這些整理成 P0／P1／P2 的具體工程修改清單與驗收測試，並排出 Milestone A（Trust boundary）／B（Research review UX）／C（Evergreen product value）三階段實作順序。同日也產出了給非工程讀者看的 [plain-language 版本](2026-08-22-three-case-ux-recommendations-plain-language.md)。

### 第三階段（反的自我修正）：官方行為研究，撤回錯誤指控
**`notebooklm-official-auto-summary-and-artifact-research.md`（08-22 19:52）**

去查證 Google 官方文件後發現：Case 3 那份「不明 Studio Report」其實是官方文件明說的已知行為——首次加入來源時「有時」會自動產生起步報告；Pro／Ultra 版的 Chat 本身就具備 agentic 建檔能力。

於是原本「NotebookLM 越權」的定性被撤回，改成「需要 Artifact Snapshot & Policy 機制去觀察、分類、揭露」。這是整個流程裡明確的一次自我修正——先懷疑平台有問題，查證後發現是自己誤讀官方行為，因而收回指控、修正方向，而不是硬凹原本的結論。

### 第四階段（合）：針對性重現實驗，證明修法有效
**`strict-grounding-reproduction-experiment.md`（08-23 03:04）**

只改一個變數——在 Persona 裡加上「Strict Grounding」約束（100% 只依來源作答、未提及必須答未知、禁止否認來源中已存在的字面文字、禁止聲稱已執行程式碼／檔案操作）——完全沿用 Case 1 一模一樣的六份來源與兩個問題重跑一次。結果：

- 因果跳躍（無狀態化 → CIMD）消失，模型主動指出「來源並未明說此因果關係」。
- 自我審查時的反向否認幻覺**徹底消除**，還能精準指出 CIMD 的定義出處（PR #2858）。

這證明了「加強 Persona 約束」這個乾預確實能修正上一階段找到的問題，而不只是理論猜測。

### 第五階段（合的落地）：根因追查 + 實際程式碼修正
**`evaluation-synthesis-and-architecture-corrections.md`（08-23 03:18）**

流程收尾階段有全程最關鍵的一次認知修正：先前一直以為「Ask 沒有原生 citation 物件」是 NotebookLM 平台本身的能力限制——結果深入追查後發現，**後端本來就會回傳完整的引用座標（`source_id`／`cited_text`／`start_char`／`end_char`），是 Skill 自己的 `gemini_backend.py` 把它丟掉了**。這不是平台限制，是自家的 bug。

於是這份報告帶出了實際的程式碼修正（目前仍是 working tree 中未 commit 的改動）：

- `backend.py` 新增 `CitationReference`／`AskResponse` 結構化資料模型
- `gemini_backend.py` 改成完整解析 `AskResult.references`，不再截斷成純字串
- `cli.py`／`evergreen.py` 在 `ask` 指令輸出後自動渲染「📚 引用出處與原文對照表」
- 測試同步更新（`test_backend_contract.py`、`fake_backend.py`、`test_evergreen.py`），新增 `test_format_answer_with_citations`
- 把「三層式 Strict Grounding Persona 範本」（角色定位 → 可核查性防線 → 格式要求）寫入專案最佳實務，供未來建立 Advisor 時直接套用

---

## 整條線串起來

```
無效實驗
（發現「無法證明產品價值」＋「模型會虛構動作」）
    ↓
三案例嚴謹測試
（系統性列出信任缺口：citation 缺失、source hydration 假陽性、artifact 透明度不足）
    ↓
官方文件查證
（修正一個過度指控，避免辯證流程滑向偏見確認）
    ↓
單變數重現實驗
（證明 Strict Grounding persona 約束真的能消除因果跳躍與自我審查幻覺）
    ↓
根因追查
（發現「無 citation」其實是自家 gemini_backend.py 的 bug，不是平台限制）
    ↓
實際程式碼修正
（backend.py／gemini_backend.py／cli.py／evergreen.py 現有改動）
```

這條線最值得留意的地方，不是「每一步都做對了」，而是它保留了**每一次自我推翻的過程**：無效實驗承認自己無效、越權指控被官方文件打臉後主動收回、平台限制的假設被追查後發現是自己的 bug。這種可追溯的自我修正記錄，本身就是 P0 清單裡要求 Skill 對使用者做到的事（claim 要能追回證據、不能宣稱做了沒做的事）——這次是專案自己先對自己做到了。

---

## 目前尚未完成、下一輪必須驗證的事

對照 `three-case-ux-recommendations.md` 的 Milestone A／B／C 與 `gauntlet-loop-field-trial.md` 提出的 A/B/C 對照實驗設計，目前完成度：

| 項目 | 狀態 |
|---|---|
| Ask citation 遺失（Milestone A-2） | **已修正**（程式碼變更，尚未 commit） |
| Strict Grounding persona 範本（因果跳躍／自我否認幻覺） | **已驗證有效**，已寫入最佳實務 |
| Source hydration／content quality gate（Milestone A-3，Cambridge 假陽性） | **未動** |
| Artifact policy／provider mutation snapshot（Milestone A-1，Studio artifact 揭露） | **未動**，只完成了「撤回誤判」，尚未做技術偵測機制 |
| 候選審查 UX（Milestone B，39–76 個候選只能讀 JSON） | **未動** |
| 歷史／事件時間範圍的 Research Profile（`recency_days` 15,340 天問題） | **未動** |
| Watchlist → 結構化 Decision Delta（Milestone C-1） | **未動** |
| 跨時間點 A/B/C 對照實驗（證明 Skill 價值優於手動 NotebookLM） | **未動**，是目前最大的缺口 |

---

## 建議下一步：讓 Skill 真正證明自己有價值需要走的流程

到目前為止，所有測試都還停留在「工程能力是否可信」這一層（citation 對不對、來源內容乾不乾淨、模型會不會說謊）。這一層很重要，但**還沒有回答最初那個問題**：這個 Skill 比起使用者自己手動開一個 NotebookLM，到底多帶來了什麼？以下是建議的後續流程，按優先順序排列。

### 1. 先把現有修正落地、閉環，再往下走
`backend.py`／`gemini_backend.py`／`cli.py`／`evergreen.py` 的 citation 修正目前還是未 commit 的 working tree 變更。在做任何新實驗之前，應該：
- 把這批改動 commit、跑過完整測試（目前是 67 個單元測試全過），並在真實 Notebook 上手動跑一次 `ask`，確認「📚 引用出處與原文對照表」在實際輸出中真的可用、可點對點核對。
- 沒有做這一步，下一輪實驗量到的「citation 是否可信」還是舊行為，會污染新一輪的結果。

### 2. 補齊剩下的 Trust Boundary（Milestone A 剩餘兩項）
在跨時間對照實驗開始前，**source hydration gate** 與 **artifact policy／snapshot** 必須先做，否則實驗過程中一旦又出現「來源其實是錯誤頁」或「NotebookLM 自己生成了東西」，會像 Case 3 一樣把整個實驗的因果解讀搞混，事後才發現要重新歸因。這兩項不是錦上添花，是讓下一輪實驗結果乾淨的前提。

### 3. 執行 gauntlet-loop 報告裡設計的跨時間 A/B/C 對照實驗
這是能不能證明「產品價值」的關鍵測試，目前完全還沒做：

- **A 組**：一般 LLM／搜尋，不給持久 Notebook。
- **B 組**：人工手動建立 NotebookLM，相同 Persona、相同來源、相同問題。
- **C 組**：本 Skill 的 Evergreen 流程，額外加上 Research Profile、Assumption／Decision Watchlist、source provenance、change history。

必須跨兩個時間點：第一輪建立一個具體、可證偽的判斷（例如「Gauntlet Loop 適合 scoped visual polish，不適合 zero-to-one 生成」），第二輪加入一份新的、可能支持或推翻這個判斷的證據，然後比較三組在下列面向的表現：
1. 誰最快指出核心假設被新證據挑戰？
2. 誰能明確說出「跟上次比，改變了什麼」？
3. 誰能把改變精準連回來源？
4. 誰產生的 unsupported claim 最少？
5. 誰最不會虛構自己做過的動作？
6. 一週後使用者回來，誰最容易恢復決策脈絡？
7. 維護來源需要多少人工時間？

**只有 C 組在這些面向明顯勝過 B 組，才能真正證明 Skill 有超越「手動用 NotebookLM」的產品價值。** 這也是三案例報告與無效實驗報告唯一交集的共同結論。

### 4. 把 Watchlist 從「串進 query」升級成真正的 Decision Delta
目前 Watchlist 只是被塞進 Deep Research 的查詢字串，Apply 後沒有任何結構化輸出。要支撐第 3 點的對照實驗，Decision Delta（`previous_status → current_status`，附 `evidence_for`／`evidence_against`）至少要有雛形，否則 C 組在「誰能說出改變了什麼」這一項會沒有東西可比。

### 5. 候選審查 UX 與時間範圍 schema（Milestone B）可以往後放
`preview.md` 只顯示前五名、`recency_days` 不適合歷史研究，這兩項會影響使用體驗，但不影響「Skill 是否有產品價值」這個核心問題的驗證，可以在核心價值證明之後再排。

---

### 一句話總結

過去兩天證明的是「這個 Skill 技術上可信任」；還沒有證明的是「這個 Skill 比使用者自己手動開一個 NotebookLM 更值得用」。下一輪測試如果不做跨時間點的 A/B/C 對照，只是繼續加功能、加 CLI 指令，並不會讓這個問題更接近答案。
