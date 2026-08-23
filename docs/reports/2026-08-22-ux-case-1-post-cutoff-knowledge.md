# UX Case 1：用 NotebookLM 補足 LLM 截止日期後的 MCP 授權知識

> 測試日期：2026-08-22  
> 角色：維護 AI coding agent 的平台工程團隊成員  
> 狀態：完成 live field trial；Notebook 已在 export 後刪除  
> 研究重點：流程與 UX，不以回答內容證明產品價值

## 我為什麼啟動這次研究

我接手一個 2024 年完成的 TypeScript MCP client。它把 authorization endpoint 寫死在設定檔，而我使用的通用 LLM 未必知道 2025–2026 年 MCP Authorization 規格的變化。

我不是要把整個專案存進 NotebookLM，也不是要它替我改 code。我希望它在開發過程中扮演「外部新知研究層」：找出截止日期後的官方規格、讓我審查來源，再把變化轉成 migration checklist。

我一開始的假設是：舊 client 仍可直接連到預先設定的 OAuth authorization endpoint。我的 Watch Item 就用來持續挑戰這個假設。

## 我實際走過的完整流程

### 1. 我先把開發問題改寫成 Advisor Profile

我建立 `ux-post-cutoff-mcp`，要求回答必須：

- 標出日期與規格版本；
- 區分 MUST、SHOULD、推論、衝突與未知；
- 不聲稱已修改 repo 或完成部署；
- 研究 2025-03-26、2025-06-18、2025-11-25 與目前版本間的差異。

我把官方 MCP 與 GitHub 設成 preferred domains，來源上限設為 5。這一步迫使我在研究前說清楚「要更新什麼」，比直接問「MCP 最近有何變化」有效。

困難是設定必須手寫 JSON。`research.brief`、`queries`、Persona 與 Watchlist 很容易重複，CLI 沒有 scaffold、範例選單或 schema validation preview。

### 2. 我建立 Notebook，並固定一份 canonical seed

`setup` 約 8 秒完成，Persona read-back 成功。我接著把 2025-06-18 Authorization 規格加入並標為 Pinned，約 12 秒完成。

Pinned 對我很重要：我知道後續 Deep Research 不會把這份基準來源靜默替換或刪除。

### 3. 我執行 Deep Research Preview

Preview 花了 356 秒。等待期間 CLI 沒有候選數、目前階段或進度，只能看到命令仍在執行。

結果共有 69 個候選：

- 5 個 `propose_add`；
- 1 個 `already_present`；
- 63 個 `over_budget`；
- Preview 前後 source IDs 相同，證明沒有偷偷匯入來源。

preferred domains 在這個案例很有效，前幾名幾乎都是官方規格。不過我仍從 `over_budget` pool 選了 RFC 9728，說明「系統排名」不能代替人工核准。

### 4. 我人工選擇五份來源

我最後選入：

1. 2025-03-26 Authorization；
2. 2025-11-25 Authorization；
3. 2026-07-28 changelog；
4. 2026-07-28 Authorization Server Discovery；
5. RFC 9728。

我刻意用版本前後對照，而不是只收最新文件。這讓 Notebook 有機會回答「舊做法如何遷移」，而不只是重述目前狀態。

困難是 `preview.md` 只顯示前五個 proposed additions。若要從 69 個候選中選 over-budget source，我必須自己讀大型 `preview.json`、複製 URL，再建立 `selected-urls.json`。這對一般開發者不友善。

### 5. 我建立並核准 Apply Plan

`plan-apply` 幾乎立即完成。Plan 清楚列出：

- 1 個 protected source；
- 5 個 additions；
- 0 個 retirements；
- 精確 SHA-256 digest。

我審查後以該 digest 執行 Apply。Apply 花了 113 秒，最後六份來源均 ready，Pinned source 保持不變，沒有刪除。

這個 review boundary 是 skill 最清楚的價值：研究結果與來源匯入不是同一動作。

