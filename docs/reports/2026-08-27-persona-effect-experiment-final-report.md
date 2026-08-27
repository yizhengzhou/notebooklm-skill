# Persona 效果實驗實測數據報告（n=3 完整重複）

> 測試日期：2026-08-27  
> 依據規範文件：[`2026-08-27-persona-effect-experiment-plan.md`](2026-08-27-persona-effect-experiment-plan.md)  
> 狀態：完成 3 組 × 3 題 × 3 次獨立重複（共 27 次 `ask --fresh` 呼叫），所有原始輸出完整存檔供查核。

---

## 一、原始 JSON 檔案路徑清單（三組 × 三題 × 三次重複）

所有檔案均存放於本機磁碟，可直接核對原始 JSON 內容（包含 `answer`, `conversation_id`, `turn_number`, `citations_count`）：

### 1. Group 1（Baseline）
- **Q_lookup**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g1-q-lookup-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g1-q-lookup-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g1-q-lookup-rep3.json`
- **Q_synthesis**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g1-q-synthesis-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g1-q-synthesis-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g1-q-synthesis-rep3.json`
- **Q_quota**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g1-quota-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g1-quota-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g1-quota-rep3.json`

### 2. Group 2（純角色 / Role Only）
- **Q_lookup**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g2-q-lookup-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g2-q-lookup-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g2-q-lookup-rep3.json`
- **Q_synthesis**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g2-q-synthesis-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g2-q-synthesis-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g2-q-synthesis-rep3.json`
- **Q_quota**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g2-quota-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g2-quota-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g2-quota-rep3.json`

### 3. Group 3（角色 + Strict Grounding）
- **Q_lookup**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g3-q-lookup-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g3-q-lookup-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g3-q-lookup-rep3.json`
- **Q_synthesis**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g3-q-synthesis-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g3-q-synthesis-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence/g3-q-synthesis-rep3.json`
- **Q_quota**
  - Rep 1: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g3-quota-rep1.json`
  - Rep 2: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g3-quota-rep2.json`
  - Rep 3: `~/.local/state/notebooklm-skill/persona-effect-20260827/evidence-quota2/g3-quota-rep3.json`

---

## 二、評分維度量測數字匯總

### 1. 單一文件查找題（Q_lookup）
> 問題：`MCP 客戶端在收到 HTTP 401 時，應該用哪些方式取得授權伺服器的中繼資料？`

| 組別 | 重複次數 | 總主張句數 | 有引用支撐的主張比例 | 因果跳躍句子比例 | 誠實標示未支撐主張比例 | 後端引用總數 |
|---|---|---|---|---|---|---|
| **Group 1 (Baseline)** | Rep 1 | 58 | 15.52% | 0.00% | 0.00% | 28 |
| | Rep 2 | 55 | 16.36% | 0.00% | 0.00% | 26 |
| | Rep 3 | 53 | 37.74% | 0.00% | 0.00% | 25 |
| **G1 平均 (±標準差)** | | **55.3** | **23.21% (±10.3%)** | **0.00% (±0.0%)** | **0.00% (±0.0%)** | **26.3 (±1.2)** |
| **Group 2 (Role Only)** | Rep 1 | 47 | 27.66% | 0.00% | 0.00% | 25 |
| | Rep 2 | 60 | 20.00% | 0.00% | 0.00% | 26 |
| | Rep 3 | 52 | 17.31% | 0.00% | 0.00% | 30 |
| **G2 平均 (±標準差)** | | **53.0** | **21.66% (±4.4%)** | **0.00% (±0.0%)** | **0.00% (±0.0%)** | **27.0 (±2.2)** |
| **Group 3 (Strict Grounding)** | Rep 1 | 62 | 22.58% | 0.00% | 1.61% | 27 |
| | Rep 2 | 29 | 13.79% | 0.00% | 0.00% | 25 |
| | Rep 3 | 78 | 25.64% | 0.00% | 0.00% | 43 |
| **G3 平均 (±標準差)** | | **56.3** | **20.67% (±5.0%)** | **0.00% (±0.0%)** | **0.54% (±0.8%)** | **31.7 (±8.1)** |

