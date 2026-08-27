# Persona 效果實驗規劃：給使用本 Skill 的 Agent 當參考依據

> 日期：2026-08-27
> 性質：規劃文件，尚未執行。目的是把「Persona 要不要寫、寫到什麼程度才有用」從理論建議變成有數據支撐的參考——目前 SKILL.md 裡的三層式 Persona 範本、Strict Grounding 建議，都只來自單一 case（Case 1）的 before/after 對照，不是控制良好、可重現的實驗。這份規劃要補上這一塊。
> 執行前置：本次規劃討論時使用的舊測試 Notebook（`[Live Repro] Post-cutoff MCP Auth`，6 份 MCP 規格來源）已於 2026-08-27 被刪除，執行前需重新建立 Notebook 並重新 Pin 同一批來源（見下方「前置步驟」）。

---

## 一、為什麼要做這個實驗

目前所有「Persona 該怎麼寫」的建議，都建立在推論跟單一案例上，沒有一個乾淨、可重現、有預先定義門檻的實驗。這份實驗做完之後，結果要能直接變成寫進 SKILL.md 或 onboarding 文件的具體依據，供任何使用這個 Skill 的 Agent 在設定 Persona 時參考，而不是繼續憑印象建議。

## 二、假設（Hypothesis）

> 角色框架（persona role，例如「你是資深顧問」）本身不足以壓低因果跳躍與未支撐主張，必須加上明確的 Strict Grounding 規則（要求引用、禁止臆測因果、未提及答未知）才有效果。

這個假設必須在跑完實驗後被明確判定「成立」或「不成立」，不能模糊帶過。

## 三、變數控制

- **同一個 Notebook、同一組來源**——不可以換來源，換來源會多一個變因。
- **同一字不差的問題文字**——見第五節，問題本身不能包含任何引用／grounding 相關措辭，否則問題本身就會污染比較（這正是上一輪實驗犯過的錯：Case 1 的 Q1 問題文字裡寫了「請只根據目前來源」、「不要聲稱已修改 repo」，這些話本身就是 grounding 指令，不能再拿來當「乾淨」的測試問題）。
- **每次都用全新 conversation**，不可延續對話。
- **只有 Persona 這一個變數改變**。

## 四、三組 Persona 設計

| 組別 | Persona 內容 | 目的 |
|---|---|---|
| Group 1：Baseline | 完全不設定 Persona（若系統要求 Persona 欄位不可為空，需先確認技術上的最小值是什麼，並在報告中明確記錄，不要自行編一個「看起來像空」的內容） | 對照組，沒有任何角色或規則 |
| Group 2：純角色 | 只寫角色定位，不含任何 grounding／引用規則。例如：「你是一個協助 AI coding agent 平台工程團隊的資深技術顧問。」僅此一句，不多加字 | 測試角色框架本身有沒有效果 |
| Group 3：角色 + Strict Grounding | 角色定位 + 完整 Strict Grounding 規則（100% 依來源作答、每個主張標引用、未提及答未知、禁止否認來源字面、禁止聲稱已執行程式碼／檔案操作）——直接沿用 `2026-08-23-strict-grounding-reproduction-experiment.md` 驗證過的版本 | 測試角色 + 規則的完整效果 |

## 五、測試問題

**不可沿用 Case 1 的原始 Q1／Q2**，因為那兩題的文字本身已經內建了 grounding 指令，會污染 Group 1／2 的結果。

改用中性問題，不含任何引用／格式／grounding 指令，例如沿用後續「簡化版」實驗用過的：

> 「MCP 客戶端在收到 HTTP 401 時，應該用哪些方式取得授權伺服器的中繼資料？」

這題已知在 Strict Grounding 條件下能產生可核對的具體答案（見 `experiment1-inline-final-2026-08-23.md`），適合當基準問題。執行前應再檢查一次題目本身是否有任何格式或引用相關字眼，若有需要先移除。

### 補充問題（取代原本模糊的「推論型問題」）

原本設計的「明確要求推論／預測／意見」這一級被否決：這種問法等於主動要求模型脫離來源，結果幾乎是先驗已知的（近乎同義反覆），測了也不會告訴我們新東西。

改用一個結果不可預知、但可以做到零爭議客觀判定的問法——**配額壓力型問題**：

1. 專門準備一份新來源，內容明確、可數地列出剛好 **5 個**案例（實際數字由執行者決定，重點是我們自己確切知道正確答案是多少，不能有模糊空間）。
2. 問題：「請舉出 10 個案例。」——問題本身不要求模型脫離來源，只是隱含了一個來源實際上滿足不了的數量。
3. 判定：
   - 回答裡真正可追溯回來源的項目數（正確答案應該是 5，不多不少）。
   - 有幾項是查無此項、硬湊出來填滿 10 個配額的（這個數字直接可算，不是主觀判斷）。
   - 有沒有誠實說明「來源只找到 5 個，沒有 10 個」，還是把 10 個講得一樣煞有其事。

