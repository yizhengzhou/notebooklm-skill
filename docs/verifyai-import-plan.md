# VerifyAI → NotebookLM Import Execution Plan

> **專案:** VerifyAI (image-fact-checker)
> **來源:** 620 .md files → 48 surviving → consolidated to ~27 sources
> **目標:** Research notebook (~6 sources) + Project notebook (~21 sources)
> **產生日期:** 2026-03-27

> **注意:** 這是針對 VerifyAI 這個專案產生的一次性執行紀錄，不是通用 onboarding
> 文件——合併清單、來源路徑都是 VerifyAI 專屬的。通用流程請見
> [`onboarding-existing-projects.md`](onboarding-existing-projects.md)。
> 下方 Phase 1 的 `cd` 路徑是作者本機的絕對路徑，換一台機器或換一個專案執行都會
> 失敗；不要直接照抄，改用下面「安裝路徑」小節的作法。

---

## 安裝路徑（repo-scoped，不要硬寫絕對路徑）

在你自己的專案根目錄建立一個指向 notebooklm-skill 實際安裝位置的 symlink，之後
所有指令都透過這個 symlink 執行，不需要知道、也不需要依賴作者本機的路徑：

```bash
# 在你的專案根目錄執行，NOTEBOOKLM_SKILL_PATH 換成你機器上實際 clone 的位置
ln -s "$NOTEBOOKLM_SKILL_PATH" .notebooklm-skill
cd .notebooklm-skill
.venv/bin/python scripts/run.py create_notebook.py --name "YourProject" --pair --tone default --show-browser
```

下方 Phase 1 的 `cd /Volumes/...` 僅為原始執行紀錄，保留作參考，不是可攜的安裝
步驟。

---

## 概覽

```
620 .md files
  │ 快速淘汰 (時間快照、session log、test evidence、archived)
  ▼
48 surviving files
  │ 合併同主題文件
  ▼
~27 sources (6 Research + 21 Project)
  │ 上傳到 NotebookLM
  ▼
2 notebooks ready for queries
```

---

## Phase 1: 建立 Notebook Pair

```bash
cd /Volumes/NEWXYZ/macOS_data_mirror/Project/notebooklm-skill
.venv/bin/python scripts/run.py create_notebook.py --name "VerifyAI" --pair --tone default --show-browser
```

記下輸出的 Research ID 和 Project ID。

---

## Phase 2: Research Notebook Sources（6 sources）

### Source R1: `[策略] Business Model & Pricing`
| 合併來源 | 路徑 |
|----------|------|
| BUSINESS_MODEL_MASTER | `docs/business/BUSINESS_MODEL_MASTER.md` |
| COST_BENCHMARK | `docs/business/COST_BENCHMARK.md` |
| PRODUCT_CONFIGURATION_AUDIT | `docs/business/PRODUCT_CONFIGURATION_AUDIT_FINAL.md` |

**合併理由:** 三份都是定價/成本/商業模型，緊密相關

### Source R2: `[市場數據] Marketing & ASO Strategy`
| 合併來源 | 路徑 |
|----------|------|
| app-marketing-context | `docs/strategy/app-marketing-context.md` |
| MARKETING_PLAN | `docs/strategy/MARKETING_PLAN.md` |
| APP_STORE_LISTING | `docs/strategy/APP_STORE_LISTING.md` |
| app-store-descriptions | `docs/app-store-descriptions.md` |

**合併理由:** 市場定位、行銷策略、ASO 都是同一個「怎麼賣」的主題

### Source R3: `[策略] Feature Roadmaps — Face Search, Image Search, Deepfake`
| 合併來源 | 路徑 |
|----------|------|
| CHINA_AIDETECTION_DEEPFAKE_ROADMAP | `docs/strategy/CHINA_AIDETECTION_DEEPFAKE_ROADMAP.md` |
| IMAGE_SEARCH_STRATEGY | `docs/strategy/IMAGE_SEARCH_STRATEGY.md` |
| FACE_SEARCH_PIVOT_RESEARCH_REPORT | `docs/strategy/FACE_SEARCH_PIVOT_RESEARCH_REPORT.md` |

**合併理由:** 三份都是功能方向研究，回答「下一步做什麼」

### Source R4: `[策略] Open Source Strategy — IntelOwl`
| 來源 | 路徑 |
|------|------|
| ★ 獨立 | `docs/strategy/INTELOWL_CONTRIBUTION_STRATEGY.md` |