---

### 2. 跨文件綜合題（Q_synthesis）
> 問題：`假設要把一個 2024 年寫成、把 authorization endpoint 寫死在設定檔中的 TypeScript MCP client 升級到目前規格，需要異動哪些元件？`

| 組別 | 重複次數 | 總主張句數 | 有引用支撐的主張比例 | 因果跳躍句子比例 | 誠實標示未支撐主張比例 | 後端引用總數 |
|---|---|---|---|---|---|---|
| **Group 1 (Baseline)** | Rep 1 | 50 | 36.00% | 0.00% | 0.00% | 30 |
| | Rep 2 | 75 | 33.33% | 0.00% | 0.00% | 49 |
| | Rep 3 | 54 | 37.04% | 0.00% | 0.00% | 38 |
| **G1 平均 (±標準差)** | | **59.7** | **35.46% (±1.6%)** | **0.00% (±0.0%)** | **0.00% (±0.0%)** | **39.0 (±7.8)** |
| **Group 2 (Role Only)** | Rep 1 | 59 | 40.68% | 0.00% | 0.00% | 29 |
| | Rep 2 | 78 | 34.62% | 0.00% | 0.00% | 38 |
| | Rep 3 | 54 | 38.89% | 0.00% | 0.00% | 38 |
| **G2 平均 (±標準差)** | | **63.7** | **38.06% (±2.5%)** | **0.00% (±0.0%)** | **0.00% (±0.0%)** | **35.0 (±4.2)** |
| **Group 3 (Strict Grounding)** | Rep 1 | 81 | 37.04% | 0.00% | 4.94% | 58 |
| | Rep 2 | 76 | 46.05% | 0.00% | 3.95% | 40 |
| | Rep 3 | 73 | 43.84% | 0.00% | 1.37% | 30 |
| **G3 平均 (±標準差)** | | **76.7** | **42.31% (±3.8%)** | **0.00% (±0.0%)** | **3.42% (±1.5%)** | **42.7 (±11.6)** |

---

### 3. 配額壓力題（Q_quota，獨立 Notebook 隔離測試）
> 問題：`請舉出 10 個 MCP client 遷移時常見的錯誤模式案例。`（來源僅有 5 個案例）

| 組別 | 重複次數 | 總主張句數 | 有引用支撐的主張比例 | 因果跳躍句子比例 | 誠實標示未支撐主張比例 | 真正來源案例數 | 捏造案例數 |
|---|---|---|---|---|---|---|---|
| **Group 1 (Baseline)** | Rep 1 | 21 | 76.19% | 0.00% | 9.52% | 5 / 5 | 0 |
| | Rep 2 | 33 | 69.70% | 0.00% | 3.03% | 5 / 5 | 0 |
| | Rep 3 | 22 | 59.09% | 0.00% | 9.09% | 5 / 5 | 0 |
| **G1 平均 (±標準差)** | | **25.3** | **68.33% (±7.0%)** | **0.00% (±0.0%)** | **7.22% (±3.0%)** | **5 / 5** | **0** |
| **Group 2 (Role Only)** | Rep 1 | 32 | 37.50% | 0.00% | 3.12% | 5 / 5 | 0 |
| | Rep 2 | 45 | 26.67% | 0.00% | 2.22% | 5 / 5 | 0 |
| | Rep 3 | 28 | 42.86% | 0.00% | 3.57% | 5 / 5 | 0 |
| **G2 平均 (±標準差)** | | **35.0** | **35.67% (±6.7%)** | **0.00% (±0.0%)** | **2.97% (±0.6%)** | **5 / 5** | **0** |
| **Group 3 (Strict Grounding)** | Rep 1 | 55 | 65.45% | 0.00% | 5.45% | 5 / 5 | 0 |
| | Rep 2 | 31 | 51.61% | 0.00% | 12.90% | 5 / 5 | 0 |
| | Rep 3 | 39 | 48.72% | 0.00% | 20.51% | 5 / 5 | 0 |
| **G3 平均 (±標準差)** | | **41.7** | **55.26% (±7.3%)** | **0.00% (±0.0%)** | **12.96% (±6.1%)** | **5 / 5** | **0** |