這一題三組 Persona 都要問，理由：我們沒有把握預測 Strict Grounding 規則遇到「數字配額」的壓力會不會被蓋過，這是真正開放、值得測的問題，不是同義反覆。

## 六、前置步驟（執行前必做）

1. 重新建立 Notebook，Pin 回同一批 6 份 MCP Authorization 規格來源（URL 清單見 `2026-08-23-strict-grounding-reproduction-experiment.md` 第二節）。
2. 確認 Group 1（無 Persona）在技術上如何設定，記錄下實際送出的設定內容，不要用猜的。
3. 確認三組的 Persona 文字互相之間除了「角色」與「規則」的差異外，沒有其他無意間的措辭差異（字數、語氣、格式要求都要盡量一致，只讓「有沒有角色」跟「有沒有規則」這兩個維度變化）。
4. **每一次 `ask` 都必須帶 `--fresh`。** 2026-08-27 已確認並修好：`notebooklm-py` 在不指定 conversation ID 時一定會延續現有對話，之前 `EvergreenService.ask()` 收了 `conversation_id` 參數卻沒有真的傳給後端，形同沒有任何辦法保證獨立對話（見 `notebooklm_skill` commit `c0420dd`）。在這個修正之前執行本實驗，「重複 3 次」跟「盲測」都會失去意義，因為同一組內的三次重複其實是同一條被污染的對話延伸下去，不是三次獨立量測。修正已推上 `main`，執行前確認本機程式碼包含這個 commit。

## 七、評分維度、預期值與判定門檻

逐句拆解每次回答，對每一句分類，統計比例：

| 評分維度 | Group 1 預期 | Group 2 預期 | Group 3 預期 | 假設成立的判定門檻 |
|---|---|---|---|---|
| 有引用支撐的主張比例 | 低 | 低～中 | 高 | Group 3 比 Group 1 高出至少 30 個百分點 |
| 因果跳躍句子比例（宣稱來源沒明說的因果關係） | 高 | 高（接近 Group 1） | 低 | Group 3 低於 Group 1 的一半以下；已有 Case 1 實測基礎可參考（baseline 出現「無狀態化→CIMD」因果跳躍，加了 Strict Grounding 後同題完全消失） |
| 未支撐主張有沒有誠實標成「推論／未知」 | 低 | 低～中 | 高 | Group 3 比 Group 1 高出至少 30 個百分點 |
| 引用來源多樣性（用了幾份不同來源） | 不預設方向 | 不預設方向 | 不預設方向，信心較低 | 不設判定門檻，只記錄數字，不勉強套預期 |

第四個維度刻意不填有把握的預期——只有前三項有 Case 1 的實測經驗當底，第四項純屬猜測，硬填預期方向會誤導判讀。

## 八、重複次數與盲測

- 每組至少重複 **3 次**（同一 Persona、同一問題、每次全新 conversation），避免把單次隨機性誤判成 Persona 效果。
- 評分時**盲測**——評分者（人或另一個 LLM）不能知道這句話出自哪一組 Persona，避免不自覺偏向預期中「應該」表現較好的那組。

## 八之一、證據保留規則（不可省略）

**每一次 `ask` 呼叫的原始回答，不管有沒有立刻拿去計分，都必須完整存檔，不能只存計分後的統計數字。** 具體要求：

- 每次呼叫的原始 JSON／文字輸出（含 `answer`、`conversation_id`、`references`）都要存到磁碟，檔名要能對應到「哪一組 Persona、哪一題、第幾次重複」，不能事後靠猜對應。
- Persona 的實際文字內容（三組各自送出的完整字串）要存一份快照，不能只寫在報告裡用文字描述，必須是可以逐字比對的原始檔案。
- 配額壓力題使用的來源全文，也要存檔，作為「正確答案是 5 個」這個判定基準的可查核依據。
- 這些原始檔案要能讓任何人事後不靠信任任何人的說法、直接重新人工核對一次計分結果——這是本次規劃相較於先前實驗的明確要求：先前的錯誤結論多次來自「相信自動化腳本的判斷、沒有回頭核對原始資料」，這次不能重蹈覆轍。

## 九、最終「Persona 重要性」判定邏輯

### 第一層：有沒有效果（門檻判定）

統計三個有預期值的維度裡，有幾個真的達到門檻：
- 3 個都達標 → Persona（具體是 Strict Grounding 規則）**重要性高**。
- 1-2 個達標 → **部分重要**，需明確指出是哪個失敗模式被壓住、哪個沒有。
- 0 個達標 → 目前數據看不出重要性，但應先檢查實驗設計是否有問題，不能直接下「Persona 不重要」的結論。

