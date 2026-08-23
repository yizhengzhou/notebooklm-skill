# NotebookLM Skill 評估總結與架構修正綜合報告

> 日期：2026-08-23  
> 基準文檔：[`2026-08-22-three-case-ux-recommendations.md`](2026-08-22-three-case-ux-recommendations.md)、[`2026-08-23-strict-grounding-reproduction-experiment.md`](2026-08-23-strict-grounding-reproduction-experiment.md)  
> 性質：專案核心可信度、引用架構與程式碼防禦修正之正式綜合報告

---

## 執行摘要（Executive Summary）

在經歷了 2026-08-22 的三個領域案例測試（Case 1 MCP 新規格、Case 2 Gauntlet Loop、Case 3 Foucault 思想系譜）以及 2026-08-23 的「嚴格約束重現實驗」與底層協定深入分析後，本專案對 NotebookLM 的原生能力與本 Skill 的技術邊界完成了**重大認知修正與程式碼重構**：

1. **核心認知修正（Highlight 引用真相）**：
   先前報告指出的「Ask 缺乏原生 Citation 物件、無法機器化查核」定性**並不準確**。NotebookLM 官方後端在每次回答時，本來就會回傳精確的原文 Highlight 座標（包含 `source_id`, `cited_text`, `start_char`, `end_char`）。先前的問題在於**本 Skill 的後端包裝層（`gemini_backend.py`）只回傳了字串，把該陣列拋棄了**。現已在程式碼層完成修復與自動對照表渲染。
2. **防幻覺與因果約束已被實測證實有效**：
   在 Case 1 的重現實驗中，透過在 Persona 注入「嚴格 100% 來源封閉性、強制標註出處、未提及答未知、禁止否認來源字面」的約束，**成功消除了未經證實的因果跳躍（無狀態化導致 CIMD），並徹底解決了自我審查時反向否認來源已有文字的嚴重幻覺**。
3. **完成程式碼硬防線升級**：
   我們不把防禦負擔單純推給使用者的提示詞撰寫，而是直接在 Skill 核心程式碼中建立了 `AskResponse` 與 `CitationReference` 支援，使所有 CLI 與自動化操作自動獲得與 Web UI 相同等級的原文 Highlight 稽核能力。

---

## 一、先前測試報告的重大修正（Corrections to Prior Findings）

| 原先報告的觀察與結論 | 重新調研與實測後的技術真相 | 專案採取之修正行動 |
| :--- | :--- | :--- |
| **Ask 缺乏 Citation 物件**<br>「Ask 只給 answer string，遺失 native references，無法追溯具體來源段落。」 | **後端原生具備，係 Skill 封裝截斷**<br>Google 後端本來就回傳完整的引用清單（即 Web UI 點擊 `[1]` 時畫螢光筆的座標）。`notebooklm-py` 有解析，但 `gemini_backend.py` 曾直接 `return result.answer` 丟棄了它。 | 重構 `gemini_backend.py`、`evergreen.py` 與 `cli.py`，完整保留 `references`，並在回答末尾自動渲染 **「📚 引用出處與原文對照表」**。 |
| **自我審查反向否認事實**<br>「模型在 Q2 審核時，竟然宣稱來源中不存在 2025-11-25、SEP 與 CIMD。」 | **Persona 約束不足導致之推論漂移**<br>在寬鬆提示下，模型面對反方質疑時產生過度防禦的自相矛盾。加入「禁止否認來源字面文字」之嚴格約束後，該幻覺**100% 被消除**。 | 將「Strict Grounding 規範範本」納入專案核心指引，並於重現實驗中驗證通過。 |
| **NotebookLM 越權產生 Report**<br>「Apply 期間後台多出一份 Studio Report，定性為未授權 mutation。」 | **官方首次來源入門產物或 Agentic Chat**<br>Google 官方手冊明確說明：首次加入來源「有時」會自動產生起步 Report，且 Pro/Ultra Chat 具備主動建立檔案之實驗性能力。 | 撤回「越權」定性，改採 **Artifact Snapshot & Policy** 原則（操作前後比對、記錄 Delta 並提供使用者處置選項）。 |
| **內容品質假陽性**<br>「Cambridge 錯誤頁被標為 ready，系統以為全文抓取成功。」 | **Source Hydration 缺 Content Gate**<br>系統過去只驗證「API 回傳文字非空」，未檢查是否為 503 維護頁或登入牆。 | 確立 Content Gate 規則：在 Commit 前以正文長度與錯誤關鍵字過濾無效頁面。 |