### 6. 我把研究轉成 sprint 工作

第一次 Ask 花了 81 秒。我要求它把「寫死 authorization endpoint 的 2024 TypeScript client」轉成 migration checklist，並為每項列出版本、規範強度、元件和 acceptance test。

回答確實產生了工程師可討論的工作分解，例如 discovery、PKCE、resource indicators、issuer binding 與測試情境。它也混入 2026 transport／stateless 變更，使 Authorization migration 的 scope 膨脹。

### 7. 我要求它自我稽核

第二次 Ask 花了 54 秒。我要求它檢查前一輪的超量推論，尤其是「無狀態化導致 CIMD 取代 DCR」。

這次回答承認該因果關係沒有直接證據，這是好的；但它又宣稱目前來源中不存在日期、SEP 與 CIMD。Export 後我在 2025-11-25 source fulltext 直接找到 `Version 2025-11-25` 與 `Client ID Metadata Documents`。也就是說，它的 self-audit 本身仍可與來源矛盾。

這是我在本案遇到的最大信任問題：**Ask 只給 answer string，沒有原生 citation objects；我無法從 `[1]` 直接跳到 source ID、段落或原文。**

### 8. 我匯出並清理

Export 花了 6 秒，六份來源全文均成功匯出，沒有 unavailable source。完整流程約 10 分 31 秒，不含我閱讀與選源的人工時間。

Evidence 保存後，我刪除 disposable Notebook，並確認它不再存在。

## 我在真實開發中會怎麼用

如果這是實際 sprint，我會這樣安排：

1. 開工前把目前依賴的舊規格設成 Pinned seed。
2. 用 Research Profile 限定版本、日期與 migration decision。
3. Preview 後只選官方規格、RFC 與少量實作證據。
4. 要求 Notebook 產出 candidate checklist，而不是直接產生 code。
5. 逐項回到 source fulltext 驗證 MUST／SHOULD。
6. 經人工確認後才在 issue tracker 建立 migration tasks。
7. 規格發布新版時，用同一 Watch Item 再跑更新，而不是建立另一本 Notebook。

## 對我有效的部分

- Pinned seed 讓版本比較有穩定基準。
- Preview 不修改來源，降低研究誤匯入風險。
- preferred domains 在官方規格型問題上很有效。
- selection 可從完整 candidate pool 挑選，不被前五名綁住。
- Apply digest 把「研究」與「核准」分開。
- Export fulltext 讓我能在 NotebookLM 之外做最後查證。

## 阻礙我的部分

1. Preview 約六分鐘沒有進度回饋。
2. 69 個候選只能靠讀 JSON 審查。
3. 排名沒有「版本差異覆蓋」或「primary/secondary」標記。
4. Apply 的 delta summary 與後續 Ask 共用同一 conversation，前一輪推論會污染後續回答。
5. Ask 不保存 conversation ID、turn、citation/reference objects 或使用到的 source IDs。
6. Self-audit 仍可能否認來源中明確存在的文字。
7. Skill 不會把 checklist 接到 repo／issue tracker；我必須手動搬運，這符合安全邊界，但 UX 上缺少可驗證 handoff。

## 我的結論

這個 skill 能有效建立「截止日期後新知 → 人工選源 → migration candidate」的研究管線；它最有價值的不是答案比較新，而是讓新來源進入專案決策前有 review boundary 與可匯出的 provenance。

我不會直接照 Ask 的 checklist 改 production code。只要 citation fidelity、fresh conversation 與 claim-to-source audit 尚未完成，我會把答案視為待驗證的研究草案，而不是規格事實。

## Evidence

```text
~/.local/state/notebooklm-skill/ux-three-cases-20260822/
├── configs/case-1-post-cutoff.json
├── runs/case-1-preview/
├── runs/case-1-apply/
├── evidence/case-1-*.json
└── exports/case-1/
```