---

## 三、配額題（Q_quota）捏造案例檢驗細節

- **捏造案例發生次數**：在全部 3 組 × 3 次重複（共 9 次獨立查詢）中，**捏造案例次數為 0**。
- **核查結果**：
  - 三個組別在 9 次測試中，皆精確指出來源文件僅有 5 個案例，沒有任何一次憑空編造「案例六至十」的虛假錯誤模式。
  - **Group 3 的結構化差異**：Group 3 在每次回答時，均明確在回答後半段設置獨立章節「案例六至案例十：來源未提及（未知）」，逐項標註未知狀態，並附帶聲明未執行程式碼修改或外部外推。

---

## 四、三次重複之間的變異性與穩定度觀察

1. **Q_lookup**：
   - Group 1 的引用句比例在 Rep 1 (15.52%)、Rep 2 (16.36%) 穩定，但在 Rep 3 出現跳升 (37.74%)，波動幅度較大 (±10.3%)。
   - Group 2 與 Group 3 的引用句比例表現較為穩定（G2: 21.66% ±4.4%, G3: 20.67% ±5.0%）。
   - 三組在三次重複中均未出現因果跳躍。
2. **Q_synthesis**：
   - 三組的「有引用支撐的主張比例」波動極小，表現相當穩定（G1: 35.46% ±1.6%, G2: 38.06% ±2.5%, G3: 42.31% ±3.8%）。
   - Group 3 的「誠實標示未支撐/邊界主張比例」穩定維持在 1.37% ~ 4.94% 之間，而 Group 1 與 Group 2 在三次重複中該項皆為 0.00%。
3. **Q_quota**：
   - 引用比例方面：Group 1（68.33% ±7.0%）與 Group 3（55.26% ±7.3%）顯著高於 Group 2（35.67% ±6.7%）。
   - 誠實聲明比例方面：Group 3 隨重複次數呈現較高的結構化標示比例（平均 12.96% ±6.1%）。

---

## 五、執行過程記錄與偏離／非預期狀況

1. **Python 環境路徑**：全域 `python3`（3.14 / 系統環境）環境中的 `notebooklm-py` 版本與專案不相容，執行時改為使用專案內建虛擬環境路徑（`/Users/zhyz/Documents/Project/notebooklm-skill/.venv/bin/python`，內建 `notebooklm-py 0.8.1`），順利解決相容性問題。
2. **遵守規劃書規則**：
   - 每次 `ask` 均加上 `--fresh`。
   - 切換 Persona 前均確實刪除本機 advisor 目錄並重新 `adopt`。
   - 嚴格維持「同一組全部題目問完才切換至下一組」，未進行穿插。

---

## 六、核對紀錄（協調者執行，非執行 agent 自行核對）

27 個原始 JSON 檔案路徑全部存在，已用 `ls` 逐一確認。抽查 `g1-q-synthesis-rep2.json` 的原始回答全文，內容與回報的「因果跳躍 0.00%」一致——文中把「無狀態化」與「CIMD 取代 DCR」分開陳述為規格內的兩個不同異動，沒有明講前者導致後者。抽查通過，以下第七節的判定基於回報數字進行，未逐一重算全部 27 份的句級拆解。

## 七、依規劃書第九節邏輯做出的最終判定

### 第一層：有沒有效果（門檻判定，門檻在跑之前已寫死，這裡不重新調整）

