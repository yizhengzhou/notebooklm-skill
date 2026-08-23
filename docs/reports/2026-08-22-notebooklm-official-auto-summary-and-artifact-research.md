# NotebookLM 官方行為研究：自動摘要、設定變更與 Studio Report

> 日期：2026-08-22  
> 方法：使用本專案的 NotebookLM Skill 執行一次官方網域 Deep Research，再人工檢查六份 Google 官方來源全文  
> 結果：研究 Notebook 已轉成專案正式的長期顧問，未刪除

## 為什麼重新研究

前三個 UX 實驗中，Foucault 案例在 Apply 過程建立了一份真的 Studio Report。我原先把它稱為「未經許可的 artifact mutation」。

使用者提醒我：NotebookLM 可能本來就會在設定或來源改變後重新產生摘要，這不一定是異常或越權。

這個提醒是正確的。我先前把「不是 skill 明確要求的動作」直接等同於「NotebookLM 未經許可」，定性太快。

## 我把問題拆成四個部分

1. 修改 Custom Chat／Persona／回覆長度，是否會建立 Studio Report？
2. 新增來源後，哪些摘要會自動產生或更新？
3. NotebookLM 官方是否本來就會自動建立 Studio artifacts？
4. Chat 是否能主動建立檔案或 Report？

## 官方文件真正說了什麼

### 1. NotebookLM 本來就有自動摘要

官方《Create a notebook in Gemini Notebook》說：

> Chat panel 會顯示根據全部來源產生的 summary。

官方《Add or discover new sources》也說：

> 每一份來源的 Source Guide 會提供整份來源的 auto-generated summary。

所以使用者在設定或來源改變後看到新的「總結」，很可能是 Chat panel summary 或 Source Guide summary。它們是 Notebook 的基本介面內容，不一定是一份 Studio Report。

### 2. 第一次加入來源時，官方確實可能自動建立 Report

官方《Create a notebook in Gemini Notebook》明確寫道：

> 為了幫助使用者開始，第一次把來源加入 Notebook 時，有時會自動建立 Report、flashcards、infographic、slide deck、audio 或 video overview。這些只建立一次，而且不計入使用額度。

因此，「沒有按下建立 Report，Studio 卻出現一份 Report」本身可能是官方設計，不足以證明產品越權或 library 出錯。

### 3. Custom Chat 設定的官方用途是調整回答

官方《Use chat in Gemini Notebook》把 Configure Chat 說明為：

- 選擇 Default、Learning Guide 或 Custom 對話風格；
- 指定角色或回答方式；
- 選擇 Default、Longer、Shorter 回覆長度。

官方資料沒有說「修改這些設定會建立 Studio Report」。

所以目前能說的是：

- 改設定會改變回答方式：官方明說；
- 改設定是否會重新產生 Chat panel summary：官方未明說；
- 改設定會建立 Studio Report：官方未說，這次也沒有重現。

### 4. Chat 官方上本來就能採取動作

官方《Use chat in Gemini Notebook》說，Google AI Pro／Ultra 桌面版使用者可在 Chat 使用 agentic capabilities，讓 Notebook 代表使用者：

- 搜尋網路；
- 執行程式碼；
- 建立可下載檔案；
- 建立圖表、圖片、PDF、Word、Excel、PowerPoint 等產物；
- 修改 artifact 版本。

同一份官方文件也提醒：

> 這些功能仍在早期實驗階段，需要使用者監督；Gemini Notebook 可能犯錯或做出意外行為，應再次確認。

Google Blog 甚至把 Artifact Creation 定義為模型能力之一：系統會判斷一個使用者問題是否值得產生 summary、study guide、FAQ 或 briefing document 等結構化產物。

這代表 Case 3 的 Report 也可能是 Chat 的官方 agentic behavior，而不是設定變更或第三方 library 的 bug。

## 這次額外實測了什麼

我建立一本新的官方行為研究 Notebook，逐步檢查 artifact list：

