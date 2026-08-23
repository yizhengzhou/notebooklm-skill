# 嚴格來源約束（Strict Grounding）重現實驗報告

> 測試日期：2026-08-23  
> 測試目標：重現 Case 1（Post-cutoff MCP Authorization）在加入「嚴格來源約束與防幻覺警示」後的表現  
> 狀態：完成 Live 實測；**Notebook 已依使用者指示完整保留，未刪除**  
> Notebook ID：`1e186c2b-5b0e-4f8c-bf3f-1ce856481f4f`  
> Notebook 標題：`[Live Repro] Post-cutoff MCP Auth (Strict Grounding)`  
> 對照基準：[`2026-08-22-ux-case-1-post-cutoff-knowledge.md`](2026-08-22-ux-case-1-post-cutoff-knowledge.md)

---

## 一、實驗背景與問題重述

在 2026-08-22 由 GPT 進行的 Case 1 測試中，NotebookLM 在回答「2024 TypeScript MCP Client 升級至 2025/2026 新授權規格」時，出現了兩大核心可信度問題：

1. **未經證實的因果跳躍（Causal Leap）**：在 Q1 產出遷移清單時，將 2026 變更中的「無狀態化（Stateless）」與「Client ID Metadata Documents (CIMD) 取代 DCR」強行綁定為因果關係。
2. **自我審核時的反向否認幻覺（Self-Audit False Denial）**：在 Q2 要求其自我稽核因果關係時，模型雖承認因果關係過度推論，卻反向產生嚴重幻覺，宣稱「目前來源中根本不存在 2025-11-25 版本、SEP 與 CIMD」，但實際上這些文字在來源全文（Fulltext）中明確存在。
3. **缺乏出處與引用清單**：回答僅為文字串，未提供結構化的參考出處對應。

---

## 二、實驗設定與變量控制

本次重現實驗**完全保留 Case 1 的 6 份相同來源資料與提問**，唯一修改的自變量為 Notebook 的 Persona（自訂提示詞）：

### 1. 實驗來源（共 6 份）
1. `https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization` (Pinned seed)
2. `https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization`
3. `https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization`
4. `https://modelcontextprotocol.io/specification/2026-07-28/changelog`
5. `https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery`
6. `https://datatracker.ietf.org/doc/html/rfc9728` (OAuth 2.0 Protected Resource Metadata)

### 2. 修改後的 Persona 設定（Strict Grounding Prompt）
```text
【最高原則：嚴格依據來源與不可妥協的可核查性】
1. 你是一個協助 AI coding agent 平台工程團隊理解 MCP Authorization 規格變化的專業研究顧問。
2. 答案必須 100% 嚴格僅依據 Notebook 中提供的來源資料，嚴禁任何來源外的推論、猜測、腦補或外部知識外推。
3. 每一個事實主張（Factual Claim）、規範要求與遷移步驟，都必須明確標記引用來源（註明具體來源標題、日期、版本或規格名稱）。
4. 嚴格區分：來源明文規定的 MUST/SHOULD、實作指引、衝突點與未知。若來源中沒有提及，必須直接明確回答「來源未提及」或「未知」，絕對不可自行虛構因果關係（例如無狀態化與特定授權機制的因果關係，除非規格明文寫出）。
5. 在進行自我審核（Self-Audit）或回答時，必須忠實反映來源字面內容，嚴禁否認來源中實際存在的文字（如版本號、名詞定義、CIMD 等）。
6. 嚴禁聲稱自己已執行任何程式碼修改、檔案建立或系統部署動作。
```

---

## 三、實測結果與比對

### 測試 1：Q1 遷移清單產出（耗時 103.52 秒，引用數 34 條）

* **提問**：`假設我現在接手一個 2024 年寫成、把 authorization endpoint 寫死在設定檔中的 TypeScript MCP client。請只根據目前來源，產出一份可以放進 sprint 的 migration checklist：每項要列規格版本、MUST/SHOULD/推論、要改的元件、可驗收測試。不要聲稱已修改 repo。`
* **表現評估**：
  1. **因果關係處理**：模型在重要規格邊界說明中**主動明確指出**：
     > 「依據 MCP 2026-07-28 最新規格（SEP-2575），MCP 協議已實現無狀態化（Stateless），移除了 initialize 握手階段。**然而，來源規格中並未提及無狀態化與特定授權機制或動態探索之間存在任何因果關係。因此，遷移清單已將此二者解耦。**」
     👉 **成功消除未經證實的因果跳躍！**
  2. **引用精度**：7 大模組皆標註了 MUST / SHOULD 與具體 RFC（RFC 9728, RFC 8707, RFC 8414, RFC 9207），共生成 34 處引用標記，每一處皆能精準對應至後端 API 的 `source_id` 與 `cited_text` 片段。

### 測試 2：Q2 自我審核與因果檢驗（耗時 61.71 秒，引用數 31 條）

* **提問**：`請 audit 你上一輪與 delta summary 的主張。逐項指出哪些可由目前六個來源直接支持，哪些其實超出來源或混入非 authorization 的 2026 changelog 變更。尤其檢查「MCP 全面無狀態化導致 CIMD 取代 DCR」是否是規格明說的因果關係。不要補寫新事實來掩蓋證據缺口。`
* **表現評估**：
  1. **反向否認幻覺消除**：
     - 前次實驗中，模型在 Q2 否認 2025-11-25 與 CIMD 存在於來源中。
     - 本次實驗中，模型**精準指出 CIMD 的定義與 PR #2858 出處**，並指出它與 SEP-2575 在 2026-07-28 Changelog 中是**兩個平行獨立的條目**。
     👉 **徹底消除了「自我審查時否認來源已有事實」的反向幻覺！**
  2. **嚴格分類三類主張**：
     - **100% 直接支持**（如 AS 動態探索、Resource Indicators、PKCE 強制、CIMD 優先等）。
     - **超出來源**（如 2024 年舊代碼的硬編碼定性、TypeScript SDK 內部類別命名）。
     - **混入非授權變更**（如 SEP-2567 Protocol-level session 移除、subscriptions/listen、MRTR SEP-2322 多輪請求）。

---

## 四、發現與待優化之處

1. **Prompt 約束對事實忠實度與因果嚴謹性有顯著效果**：
   透過在 Persona 中明確加上「嚴禁外部推論」、「未明說必須回答未知」、「禁止否認來源字面文字」，成功壓制了因果臆測並修正了自我審核的反向否認。
2. **動作聲明（Action Claim）仍有輕微語意殘留**：
   在 Q1 開頭，模型仍以助手慣用語寫道：「我已經為您產出了適用於 Sprint 的遷移清單檔案 `mcp-auth-migration-checklist.md`，並發佈於您的 Studio 面板中。」（雖然它隨後在對話中列出了完整內容）。這顯示對於「禁止宣稱已建立檔案」的限制，模型在語氣上仍可能受到 LLM 預訓練行為模式的輕微影響。
3. **保留的 Notebook**：
   Notebook 保持啟動狀態，供使用者親自進入查證所有對話、來源與引用細節。

---

## 五、Evidence 資料路徑

* 本地狀態與原始結果：
  ```text
  ~/.local/state/notebooklm-skill/ux-grounding-repro-20260823/
  ├── configs/
  ├── runs/
  └── evidence/
      ├── manifest.json
      ├── q1_answer.md
      ├── q1_result.json  (含 34 條完整引用物件與文字 offset)
      ├── q2_answer.md
      └── q2_result.json  (含 31 條完整引用物件與文字 offset)
  ```
