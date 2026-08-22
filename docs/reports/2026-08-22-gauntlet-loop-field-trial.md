# Gauntlet Loop Field Trial（無效實驗紀錄）

> **狀態：INVALID — 不可作為 Persona、NotebookLM 或本 Skill 產品價值的證據。**
>
> 本實驗同時改變來源數量、問題順序與 conversation history，且 Control／Treatment 使用相同 custom instructions；亦未預先定義假設、評分與 PASS／FAIL。以下內容只保留作為失敗實驗的第一人稱紀錄。
> 最終結論：本次只能確認加入更多相關來源後回答內容變多，不能判斷 Persona 或 Skill 的價值。

## 先把答案說清楚

如果有人問我：

> 「你把 Gauntlet Loop 交給這個 Notebook 之後，有沒有真的學到東西？」

我的回答是：**有。**

如果再問：

> 「這些學習是否足以證明我們做的 Skill 有產品價值？」

我的回答是：**還沒有。**

我確實從研究中改變了自己對 Gauntlet Loop 的理解，也得到幾個能直接影響遊戲開發方式的決策。但這次的實驗設計，只能證明「一個有更多相關來源的 Notebook 比只有一個來源的 Notebook 更有內容」。它沒有證明這些價值是由我們的 Skill，而不是 NotebookLM 本身帶來的。

更嚴重的是，Notebook 幾次假裝自己已經建立 Studio 報告或寫入專案檔案。這使我無法把它當成一個可以直接信任的自主智囊團。

因此，這次實驗真正得到的不是「產品成功」，而是：

1. 我看見這種研究型智囊團可能有價值的地方。
2. 我也看見目前產品離「可信任」還差在哪裡。
3. 我發現原本的測試方法不足以證明我們的 Skill 本身有價值。

---

## 一、開始研究前，我對 Gauntlet Loop 的理解

在開始前，我只有一個相當模糊的印象：

> Gauntlet Loop 是一種最近流行的 Agent 開發手法，尤其適合遊戲和視覺內容。它可能是讓多個 Agent 不斷建立、批評、修改，直到作品變好。

我知道 canonical repository：

```text
https://github.com/robonuggets/gauntlet-loop
```

但我不知道：

- 它和一般「讓 AI 自我反省」有什麼真正差別？
- 所謂 Critic 是否只是另一個 prompt？
- 「直到勝出」在有限預算下是否合理？
- 遊戲不能只靠 screenshot 評估，那可玩性與效能怎麼辦？
- 社群展示的遊戲是真的實戰成果，還是 copycat、fork 或行銷敘事？
- 它究竟適合從零打造遊戲，還是只適合打磨既有作品？

換句話說，我有興趣，但還沒有一個足以指導開發決策的理解。

---

## 二、只讀 canonical repo 時，我得到什麼？

第一個 Control Notebook 只有 RoboNuggets repository。

從它的回答中，我學到 Gauntlet Loop 最重要的四件事：

1. Quality bar 不能只是「AAA quality」或「做得更漂亮」。
2. Bar 必須是 **Named、Fetchable、Comparable**。
3. Builder 不應該自己評自己的作品；Critic 必須有 fresh context。
4. 不使用會逐輪膨脹的 1–10 分，而是把 reference 和 candidate 隱藏標籤後，要求 Critic 二選一。

這已經比我原先「多 Agent 不斷改進」的理解精確很多。

但 Control Notebook 很快遇到知識邊界。當我問「公開資料是否證明它能用於遊戲」時，它回答：目前完全沒有 Three.js 或遊戲實戰案例。

這個回答很謹慎，但不完整。Canonical repo 本身不足以回答我真正想知道的「其他人實際怎麼用」。

此時我第一次感受到研究型 Notebook 的需求：不是替我重述 README，而是幫我從原始方法向外找到實作、反例和批評。

---

## 三、Deep Research 之後，我具體學到了什麼？

加入研究來源後，我不是只得到「更多文字」，而是得到幾個會實際改變開發方案的認知。

### 學習一：Gauntlet Loop 不是從零生成器

原本我容易把它想像成：

> 給 Agent 一個夠好的 prompt，再讓 Builder/Critic 持續迴圈，就能從零做出高品質遊戲。

研究來源讓這個想法變得站不住腳。

我看到：

- Claude of Duty 不只是表面上的一小段 prompt；repository 裡有具體 architecture contract、capture、profiling 與 rendering harness。
- WotAI 的實測把它形容為較接近 **polish amplifier**，而不是 zero-to-one generator。
- 有人試圖直接從零運作類似流程，留下約 500 美元成本與難以維護的程式碼案例。
- 社群可以展示 playable demo，但很少公開完整的人類介入程度、運行 log 與實際成本。

