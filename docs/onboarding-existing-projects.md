# NotebookLM Onboarding: Existing Projects（Legacy v1 — 目前與 v2 Runtime Contract 不相容）

> ⚠️ **狀態：Legacy v1，暫不可執行。** 本文件描述的雙 Notebook（Research／Project pair）
> 架構、`scripts/run.py`（`auth_manager.py`、`create_notebook.py --pair`）呼叫方式，
> 以及專案資料夾批次掃描匯入，皆違反 `SKILL.md` 的 v2 Runtime Contract（單一
> Evergreen Advisor Notebook、僅能用 `python -m notebooklm_skill.cli ...`、不得使用
> `scripts/`、不得掃描專案資料夾、不得強制 Research/Project pair）。詳見 SKILL.md
> 「Runtime contract」與「Legacy v1」兩節。
>
> **更根本的問題：v2 的 CLI 目前沒有任何匯入本地檔案／文字的公開指令**（只有
> `source-add-url`）。後端 `add_text_source()` 已存在且有測試覆蓋，但尚未包裝成
> Advisor 方法或 CLI 指令。也就是說，本文件描述的「把既有專案文件匯入 NotebookLM」
> 這個工作流程，在 v2 目前的公開能力下**做不到**，不只是指令名稱要換而已。
>
> 在 v2 的 `source-add-text`／`source-add-file` 指令補上之前，請不要照本文件執行；
> 若只需要追蹤外部規格／文件的 URL，改用 `source-add-url` 搭配 v2 的 Preview →
> Selection → Plan → Digest Approval → Apply 流程（見 SKILL.md）。本文件其餘章節
> （文件盤點、過濾判斷、合併策略、反模式）的**方法論**仍然有效，只有「執行指令」
> 部分是 v1 遺留、不能直接照抄。

> **第一原理：** 聘請 NotebookLM 當你的專案文件管理員。每次查詢都應該返回有引用、有根據的答案 — 不是 AI 幻覺，而是你自己文件中的真實知識。

本文件是一個完整的方法論：如何將一個已有大量文件的專案，中途導入 NotebookLM 雙 notebook 架構。**下方的雙 notebook 架構與 `scripts/run.py` 指令為 v1 遺留內容，見上方警語。**

---

## 0. 前置條件（5 分鐘）

- [ ] NotebookLM skill 已安裝並認證（`python scripts/run.py auth_manager.py status`）
- [ ] 已建立雙 notebook（`python scripts/run.py create_notebook.py --name "ProjectName" --pair`）
- [ ] 了解 NotebookLM 硬限制：每 notebook 最多 **50 sources**，每 source 最多 **500,000 字**

---

## 1. 文件盤點（Audit）

### 1.1 掃描專案

列出所有文件文件：
```bash
find /path/to/project -name "*.md" -o -name "*.txt" | wc -l      # 總數
find /path/to/project -name "*.md" -o -name "*.txt" | head -50    # 取樣
```

### 1.2 分類登記

將每個文件歸入以下 **7 種類型** 之一：

| 類型 | 定義 | 範例 |
|------|------|------|
| **A. 策略/研究** | 市場分析、用戶研究、競品分析、商業模型 | `BUSINESS_MODEL_MASTER.md`, `COST_BENCHMARK.md` |
| **B. 架構/規格** | 技術 PRD、系統設計、API 規格、資料模型 | `TECHNICAL_PRD.md`, `PIPELINE_ARCHITECTURE.md` |
| **C. 決策記錄** | 為什麼選 X 而不是 Y、架構決策、trade-off 分析 | `BACKEND_UNIFICATION_PLAN.md` |
| **D. 操作手冊** | 部署流程、Runbook、環境設定、CI/CD | `railway.md`, `ios.md`, `android.md` |
| **E. 症狀索引** | 跨版本有效的 troubleshooting 模式、根因分析 | `SYMPTOM_INDEX.md`, `TIER_INSTABILITY_DIAGNOSIS.md` |
| **F. 時間快照** | 帶時間戳的報告、session log、build audit、test report | `railway_backend_test_report_20260115.md` |
| **G. 已歸檔** | archive/ 目錄下的任何文件 | `archived_docs_*.md` |