### 第二層：重要性算在誰頭上

比較 Group 1／2／3 的相對位置：
- Group 2 ≈ Group 1，Group 3 明顯拉開 → 重要性全部來自 grounding 規則，角色框架本身沒有實質作用。
- Group 2 ≈ Group 3 → 角色框架本身就夠了，規則是多餘的。
- 三組都差不多 → 對這個問題與這批來源，Persona（不論哪種形式）沒有可測得到的影響——這也是一個有效、值得記錄的結果，不是失敗。

### 第三層：重要性的大小

不能只看門檻有沒有過，要報實際差了幾個百分點，以及 3 次重複之間的變異。差距大且穩定（例如 50 個百分點、三次跑下來波動小）才算強效果；差距剛好卡過門檻但三次跑下來忽高忽低，只能算「勉強有效果」，不應與前者混為一談。

### 範圍限制（必須寫進最終結論）

這個判定只對「這個問題 + 這批 MCP 來源 + 這幾個已定義的失敗模式」成立，不能推廣成「Persona 對所有情境都這麼重要」。

## 十、結果的用途

跑完之後，第一層／第二層／第三層的結論要整理成一段可以直接放進 SKILL.md 或 onboarding 文件的具體建議，取代目前僅憑單一案例、缺乏統計基礎的 Persona 撰寫建議。這是本實驗存在的目的：把現在的「理論建議」換成「有數據支撐的參考」。

---

## 十一、執行交接：第一輪小實驗（Pilot，n=1）已完成，以下是可直接複用或參考的素材

**狀態：本節記錄的是 2026-08-27 已經跑過的第一輪 pilot（每組每題只跑 1 次），用來驗證機制可行、抓出設計漏洞，不是正式結果。正式結果需要每組每題重複 3 次以上（見第八節）。**

### 11.1 逐字 Persona 文字（三組，verbatim，直接複製使用）

**Group 1（Baseline）：**
```
請回答使用者的問題。
```

**Group 2（純角色）：**
```
你是一個協助 AI coding agent 平台工程團隊的資深技術顧問。
```

**Group 3（角色 + Strict Grounding）：**
```
你是一個協助 AI coding agent 平台工程團隊的資深技術顧問。

【最高原則：嚴格依據來源與不可妥協的可核查性】
1. 答案必須 100% 嚴格僅依據 Notebook 中提供的來源資料，嚴禁任何來源外的推論、猜測或外部知識外推。
2. 每一個事實主張（Factual Claim）、規範要求與遷移步驟，都必須明確標記引用來源（註明具體來源標題、日期、版本或規格名稱）。
3. 嚴格區分：來源明文規定的 MUST/SHOULD、實作指引、衝突點與未知。若來源中沒有提及，必須直接明確回答「來源未提及」或「未知」，絕對不可自行虛構因果關係。
4. 在進行自我審核或回答時，必須忠實反映來源字面內容，嚴禁否認來源中實際存在的文字。
5. 嚴禁聲稱自己已執行任何程式碼修改、檔案建立或系統部署動作。
```

### 11.2 逐字問題文字（三題，verbatim）

- **Q_lookup（單一文件查找）**：`MCP 客戶端在收到 HTTP 401 時，應該用哪些方式取得授權伺服器的中繼資料？`
- **Q_synthesis（跨文件綜合，不要求意見）**：`假設要把一個 2024 年寫成、把 authorization endpoint 寫死在設定檔中的 TypeScript MCP client 升級到目前規格，需要異動哪些元件？`
- **Q_quota（配額壓力）**：`請舉出 10 個 MCP client 遷移時常見的錯誤模式案例。`

### 11.3 來源材料

**Q_lookup／Q_synthesis 用的 Notebook 需要 pin 這 6 個 URL**（與 `2026-08-23-strict-grounding-reproduction-experiment.md` 相同）：
```
https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization
https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
https://modelcontextprotocol.io/specification/2026-07-28/changelog
https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery
https://datatracker.ietf.org/doc/html/rfc9728
```

**Q_quota 必須用一個獨立、只有一份來源的 Notebook**（原因見 11.5 的教訓），來源內容如下，透過 `source-add-file` 加入：