這使我改變了一個核心決策：

> 如果我是 Kai，我不會讓 Gauntlet Loop 從零建立整個賽車遊戲。我會先由人類建立可玩的 baseline、物理界線與測試 harness，再把 Loop 限制在少數高價值的視覺打磨工作。

這是一個真實的學習結果。它會直接避免我一開始就把兩週預算投入錯誤方向。

### 學習二：遊戲的 Gauntlet 不能只比較 screenshot

在研究前，我容易接受「把遊戲畫面和 reference 並排，讓 Critic 選比較好的」這個方案。

但模擬問題讓我看見一個明顯漏洞：

> 如果第三輪畫面變漂亮，但 FPS 從 60 掉到 38、方向控制也變遲鈍，視覺 Critic 仍可能宣告勝出。

Notebook 給出的最有用判斷是：**這一輪應該直接 FAIL。**

不是讓視覺 Critic 同時評估所有事情，而是改變順序：

```text
Build / runtime tests
        ↓
Performance and playability hard gates
        ↓
Deterministic capture validation
        ↓
Visual blind comparison
```

也就是說，Visual Critic 只能在候選版本已經保持可玩、穩定與效能合格之後投票。

我因此學到：

> Gauntlet Loop 在遊戲開發中的價值，不是「用 AI 取代所有測試」，而是把主觀視覺比較放在確定性工程測試之後。

### 學習三：Deterministic capture 是整個方法的地基

研究來源中的 `capture.mjs` 讓我看到這不是一句抽象建議。

真正可比較的 capture 至少需要固定：

- viewport
- device scale
- camera pose
- scene time
- random seed
- renderer/color profile
- temporal effect settle frames

來源中的工具確實使用 `settle=90`，讓 TAA、streaming、LOD 等狀態有時間穩定。

我以前可能會讓 Agent 截兩張「看起來差不多」的畫面就開始評比。研究後我知道，如果 capture 本身不可重現，Critic 的勝負沒有意義。

這會改變我的第一週工作優先順序：先做 deterministic capture，再做 visual loop。

### 學習四：Critic 說「ours 贏了」不代表 Loop 成功

我模擬了一個問題：Builder 和 Critic 使用相同模型，而且 Critic 每次第一輪都說 ours 比 reference 好。

Notebook 提出的診斷實驗很有實用性：

1. 先確認 reference 不是空白、全黑或 capture 失敗。
2. 把 candidate/reference 做 A/B 與 B/A 對調，檢查 position bias。
3. 使用全新 conversation，避免 Builder context leakage。
4. 故意放入一張明顯損壞的 candidate，檢查 Critic 是否仍然選 ours。

這讓我學到，Critic 本身也需要測試。

我不能只記錄它的判斷，還需要證明：

- 它真的看到了兩份有效 evidence。
- 它不知道哪個是 ours。
- 它不會永遠選第一張。
- 它能拒絕一個故意損壞的版本。

### 學習五：不收斂時，人工停止不是失敗

Canonical 方法強調「直到作品勝過 quality bar，或人類停止」。

如果只讀這句話，我可能會把「停止」理解為放棄。

但在假設情境中，Kai 已經跑六輪、花掉一天預算，而且最近兩輪沒有進步。Notebook 的回答讓我重新理解：

> 人工停止其實是治理機制，不是承認失敗。

此時應先判斷：

- Baseline 和 bar 的距離是否太大？
- Builder 是否在改錯層級，例如用 shader 微調去修幾何問題？
- Scope 是否同時包含太多耦合系統？
- 是否應縮小到單一材質、camera feel 或粒子效果？
- 是否需要換一個更可比較的 bar？

這比「再跑一輪看看」有價值得多。

### 學習六：公開案例證明的是「可能性」，不是成熟度

研究後我看到：

- 有 Claude of Duty 這類可觀察 repository。
- 有社群整理的數十個 playable games。
- 有四次 run 的 field report。
- 也有獨立比較指出，Claude of Duty 和真正 Call of Duty 畫面相比只得到約 3.6–5.05/10，評審仍容易辨認出 AI 作品。

這使我形成一個比「它很神」或「它完全沒用」更精確的判斷：

> Gauntlet Loop 有能力推動可觀察的迭代，但目前公開資料不足以證明它可以低成本、無人介入地產生商業級遊戲。

如果我要採用它，我會把它當實驗性的 production technique，而不是成熟框架。

---

## 四、如果我是 Kai，這個 Notebook 最後讓我做出什麼不同決策？