---

## 2. 過濾決策（The Filter）

### 2.1 快速淘汰規則

以下文件 **直接排除**，不進 NotebookLM：

| 排除條件 | 理由 | 影響量（以 VerifyAI 為例） |
|----------|------|--------------------------|
| 類型 F（時間快照） | 過期數據會污染查詢結果 | ~250 個文件 |
| 類型 G（已歸檔） | 已失效，且 git 裡有完整歷史 | ~174 個文件 |
| 檔名含連續日期戳 (`*_20260115*`) | 報告系列中只保留最新一份 | ~100 個文件 |
| 內容 < 200 字 | 太短，沒有查詢價值 | ~30 個文件 |
| 純 log/dump 格式（無結構、無分析） | Gemini 無法從中提取有意義的答案 | ~20 個文件 |

### 2.2 保留判斷標準

對剩餘文件，逐一問 **三個問題**：

```
┌─ Q1: 三個月後，我是否還會需要查詢這份文件中的知識？
│   └─ 否 → 排除
│
├─ Q2: 這份知識是否已經反映在 code、git commit、或其他保留文件中？
│   └─ 是 → 排除（避免冗餘）
│
└─ Q3: 如果把這份文件刪掉，我是否會失去無法從其他地方恢復的知識？
    └─ 否 → 排除
    └─ 是 → 保留 ✓
```

### 2.3 VerifyAI 實際結果

| 類型 | 原始數量 | 通過過濾 | 保留率 |
|------|---------|---------|--------|
| A. 策略/研究 | ~50 | ~20 | 40% |
| B. 架構/規格 | ~30 | ~15 | 50% |
| C. 決策記錄 | ~15 | ~10 | 67% |
| D. 操作手冊 | ~7 | ~5 | 71% |
| E. 症狀索引 | ~5 | ~5 | 100% |
| F. 時間快照 | ~370 | 0 | 0% |
| G. 已歸檔 | ~174 | 0 | 0% |
| **合計** | **~654** | **~55** | **8.4%** |

**結論：654 個文件中只有 ~55 個通過，正好在雙 notebook 容量內（Research 25 + Project 30）。**

---

## 3. 路由決策（Research vs Project）

通過過濾的文件，根據以下規則分配到對應的 notebook：

```
                    這份文件回答的問題是...
                           │
              ┌────────────┴────────────┐
              ▼                          ▼
     「為什麼」/「誰」/「市場」      「怎麼做」/「是什麼」/「架構」
              │                          │
              ▼                          ▼
       Research Notebook            Project Notebook
              │                          │
    ┌─────────┤                ┌─────────┤
    ▼         ▼                ▼         ▼
  策略/研究  商業模型        架構/規格  決策記錄
  用戶研究   競品分析        操作手冊   症狀索引
  市場數據                   DevOps 精華
```

### 明確的路由表

| 文件類型 | → Notebook | Category Prefix |
|----------|-----------|-----------------|
| A. 策略/研究 | **Research** | `[策略]`, `[用戶痛點]`, `[競品分析]`, `[市場數據]` |
| B. 架構/規格 | **Project** | `[架構]`, `[規格]` |
| C. 決策記錄 | **Project** | `[決策]` |
| D. 操作手冊 | **Project** | `[Runbook]` |
| E. 症狀索引 | **Project** | `[DevOps]` |

---

## 4. 合併策略（Consolidation）

NotebookLM 每個 notebook 限 50 sources。如果通過過濾的文件 > 25（單 notebook 建議上限），需要合併。

### 4.1 合併規則

| 情境 | 處理方式 | 範例 |
|------|---------|------|
| 同主題的 3+ 份文件 | 合併為 1 份摘要 source | 5 份 Tier 系統文件 → 1 份 `[DevOps] Tier System — Diagnosis & Fixes` |
| 同類型的碎片文件（各 <1000 字） | 打包為 1 份集合 source | 3 份 Runbook → 1 份 `[Runbook] Deployment Guides — iOS / Android / Railway` |
| 報告系列（只保留最新） | 取最新版，丟棄舊版 | 10 份 project status → 只留最新 1 份 |