| 階段 | Studio artifact 數量 |
|---|---:|
| 建立 Notebook 並設定 Custom Persona | 0 |
| 加入第一份官方 Help seed | 0 |
| Deep Research 後加入三份官方來源並產生 Apply summary | 0 |
| 再加入兩份官方 Help 來源 | 0 |
| 詢問自動摘要與 Report 問題 | 0 |
| 轉成正式 Advisor 並再次設定 Persona | 0 |

本次沒有重現自動 Report。

這不能推翻官方的「第一次加入來源時有時會自動建立」，因為官方本來就用了 `sometimes`。它只能證明：

- 修改 Persona 不會在每次操作中必然建立 Report；
- 加入來源也不會每次都建立 Report；
- Artifact creation 是情境式或非固定發生，而不是穩定必現的副作用。

## 如何重新解讀 Case 3

較準確的描述應該是：

> Case 3 在 Apply 的 summary chat 期間出現一份不在 skill Apply Plan 中的 Studio Report。這份 Report 真實存在，但它可能屬於 NotebookLM 官方的首次來源自動產物或 Chat agentic artifact creation。現有官方文件與單次紀錄不足以確定實際觸發原因。

所以我撤回兩個過度結論：

1. 不能直接稱它為 NotebookLM「未經許可」的行為。
2. 不能直接認定是 `notebooklm-py` 或本 skill 額外建立。

但對本 skill 仍然有一個真實問題：

> Skill 的 Apply Plan 只顯示來源變更，沒有告訴使用者 NotebookLM 可能依官方產品能力產生 Studio artifact，也沒有把實際 artifact delta 放進結果。

這是「產品行為沒有被 skill 完整揭露」，而不是已證明的「Google 越權」。

## 專案建議如何修正

### 不應再預設全部封鎖

原建議是禁止 Apply summary 產生任何 artifact。現在應改成可選政策：

- `text_only`：如果官方 API 支援，禁止工具與 artifact；
- `observe`：允許官方正常行為，但記錄前後 artifact 差異；
- `approve`：若 Chat 建議建立 artifact，先讓使用者核准；
- `allow`：使用者明確允許 agentic artifact creation。

### 每次操作都應揭露結果

Ask／Apply 應回傳：

- 操作前有哪些 artifacts；
- 操作後新增了哪些；
- Report 的 ID、名稱、類型與建立時間；
- 若可取得，保存 custom prompt、thinking steps 或 action receipt；
- 來源是 `first-source-auto`、`chat-action`、`user-requested` 或 `unknown`。

### 不同風險應有不同處理

- 多一份非破壞性 Report：警告、記錄、讓使用者選擇保留或刪除。
- 多出來源、刪除來源或修改既有內容：停止並要求重新核准。
- 來源 retirement 前發生任何未解釋的破壞性變更：fail closed。

## 保留下來的專案大腦

本次 Notebook 已轉成正式資產：

- Advisor ID：`notebooklm-official-product-watch`
- Notebook：`NotebookLM Skill — Official Product Behavior Advisor`
- 用途：追蹤 NotebookLM／Gemini Notebook 官方產品行為，協助本專案修正 backend contract、使用指南與安全邊界。
- Owner：notebooklm-skill 專案維護者。
- 維護方式：手動 Preview、人工選源、官方 Help 核心來源 Pinned；在官方 Chat、Reports、Studio、來源同步或品牌／API 改變時 Refresh。
- 設定檔：`docs/advisors/notebooklm-official-product-watch.json`

## 主要官方來源

1. [Create a notebook in Gemini Notebook](https://support.google.com/gemininotebook/answer/16206563?hl=en)
2. [Use chat in Gemini Notebook](https://support.google.com/gemininotebook/answer/16179559?hl=en)
3. [Add or discover new sources for your notebook](https://support.google.com/gemininotebook/answer/16215270)
4. [Chat in NotebookLM: A powerful, goal-focused AI research partner](https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-custom-personas-engine-upgrade/)
5. [Do better research with NotebookLM](https://blog.google/innovation-and-ai/products/notebooklm/better-research-notebooklm/)

## Evidence

```text
~/.local/state/notebooklm-skill/ux-official-behavior-20260822/
├── evidence/
├── runs/
├── export-before-apply/
└── export-final/
```