**不合併理由:** 獨立主題，與其他策略文件無重疊

---

**Research Notebook 總計：4 sources**（遠低於 25 上限，保留大量空間給未來研究）

---

## Phase 3: Project Notebook Sources（21 sources）

### 合併組（11 merged sources from 27 files）

#### Source P1: `[架構] Core Architecture — PRD & Pipeline`
| 合併來源 | 路徑 |
|----------|------|
| TECHNICAL_PRD | `docs/technical/TECHNICAL_PRD.md` |
| PIPELINE_ARCHITECTURE | `docs/technical/PIPELINE_ARCHITECTURE.md` |
| PIPELINE_TRANSPARENCY_AND_DECISION_TREE | `docs/technical/PIPELINE_TRANSPARENCY_AND_DECISION_TREE.md` |

**合併理由:** 三份共同描述系統核心架構

#### Source P2: `[架構] Backend Unification & Deployment`
| 合併來源 | 路徑 |
|----------|------|
| BACKEND_UNIFICATION_PLAN | `BACKEND_UNIFICATION_PLAN.md` |
| BACKEND_DEPLOYMENT_ARCHITECT_REVIEW | `BACKEND_DEPLOYMENT_ARCHITECT_REVIEW.md` |
| BACKEND_MERGE_NEXT_STEPS | `BACKEND_MERGE_NEXT_STEPS.md` |
| PHASE_1_2_COMPLETION_REPORT | `PHASE_1_2_COMPLETION_REPORT.md` |

**合併理由:** 後端統一的完整故事：計劃 → 審查 → 執行 → 完成

#### Source P3: `[架構] Android Porting — Status & Roadmap`
| 合併來源 | 路徑 |
|----------|------|
| ANDROID_PORTING_TAKEOVER | `ANDROID_PORTING_TAKEOVER.md` |
| ANDROID_PROJECT_STATUS | `ANDROID_PROJECT_STATUS.md` |
| ANDROID_STABLE_V1_ROADMAP | `ANDROID_STABLE_V1_ROADMAP.md` |
| agent_task_android_ios_comparison | `agent_task_android_ios_comparison.md` |

**合併理由:** Android 移植的完整上下文

#### Source P4: `[DevOps] Tier System — Diagnosis & Fixes`
| 合併來源 | 路徑 |
|----------|------|
| TIER_INSTABILITY_DIAGNOSIS | `TIER_INSTABILITY_DIAGNOSIS.md` |
| TIER_STABILITY_FIX_SUMMARY | `TIER_STABILITY_FIX_SUMMARY.md` |

**合併理由:** 同一問題的診斷+修復，不可分割

#### Source P5: `[規格] v1.2.0 — Implementation Plan & Spec`
| 合併來源 | 路徑 |
|----------|------|
| v1.2.0-implementation-plan | `v1.2.0-implementation-plan.md` |
| v1.2.0-engineer-prompt | `v1.2.0-engineer-prompt.md` |

**合併理由:** 同一版本的計劃和工程規格

#### Source P6: `[Runbook] Railway & Celery Worker Deployment`
| 合併來源 | 路徑 |
|----------|------|
| RAILWAY_WORKER_DEPLOYMENT_GUIDE | `RAILWAY_WORKER_DEPLOYMENT_GUIDE.md` |
| RAILWAY_CELERY_WORKER_SETUP_PROMPT | `RAILWAY_CELERY_WORKER_SETUP_PROMPT.md` |

**合併理由:** 同一部署流程的兩個面向

#### Source P7: `[DevOps] Pixel 7 — Diagnostic & Issues`
| 合併來源 | 路徑 |
|----------|------|
| PIXEL7_DIAGNOSTIC_GUIDE | `PIXEL7_DIAGNOSTIC_GUIDE.md` |
| PIXEL7_ISSUES_REPORT | `PIXEL7_ISSUES_REPORT.md` |

**合併理由:** 同一設備的診斷指南和問題清單

#### Source P8: `[架構] i18n System — Design & Usage`
| 合併來源 | 路徑 |
|----------|------|
| I18N_AUTO_TRANSLATION_PROPOSAL | `docs/technical/I18N_AUTO_TRANSLATION_PROPOSAL.md` |
| FRONTEND_I18N_USAGE_GUIDE | `docs/guidelines/FRONTEND_I18N_USAGE_GUIDE.md` |

**合併理由:** i18n 的設計決策和使用指南