### 4.2 合併後的 Source 格式模板

```markdown
# [Category] Title — Subtitle

> 合併自：file1.md, file2.md, file3.md
> 最後更新：2026-03-26
> 權重：[權重:高 — 涵蓋 N 個原始文件]

## 主題 1
[內容，保留關鍵細節和原始引用]

**為何重要：** [一句話解釋為什麼這對專案有價值]

## 主題 2
[...]

---
*本 source 由 NotebookLM onboarding 流程生成。原始文件保留在 git 中。*
```

### 4.3 VerifyAI 合併後的 Source Budget

**Research Notebook（~15 sources）：**

| # | Source 名稱 | 合併來源 | Category |
|---|-----------|---------|----------|
| 1 | Business Model & Pricing | BUSINESS_MODEL_MASTER + COST_BENCHMARK | `[策略]` |
| 2 | Product Audit 2026-01 | PRODUCT_AUDIT_2026-01-11 | `[策略]` |
| 3 | User Pain Points — Consolidated | 用戶研究相關文件 | `[用戶痛點]` |
| 4 | Competitor Analysis | 競品分析相關文件 | `[競品分析]` |
| 5-15 | (其餘策略/市場文件) | ... | ... |

**Project Notebook（~20 sources）：**

| # | Source 名稱 | 合併來源 | Category |
|---|-----------|---------|----------|
| 1 | Technical PRD | TECHNICAL_PRD | `[架構]` |
| 2 | Pipeline Architecture | PIPELINE_ARCHITECTURE | `[架構]` |
| 3 | i18n System Design | i18n 相關文件合併 | `[架構]` |
| 4 | Architecture Decisions Log | 所有決策記錄合併 | `[決策]` |
| 5 | Deployment Runbooks | ios.md + android.md + railway.md | `[Runbook]` |
| 6 | Tier System — Complete Guide | TIER_INSTABILITY_DIAGNOSIS + TIER_FIX + TIER_STABILITY | `[DevOps]` |
| 7 | Symptom Index | SYMPTOM_INDEX | `[DevOps]` |
| 8 | IAP Flow — Incidents & Fixes | IAP 相關 incident reports 合併 | `[DevOps]` |
| 9 | V1.2.0 Implementation Plan | v1.2.0 相關文件 | `[規格]` |
| 10-20 | (其餘架構/操作文件) | ... | ... |

**總計：~35 sources（Research 15 + Project 20），遠在 100 上限內。**

---

## 5. 導入執行

### 5.1 Quick Win 路徑（< 30 分鐘）

如果專案很急，不想做完整盤點，先導入 **最高價值的 5 份文件**：

1. **技術 PRD / 架構文件**（最完整的那一份）→ Project notebook
2. **商業模型 / 產品策略**（如果有）→ Research notebook
3. **Symptom Index / Troubleshooting 索引**（如果有）→ Project notebook
4. **最新的 Runbook**（部署流程）→ Project notebook
5. **用戶研究摘要**（如果有）→ Research notebook

```bash
# Quick Win: 5 個 source 就能讓 NotebookLM 開始工作
python scripts/run.py add_source.py --file TECHNICAL_PRD.md \
  --notebook-id PROJECT_ID --category "架構" --title "Technical PRD"

python scripts/run.py add_source.py --file BUSINESS_MODEL_MASTER.md \
  --notebook-id RESEARCH_ID --category "策略" --title "Business Model"

# ... 重複 3 次
```

導入後立即測試：
```bash
python scripts/run.py ask_question.py --quiet \
  --question "What is the core architecture of this project?" \
  --notebook-id PROJECT_ID
```

### 5.2 完整導入路徑

1. **盤點**（15 min）— 執行文件掃描和分類
2. **過濾**（15 min）— 套用快速淘汰規則 + 三問判斷
3. **合併**（30 min）— 同主題文件合併為 consolidated sources
4. **導入**（20 min）— 用 `add_source.py` 逐一上傳，附 category prefix
5. **設定 Persona**（5 min）— 為兩個 notebook 設定適當的 guide
6. **驗證**（10 min）— 用 5 個代表性問題測試