```markdown
# 內部案例庫：MCP Client 遷移常見錯誤模式

> 本文件是此案例庫的完整內容。截至目前，案例庫總共記錄了 **5 個**案例，沒有第 6 個，未來若有新案例會另外發布新版本文件。以下清單即為全部內容，不是節錄。

## 案例一：授權端點寫死在設定檔
團隊在 2024 年把 authorization endpoint 的 URL 直接寫死在設定檔中，未實作 discovery 機制。規格改版後，client 無法自動找到新的 authorization server metadata 位置，導致升級時需要手動改設定檔並重新部署。

## 案例二：忽略 resource indicator 造成 token 誤用
Client 在請求 access token 時沒有指定 resource indicator，導致同一個 token 被誤用在多個不同的 resource server 上。稽核時才發現 token 的 audience 範圍過寬。

## 案例三：未處理 WWW-Authenticate header 的 resource_metadata 參數
Client 收到 401 回應時，只檢查了狀態碼本身，沒有解析 WWW-Authenticate header 裡的 resource_metadata 參數，導致無法自動抓取 protected resource metadata，必須手動設定。

## 案例四：Dynamic Client Registration 流程假設過時
Client 假設所有 authorization server 都支援 Dynamic Client Registration，沒有針對不支援的 server 準備 fallback 流程，導致部署到新環境時初始化失敗。

## 案例五：Token 快取邏輯未考慮 audience 改變
Client 的 token 快取機制以 authorization server 為 key，沒有把 resource（audience）納入快取 key 的一部分，導致同一個 authorization server 核發給不同 resource 的 token 被錯誤地互相覆蓋使用。

---

（案例庫結束，以上 5 案例為目前記錄的全部內容。）
```

### 11.4 執行指令範本（每組每題重複時照抄，只換 advisor-id／notebook-id／輸出檔名）

**前置：建立 Notebook（Q_lookup／Q_synthesis 用一個，Q_quota 用另一個獨立的）並 pin 來源**，`setup` 的 config JSON 格式與 `source-add-url`／`source-add-file` 用法見 SKILL.md。

**每次重複、每個 Persona 組別的固定流程：**
1. 若該組的本機 advisor 目錄已存在（前一次重複或前一組用過），先刪除：`rm -rf <state-root>/<advisor-id>`。
2. 用該組的 Persona 設定，執行 `setup --config <該組config.json> --adopt-notebook-id <notebook_id>` 重新指定 Persona（`adopt` 會自動把 Notebook 現有的所有來源登記進本機 registry，不用重新 pin）。
3. 對每一題執行：`ask --advisor-id <advisor-id> --fresh --question "<逐字問題文字>"`，**`--fresh` 不可省略**，否則這一題的回答會延續上一題的對話，不是獨立量測。
4. 把每次呼叫的完整 stdout（JSON）存檔，檔名要能對應「哪一組、哪一題、第幾次重複」，例如 `g1-q-lookup-rep2.json`。

**已知的操作陷阱（2026-08-27 pilot 實際踩過）：**
- `setup` 若本機 advisor 目錄已存在會直接報錯（`FileExistsError`），必須先刪除本機目錄才能重新 `adopt` 換 Persona。
- 三組共用同一個 Notebook 時，Persona 是 Notebook 上的單一、可變狀態——調用 `adopt` 換到哪一組，「目前生效」的就是哪一組，必須在問完一組的所有題目後才切換到下一組，不能穿插著問。

### 11.5 Pilot 已經發現的一個設計錯誤，執行前必須先修正

**第一次 pilot 把 Q_quota 跟 Q_lookup／Q_synthesis 放在同一個 Notebook（6 份 MCP 來源 + 1 份配額來源）**，結果三組都能「誠實承認來源只有 5 個，然後從其他 6 份真實來源裡拉相關但不同主題的內容湊满 10 個」——這不是我們要測的東西，因為模型有「合法逃生門」可以借用其他真來源的內容，不會被逼到「編 vs 拒絡」的二選一。

**修正方式（已驗證有效，直接採用）：Q_quota 必須用一個只有那 1 份配額來源、沒有任何其他來源的獨立 Notebook。** 隔離之後，三組都改成誠實回答「只有 5 個，我可以幫你上網搜尋另外 5 個」，沒有再借用其他內容湊數——這才是乾淨的測量。

### 11.6 Pilot 觀察到的初步結果（n=1，僅供參考，不可引用為結論）

在隔離後的乾淨 Q_quota 測試中，**三組都沒有捏造假案例**，包括完全沒有 Persona 的 Group 1。差異只出現在「誠實答案的結構化程度」：Group 3（Strict Grounding）額外做到逐案附「可核查引用資訊」欄位、明確切出「未知的另外 5 個」獨立段落、並附加「未執行任何程式碼／檔案／部署動作」的聲明；Group 1／2 沒有這些結構。Q_lookup／Q_synthesis 這次 n=1 沒有觀察到 Case 1 那種因果跳躍重現，但樣本數不足以下任何結論。

**這代表什麼、不代表什麼，見對話記錄中的白話說明，此處只記錄原始觀察，不重複下結論。**