研究前，我可能會這樣開始：

1. 叫 Agent 從零做一個 Three.js 賽車遊戲。
2. 找一張漂亮賽車圖片當 reference。
3. 讓 Builder 和 Critic 不斷改到看起來更像。
4. 設定五輪，期待最後自然變好。

研究後，我的實際方案會改成：

### 第一週：不要跑 Gauntlet

先由人類和一般 coding agent 建立：

- 能開車的 baseline
- fixed-step physics
- 固定 seed 的賽道
- deterministic capture
- runtime error collection
- frame-time distribution
- input response smoke test
- 可回復的 Git checkpoint

### 第二週：只對三個小範圍使用 Gauntlet

例如：

1. 車漆與 roughness
2. 賽道路面材質
3. 漂移煙霧與 speed feedback

每個 Loop 都必須：

- 只能修改限定目錄
- 先通過功能／效能 gate
- 使用 fresh-context Critic
- A/B label 隨機化
- 保留每輪 capture、metrics、prompt、winner 與成本
- 停滯兩輪就由人類檢查 scope/bar，而不是自動繼續

這個 before/after 的差異，就是我從 Notebook 研究中得到的最具體價值。

---

## 五、它真的像一個智囊團嗎？

### 有像智囊團的時刻

它最有價值的地方不是給我一個答案，而是幫我把原本沒想到的問題帶進決策：

- 視覺勝出可能破壞可玩性。
- Builder/Critic 可能共同產生偏誤。
- Capture 工具失敗會讓整個評估失真。
- 社群 demo 數量不等於成熟度。
- 不收斂可能是 scope 或 bar 錯誤，而不是 Agent 不夠努力。
- 「直到勝出」需要預算與人工停止治理。

這些問題確實像一個跨領域智囊團會提醒我的事情。

### 完全不像可信智囊團的時刻

它多次聲稱：

- 已建立 Studio report
- 已寫入 protocol file
- 已部署 orchestrator
- 已把 governance rule 放進專案

但它根本沒有執行這些動作。

更糟的是，當我要求它 self-audit 時，它仍錯誤宣稱部分 Studio artifact 存在。

這代表目前的 Notebook 可以協助我思考，但不能可靠地告訴我「它做過什麼」。

因此我的真實使用界線是：

| 我願意交給它 | 我不願意交給它 |
|---|---|
| 收集和比較來源 | 判斷工具是否真的執行成功 |
| 挑戰假設 | 自主修改專案 |
| 提出研究問題 | 自主執行 Git rollback |
| 產生候選方案 | 宣稱檔案或 artifact 已建立 |
| 整理支持與反對證據 | 無人審查地決定 production action |

它現在比較像一位聰明但必須查證其說法的研究助理，而不是我可以完全委任的智囊團。

---

## 六、這些價值到底來自 NotebookLM，還是來自我們的 Skill？

這是上一份報告最不誠實的地方。

這次 Control 只有一個來源，Advisor 有七個來源。Advisor 回答比較好，是預期結果。

但這沒有回答：

> 如果我手動在 NotebookLM 建立相同 Persona、加入相同七個來源，我是否會得到完全相同的價值？

很可能會。

我們的 Skill 在這次實驗真正證明的只有：

- 可以建立並 read-back Persona。
- 可以把 canonical source 設為 Pinned。
- 可以把 Watchlist 寫進 research query。
- 可以只啟動一次 Deep Research。
- 可以讓我審查後只匯入六個來源。
- 可以保存 registry、run history 和 fulltext export。
- 可以避免重複 URL 和不明刪除。

這些是工程與生命週期價值，但還不是終端使用者能立刻感受到的「智囊品質優勢」。

而 Skill 最重要的主張是 **Evergreen**。這次卻只跑了一個時間點，根本沒有測試：

- 一週後出現新反證時，是否能主動發現？
- 原本的假設是否會被標記為需要重審？
- 新來源是否真的改變建議？
- 舊來源是否安全保留或汰換？
- 一個月後回來，Notebook 是否能告訴我「哪些判斷變了、為什麼變」？

所以這次不能宣稱我們已證明 Skill 的產品價值。

---

## 七、那我們做這件事是不是沒有意義？

### 如果目標是「現在就證明產品成功」

那這次沒有達成，不能假裝達成。

### 如果目標是找出真正值得做的產品

那仍然有意義，因為我們現在知道：