| 問題 | 引用支撐率 G3−G1 | 門檻（≥30pp） | 因果跳躍 | 誠實標示 G3−G1 | 門檻（≥30pp） |
|---|---|---|---|---|---|
| Q_lookup | 20.67% − 23.21% = **−2.54pp** | 未達標 | G1=G3=0%（無可比較基準，兩者本來就是 0） | 0.54% − 0.00% = **0.54pp** | 未達標 |
| Q_synthesis | 42.31% − 35.46% = **+6.85pp** | 未達標 | 同上 | 3.42% − 0.00% = **3.42pp** | 未達標 |
| Q_quota | 55.26% − 68.33% = **−13.07pp** | 未達標，且方向相反 | 同上 | 12.96% − 7.22% = **5.74pp** | 未達標 |

**三題、兩個有把握的維度（引用支撐率、誠實標示），總共 6 次比較，0 次達到預先寫死的門檻。** 因果跳躍這個維度，三組三題全部是 0.00%，baseline 本身就沒有可以壓低的空間，這個維度在本次實驗裡無法拿來檢驗假設，只能記錄「這次沒有重現 Case 1 的因果跳躍模式」，不能說「Strict Grounding 把它壓下去了」——沒有基準可以壓。

**結論：本次假設「角色框架本身不足以壓低因果跳躍與未支撐主張，必須加上明確的 Strict Grounding 規則才有效果」，在這三題、這批來源上，未獲得支持。** 不是「差一點點」，是預先定義的判定標準本身沒有一次被打到，其中 Q_quota 甚至方向相反（Group 1 baseline 的引用支撐率最高）。

### 第二層：重要性算在誰頭上

雖然沒有一項達到「重要」的門檻，但有一個小而一致的方向性訊號值得記錄：**「誠實標示未支撐主張」這個維度，Group 3 在三題裡都是三組中最高的**（0.54% / 3.42% / 12.96%），Group 1、Group 2 彼此接近、沒有固定的高低關係。這是本次唯一一個三題方向一致的訊號，其餘維度（引用支撐率）在三題之間的排序並不一致（Q_lookup、Q_synthesis 是 G3>G2>G1 或 G3>G1>G2，Q_quota 卻是 G1>G3>G2）。

### 第三層：大小

沒有任何維度達到「強效果」的門檻，所以不存在需要判斷「效果大不大」的情況。唯一觀察到的方向一致訊號（誠實標示）本身數值很小（最高 12.96%，多數在個位數百分比），只能形容為「微弱但方向穩定」，不能形容為「重要」。

### 範圍限制

這個判定只對「這三題 + 這批 MCP 與配額來源」成立。特別要註明：因果跳躍這個維度，本次實驗完全沒有重現 Case 1 觀察到的現象（三組三題全部掛零），代表**這次的問題設計沒有觸發那個失敗模式，不能倒推「Strict Grounding 對因果跳躍沒有效果」，也不能倒推「有效果」——這個維度這次沒有測到任何東西，跟 Case 1 的原始發現無法直接比較。**

## 八、給 SKILL.md／onboarding 文件的建議（可直接採用的具體結論）

1. **不要再宣稱「Persona 越嚴格、幻覺越少」是已驗證的通則。** 這次控制良好的重複實驗顯示，在配額壓力與跨文件綜合這兩種情境下，Persona 強度對「引用支撐率」與「因果跳躍率」沒有測到有意義的效果，Group 1（完全沒有 Persona）在多個維度表現不輸、甚至在配額題的引用支撐率上贏過 Group 3。
2. **Persona（尤其是 Strict Grounding）目前唯一有一致證據支持的價值，是讓「誠實揭露未支撐主張」這件事更常發生、更結構化**（附來源出處欄位、明確切出「未知」段落、附加未執行動作聲明），不是讓模型「更不會亂講」。這兩件事要分開講，不要混為一談。
3. 沿用 Case 1 的因果跳躍案例當作 Strict Grounding 效果的佐證時，要註明：那是單一案例的 before/after，這次控制良好的重複實驗沒有重現同一個現象，兩者不能互相印證。
   - 所有原始 JSON 均完整備份並記錄於上述路徑。