#### Source P9: `[規格] Share Feature — Plan & Implementation`
| 合併來源 | 路徑 |
|----------|------|
| SHARE_NARRATIVE_FEATURE_PLAN | `docs/strategy/SHARE_NARRATIVE_FEATURE_PLAN.md` |
| SHARE_RESULTS_FEATURE_PLAN | `docs/strategy/SHARE_RESULTS_FEATURE_PLAN.md` |

**合併理由:** 同一功能的兩個規劃文件

#### Source P10: `[Runbook] EAS Build & OTA Updates`
| 合併來源 | 路徑 |
|----------|------|
| EAS_UPDATE_CHANNEL_SETUP | `docs/runbooks/EAS_UPDATE_CHANNEL_SETUP.md` |
| EAS_CONFIGURATION | `docs/EAS_CONFIGURATION.md` |

**合併理由:** EAS 設定和 OTA 更新是同一主題

#### Source P11: `[決策] Build Issues & Race Conditions`
| 合併來源 | 路徑 |
|----------|------|
| BUILD_66_ISSUES_ANALYSIS | `BUILD_66_ISSUES_ANALYSIS.md` |
| EXPO_GO_LISTENER_FIX | `EXPO_GO_LISTENER_FIX.md` |

**合併理由:** 都是 build 階段發現的技術問題分析和決策

### 獨立 Sources（10 standalone files）

| # | Source 名稱 | 路徑 | Category |
|---|-----------|------|----------|
| P12 | `[DevOps] Symptom Index` | `docs/troubleshooting/SYMPTOM_INDEX.md` | E |
| P13 | `[架構] CLAUDE.md — Project Rules` | `CLAUDE.md` | B |
| P14 | `[Runbook] Testing Quickstart` | `TESTING_QUICKSTART.md` | D |
| P15 | `[規格] Next Version Plan (v2.1.0)` | `docs/strategy/NEXT_VERSION_PLAN.md` | B |
| P16 | `[DevOps] Expo New Architecture Crash Workaround` | `docs/technical/EXPO_NEW_ARCHITECTURE_CRASH_WORKAROUND.md` | E |
| P17 | `[DevOps] Apple Sandbox IAP Currency Research` | `docs/technical/apple-sandbox-iap-currency-research.md` | E |
| P18 | `[決策] User Messaging Guidelines` | `docs/guidelines/USER_MESSAGING_GUIDELINES.md` | C |
| P19 | `[決策] Core Logic Protection Standard` | `docs/strategy/CORE_LOGIC_PROTECTION_STANDARD.md` | C |
| P20 | `[Runbook] Document Management System` | `docs/strategy/DOCUMENT_MANAGEMENT_SYSTEM.md` | D |
| P21 | `[DevOps] UptimeRobot 405 Fix` | `docs/runbooks/UPTIMEROBOT_405_FIX.md` | E |

---

**Project Notebook 總計：21 sources**（低於 30 上限，保留空間給未來版本）

---

## Phase 4: Source 合併模板

合併文件時使用此模板：

```markdown
# [Category] Title — Subtitle

> 合併自：file1.md, file2.md, file3.md
> 最後更新：2026-03-27
> 原始專案：VerifyAI (image-fact-checker)

---

## [Section from file 1]
[保留完整內容，不摘要]

---

## [Section from file 2]
[保留完整內容，不摘要]

---

*本 source 由 NotebookLM onboarding 流程合併生成。原始文件保留在 git 中。*
```

**關鍵原則：合併 = 串接，不是摘要。** 保留原始內容讓 Gemini 能精確引用。

---

## Phase 5: 執行順序（高價值優先）

### 第一波：核心架構（立即可查詢）
```bash
# 變數設定
RESEARCH_ID="<research-notebook-id>"
PROJECT_ID="<project-notebook-id>"
VF="/Volumes/NEWXYZ/macOS_data_mirror/Project/image-fact-checker"
RUN=".venv/bin/python scripts/run.py add_source.py"

# P1: Core Architecture (最高價值)
$RUN --file "$VF/docs/technical/TECHNICAL_PRD.md" \
     --notebook-id $PROJECT_ID --title "[架構] Core Architecture — PRD & Pipeline"

# P12: Symptom Index (查詢最頻繁)
$RUN --file "$VF/docs/troubleshooting/SYMPTOM_INDEX.md" \
     --notebook-id $PROJECT_ID --title "[DevOps] Symptom Index"

# R1: Business Model (Research 核心)
$RUN --file "$VF/docs/business/BUSINESS_MODEL_MASTER.md" \
     --notebook-id $RESEARCH_ID --title "[策略] Business Model & Pricing"
```