### 5.3 Persona 建議

**Research Notebook Guide：**
```
你是這個專案的策略顧問。回答問題時：
1. 總是引用具體的用戶反饋或市場數據
2. 區分「已驗證的事實」和「假設」
3. 如果來源中有權重標記，按權重排序回答
4. 回答要簡潔但有根據
```

**Project Notebook Guide：**
```
你是這個專案的技術顧問。回答問題時：
1. 總是指出相關的架構組件和檔案路徑
2. 如果問題涉及 bug，先查看 [DevOps] 來源中的症狀索引
3. 區分「設計決策」和「實作細節」
4. 如果涉及部署，引用 [Runbook] 來源的具體步驟
```

---

## 6. 維護週期

### 6.1 觸發式更新（推薦）

| 事件 | 動作 |
|------|------|
| 完成重大功能/版本 | 更新 Project notebook 中的架構文件 |
| 解決重要 bug | 更新 Symptom Index source |
| 新的市場調研 | 加入 Research notebook |
| Runbook 流程改變 | 替換對應的 Runbook source |
| Source 超過 3 個月未更新 | 檢查是否仍然準確 |

### 6.2 不要做的事

| 觸發 | 不該做 | 該做 |
|------|--------|------|
| 每次 commit | 不要自動上傳 | 累積到版本里程碑再更新 |
| 每次 bug fix | 不要建立新 source | 更新 Symptom Index 那一份 |
| 文件刪除 | 不要也刪 NotebookLM source | 留著，除非知識已完全過期 |

---

## 7. 反模式（Anti-patterns）

| 反模式 | 為什麼有害 | 正確做法 |
|--------|-----------|---------|
| **把所有文件都丟進去** | 50 source 上限；過期數據污染回答 | 嚴格過濾，只留持久價值的 |
| **每個 bug 一份 source** | 快速消耗配額，大多過期 | 合併到 Symptom Index |
| **重複內容跨 notebook** | Gemini 可能從兩邊引用矛盾版本 | 每份知識只存在一處 |
| **用 NotebookLM 替代 git** | NotebookLM 不是版本控制 | git 管歷史，NotebookLM 管當前知識 |
| **導入後不維護** | 知識腐爛，回答越來越不準 | 隨專案演進更新 sources |
| **導入原始 log/dump** | Gemini 無法從無結構數據中提取意義 | 先整理為結構化文件再導入 |

---

## 8. 預期效益

導入後，你的專案獲得：

| 場景 | 沒有 NotebookLM | 有 NotebookLM |
|------|-----------------|---------------|
| 「這個 bug 之前遇過嗎？」 | 翻 git log + 600 個文件 | 一句查詢，有引用的答案 |
| 「我們為什麼選 Railway？」 | 找決策記錄 → 可能找不到 | 直接回答 + 引用決策文件 |
| 「競品怎麼處理 IAP？」 | 重新研究 | 引用現有研究，秒回 |
| 「部署到 iOS 的步驟？」 | 找 Runbook → 可能過期 | 引用 Runbook source |
| 新團隊成員 onboarding | 讀 654 個文件 | 問 NotebookLM 任何問題 |

**核心價值：把散落在 654 個文件中的知識，壓縮成可查詢、有引用、永遠在線的專案顧問。**

---

## 附錄：Category Prefix 完整表

| Prefix | Notebook | 用途 |
|--------|----------|------|
| `[策略]` | Research | 商業策略、產品方向 |
| `[用戶痛點]` | Research | 用戶研究、社區反饋 |
| `[競品分析]` | Research | 競品功能、評價、定價 |
| `[市場數據]` | Research | 市場規模、趨勢 |
| `[學術研究]` | Research | 論文、方法論 |
| `[架構]` | Project | 系統設計、技術 PRD |
| `[規格]` | Project | API spec、資料模型、版本計劃 |
| `[決策]` | Project | 架構決策、trade-off 分析 |
| `[Runbook]` | Project | 部署流程、操作手冊 |
| `[DevOps]` | Project | 症狀索引、跨版本 bug 模式 |
| `[LIVE]` | 任一 | 可能過期的外部文件（API docs 等） |