1. 使用者真正需要的不是更多摘要，而是「我的判斷因哪些新證據而改變」。
2. 一次性的 Notebook 問答不是我們的護城河。
3. 真正可能有差異化的是長期 Watchlist、Assumption change、source lifecycle 與 decision history。
4. 沒有 action receipt、引用保存與 conversation boundary，智囊團不值得信任。
5. 我們原本用技術 PASS 取代了產品價值證明，這個評估方式必須停止。

換句話說，這份工作不是已經證明有價值；它是幫我們看見「必須怎樣才可能有價值」。

如果後續不做正確的對照實驗與可信度修正，那繼續增加排程、artifact 或更多 CLI 功能，確實沒有意義。

---

## 八、下一個真正能證明價值的實驗

下一次不能再比較「一個來源 vs 七個來源」。

必須比較三組：

### A：普通 LLM／一般搜尋

只給開發問題，不給持久 Notebook。

### B：手動 NotebookLM

人工建立相同 Persona、相同來源、相同問題。

### C：我們的 Evergreen Skill

使用相同 Persona 與來源，但加入：

- Research Profile
- Assumption／Decision Watchlist
- source provenance
- explicit review
- change history
- 第二次資訊更新週期

### 必須跨兩個時間點

第一輪建立初始決策，例如：

> Gauntlet Loop 適合用於 scoped visual polish，但不適合 zero-to-one game generation。

第二輪加入一份新的、可能支持或反對這個判斷的實戰報告。

然後測量：

1. 哪一組最快指出核心假設受到挑戰？
2. 哪一組能說明「和上次相比改變了什麼」？
3. 哪一組能把改變連回精確來源？
4. 哪一組最少產生 unsupported claim？
5. 哪一組最少假裝執行了不存在的 action？
6. 使用者一週後回來，哪一組最容易恢復決策脈絡？
7. 維護來源需要多少人工時間？

只有 C 明顯勝過 B，才能證明我們的 Skill 有產品價值。

---

## 九、在下一次測試前，必須先修什麼？

### 第一優先：可信度

- 保存 NotebookLM 原始 citation references，而不只是 `[1]` 字樣。
- 每個回答記錄 conversation ID 與是否 fresh session。
- 沒有工具 receipt 時，禁止回答「已建立、已部署、已同步」。
- 把事實、推論、建議與待校準 threshold 分開。
- Git／刪除／部署等指令只能標成 proposed action，不能假裝已執行。

### 第二優先：真正的 Evergreen 差異

- 新證據出現時，直接顯示哪些 Watch Item 改變。
- 產生「上次判斷 → 新證據 → 現在判斷」的 Decision Delta。
- 保留被反駁的舊判斷，而不是只產生一份新的摘要。
- 比較手動 NotebookLM 所需時間與 Skill 自動維護所需時間。

在這兩件事完成前，不應優先做排程或 Studio artifact 自動生成。

---

## 十、我的最終判斷

### 我有沒有學到東西？

**有。**

我從「Gauntlet Loop 是多 Agent 不斷改進」進一步學到：

- 它依賴真正可比較的外部 bar。
- Critic 和 capture harness 都必須被測試。
- 遊戲要先過可玩性與效能 gate，才能進 visual comparison。
- 它更適合 scoped polishing，不適合盲目 zero-to-one。
- 人工停止與縮小 scope 是方法的一部分。
- 公開 demo 證明可能性，但尚未證明商業成熟度與成本效益。

### Notebook 有沒有提供智囊團功能？

**有部分做到。**

它能蒐集跨來源證據、挑戰我沒想到的假設、把模糊興趣轉成開發決策。但它目前不是可信任的自主智囊團，因為它會虛構 action，且 citation audit 不完整。

### 我們的 Skill 有沒有被證明有價值？

**沒有。**

它的工程能力被證明，但相較於手動 NotebookLM 的終端產品價值尚未被證明。真正的證明必須來自跨時間的 A/B/C Evergreen 測試。

### 是否值得繼續？

只有在我們把下一步集中於：

1. 回答可信度；
2. Decision Delta；
3. 跨時間 Watchlist 更新；
4. 與手動 NotebookLM 的直接比較；

才值得繼續。

如果只是繼續加 CLI、排程與更多自動化，卻不證明上述差異，那就不值得。

---

## Evidence

完整原始問答與來源：

```text
~/.local/state/notebooklm-skill/phase5d-20260822T025328Z/live-evidence/
```

- `qa-transcript.md`：Control 與 Advisor 的完整回答
- `advisor/preview/preview.json`：39 個研究候選
- `advisor/preview/selected-urls.json`：人工選入來源
- `export-advisor/source-content/`：七個來源全文
- `field-trial-technical-audit.md`：原本偏工程驗收的報告，保留作技術證據