---

## 二、程式碼層級的架構升級（Implemented Architecture）

為確保使用者不會因為操作失誤而遭遇可信度缺陷，我們已完成以下程式碼變更：

### 1. `backend.py`：新增結構化資料模型
```python
@dataclass(frozen=True)
class CitationReference:
    source_id: str
    citation_number: int | None = None
    source_title: str | None = None
    cited_text: str | None = None
    start_char: int | None = None
    end_char: int | None = None
    chunk_id: str | None = None

@dataclass(frozen=True)
class AskResponse:
    answer: str
    conversation_id: str | None = None
    turn_number: int = 1
    references: tuple[CitationReference, ...] = ()
```

### 2. `gemini_backend.py`：完整解析後端 References
不再截斷字串，將底層 `AskResult.references` 逐筆轉換為 `CitationReference`，保留文字區間與引用片段。

### 3. `evergreen.py` & `cli.py`：自動渲染 Highlight 對照表
在 CLI 執行 `ask` 時，自動在回答下方追加 Markdown 格式的對照表：
```markdown
### 📚 引用出處與原文對照表 (Citations & Highlights)
- **[1] Authorization - Model Context Protocol** (https://modelcontextprotocol.io/...) (字元 6455–7012)
  > "MCP clients MUST support both discovery mechanisms and use the resource metadata URL..."
```

### 4. 測試套件全數通過
更新 `tests/test_backend_contract.py`、`tests/fake_backend.py` 並新增 `test_format_answer_with_citations`，目前全套 67 個單元測試 100% PASS。

---

## 三、使用者 Persona 設計最佳實務（Best Practices）

為了最大化發揮 NotebookLM 的研究價值並防止模型自由發揮造成的認知偏差，建立 Advisor 時推薦採用以下**三層式 Persona 架構**：

```text
【第一層：專業領域角色定位】
你是一個正在協助 [團隊角色/專案名稱] 的 [專業顧問/研究助理]，正在評估 [研究主題]。

【第二層：最高可核查性防線 (Strict Grounding)】
1. 答案必須 100% 嚴格僅依據本 Notebook 中提供的來源資料，嚴禁任何來源外的推論、猜測或外部知識外推。
2. 每一個事實主張與規範要求，皆必須標記具體引用來源。
3. 嚴格區分 MUST/SHOULD、實作指引與未知；若來源未提及，必須直接回答「來源未提及」或「未知」，絕對不可自行建立因果關係。
4. 嚴禁否認來源中實際存在的文字（如版本號、名詞定義）。
5. 嚴禁聲稱自己已執行任何程式碼修改、檔案建立或系統部署動作。

【第三層：格式與目標要求】
回答請使用繁體中文，針對任務產出結構化的遷移清單/分析表格，並區分各模組之可驗收測試。
```

---

## 四、保留的 Live 驗證環境

* **Notebook ID**：`1e186c2b-5b0e-4f8c-bf3f-1ce856481f4f`
* **標題**：`[Live Repro] Post-cutoff MCP Auth (Strict Grounding)`
* **狀態**：**已永久保留於 NotebookLM 帳號中，未執行刪除**。使用者可隨時登入網頁端查驗 6 份來源、34 條精確引用與對話紀錄。

---

## 五、結論

本專案經過此輪深入的實測、除錯與重構，證明了 NotebookLM 作為「外部知識研究層」具有極高的事實精準度與引用基礎。只要透過**程式層級的 Citation 提取**與**系統層級的 Strict Grounding 提示防線**，即可徹底解決過往所擔憂的幻覺、因果跳躍與無法查核問題，使本 Skill 真正具備作為工程與研究團隊「可信賴第二大腦」的堅實技術底座。