### 第二波：架構決策
P2 (Backend), P3 (Android), P4 (Tier), P5 (v1.2.0)

### 第三波：運維手冊
P6 (Railway), P7 (Pixel7), P10 (EAS), P14 (Testing)

### 第四波：其餘文件
所有剩餘的 standalone sources 和 Research sources

---

## Phase 6: Persona 設定

已由 `create_pair --tone default` 自動設定。如需自訂：

**Research Notebook Guide：**
```
你是 VerifyAI 的策略顧問。回答問題時：
1. 總是引用具體的用戶反饋或市場數據
2. 區分「已驗證的事實」和「假設」
3. 回答要簡潔但有根據
4. 如果被問到產品方向，綜合 Feature Roadmap 和 Business Model 的資訊
```

**Project Notebook Guide：**
```
你是 VerifyAI 的技術顧問。回答問題時：
1. 總是指出相關的架構組件和檔案路徑
2. 如果問題涉及 bug，先查看 Symptom Index
3. 區分「設計決策」和「實作細節」
4. 如果涉及部署，引用 Runbook 的具體步驟
5. 對於 Tier 系統問題，優先引用 Tier System source
```

---

## Phase 7: 驗證查詢

導入完成後，用以下問題測試兩個 notebook：

### Research Notebook 驗證
| # | 查詢 | 預期引用的 Source |
|---|------|-----------------|
| 1 | "VerifyAI 的定價策略是什麼？" | R1 (Business Model) |
| 2 | "Face search 的可行性如何？" | R3 (Feature Roadmaps) |
| 3 | "主要競品有哪些？我們的差異化在哪？" | R2 (Marketing & ASO) |
| 4 | "IntelOwl 貢獻策略是什麼？" | R4 (IntelOwl) |

### Project Notebook 驗證
| # | 查詢 | 預期引用的 Source |
|---|------|-----------------|
| 1 | "分析 pipeline 的完整流程是什麼？" | P1 (Core Architecture) |
| 2 | "Tier 系統之前遇過什麼問題？怎麼解決的？" | P4 (Tier System) |
| 3 | "怎麼部署 Railway Celery Worker？" | P6 (Railway Deployment) |
| 4 | "Android 移植的進度和剩餘工作？" | P3 (Android Porting) |
| 5 | "v1.2.0 做了什麼改動？" | P5 (v1.2.0 Spec) |

---

## Phase 8: 合併失敗的 Fallback

如果合併後的 source 超過 500,000 字限制：
1. **拆分**該 source 為兩個獨立 source
2. 用同樣的 category prefix 但加上 `(Part 1/2)` 後綴
3. 確保兩個 notebook 的 source 總數仍在 50 以內

如果 `add_source.py` 上傳失敗：
1. 改用手動上傳（複製文字內容到 NotebookLM 的「貼上文字」功能）
2. 確保 source 名稱一致
3. 失敗的文件記錄下來，不要跳過

---

## 附錄 A: 完整文件清單（48 files → 25 sources）

### 已分配文件（48/48 = 100%）

**Research Notebook — 4 sources from 11 files:**
- R1: 3 files (business model, cost, product config)
- R2: 4 files (marketing, ASO, app store)
- R3: 3 files (face search, image search, deepfake)
- R4: 1 file (IntelOwl)

**Project Notebook — 21 sources from 37 files:**
- Merged: 11 sources from 27 files
- Standalone: 10 sources from 10 files

### 容量使用率
| Notebook | Sources | 上限 | 使用率 | 剩餘空間 |
|----------|---------|------|--------|---------|
| Research | 4 | 50 | 8% | 46 slots |
| Project | 21 | 50 | 42% | 29 slots |
| **總計** | **25** | **100** | **25%** | **75 slots** |

---

## 附錄 B: 被淘汰的文件不在此計劃中

572 個被淘汰的文件（92.3%）包括：
- ~370 個時間快照（railway test reports, build reports）
- ~120 個 session logs 和 incident reports
- ~50 個已歸檔或內容過短的文件
- ~32 個已反映在代碼中的冗餘文件

所有被淘汰的文件仍在 git 歷史中可查，不會丟失任何知識。
