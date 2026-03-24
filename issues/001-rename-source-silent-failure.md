# Issue #001: add_source.py 重新命名來源可能靜默失敗

**狀態：** 已關閉 — 原報誤報，但調查期間發現並修正了真實的邊緣案例
**嚴重程度：** ~~高~~ 低（原報場景為誤報）
**修正版本：** v1.3.2
**發現日期：** 2026-03-22
**關閉日期：** 2026-03-22
**發現場景：** SingLingo 專案上傳 11 份來源到 NotebookLM

## 結論：誤報

經調查確認，`add_source.py` 的 Insert 和 Rename 均正常運作。來源 `[USER] 競品批評：FluentU/Migaku/Sounter/Talkpal` 確實存在於 NotebookLM 中，且 Gemini 能正確引用其標題和內容。

**誤判原因：** 操作者在 NotebookLM 來源清單中未滾動到該來源的位置（notebook 有 80+ 份來源），誤以為來源不存在。

**教訓：**
- 確認來源是否存在時，應直接問 NotebookLM 「是否有名為 X 的來源」，而非只靠目視清單
- 來源數量多時，清單需要滾動，容易遺漏

---

以下為原始調查內容（保留作為參考）：

---

## 問題描述

`add_source.py` 上傳來源並重新命名時，日誌顯示「✓ Source renamed to: [標題]」，但實際上來源在 NotebookLM 中可能仍然顯示為「貼上的文字」，重新命名靜默失敗。

## 影響

- 用戶無法透過來源清單辨識已上傳的來源
- 依賴 `--title` 做分類前綴管理（如 `[USER]`、`[競品分析]`）的工作流程會失效
- 回報成功但實際失敗 = 最糟糕的 bug 類型

## 重現條件

### 環境
- macOS Darwin 25.3.0
- NotebookLM 帳號 authuser=1
- Notebook 內已有大量來源（80+ 份）

### 重現步驟

```bash
# 1. 準備一個測試用 markdown 文件
cat > /tmp/test-rename.md << 'EOF'
# 測試來源

這是一個測試來源，用來驗證 add_source.py 的重新命名功能。
上傳時間：$(date)
EOF

# 2. 用 --show-browser 上傳並觀察重新命名過程
cd /Users/zhyz/.claude/skills/notebooklm
python3 scripts/run.py add_source.py \
  --file /tmp/test-rename.md \
  --notebook-url "YOUR_NOTEBOOK_URL" \
  --title "[TEST] 重新命名驗證" \
  --show-browser

# 3. 觀察瀏覽器中的操作：
#    a. 文字是否成功插入？
#    b. Insert 按鈕是否被點擊？
#    c. 重新命名時，是否找到正確的「貼上的文字」來源？
#    d. 三點選單是否打開？
#    e. 「重新命名來源」選項是否被點擊？
#    f. 重新命名 dialog 中的 input 是否被正確 focus 和填入？
#    g. 確認按鈕是否被點擊？

# 4. 上傳完成後，手動到 NotebookLM 確認：
#    - 來源清單中是否出現 "[TEST] 重新命名驗證"？
#    - 還是顯示為 "貼上的文字"？
```

### 預期結果
來源清單中顯示 `[TEST] 重新命名驗證`

### 實際結果（疑似）
來源清單中顯示 `貼上的文字`，但腳本日誌輸出 `✓ Source renamed to: [TEST] 重新命名驗證`

## 疑似根因分析

根據 SKILL.md 的 Gotchas 和程式碼分析，可能的失敗點有 4 個：

### 假說 1：`querySelectorAll` 定位到錯誤的來源
`add_source.py` 在插入新來源後，用 `querySelectorAll` 找所有「貼上的文字」來源，取最後一個來重新命名。但如果 notebook 有大量來源且 DOM 順序不是按插入時間排序，可能會點到錯誤的來源。

**驗證方式：** 用 `--show-browser` 觀察重新命名時高亮的是哪個來源。

### 假說 2：三點選單點到但 overlay 打開在錯誤位置
NotebookLM 使用 Angular Material CDK overlay，overlay 的定位可能偏移到其他來源的位置。

**驗證方式：** 觀察 overlay 彈出位置。

### 假說 3：重新命名 dialog 的 input focus 問題
SKILL.md Gotchas 明確記載：
> 「Focus lands on submit button, not input — After clicking '重新命名來源', the active element is the submit button. Must explicitly `.click()` the input before `.fill()`」

如果 `.click()` 沒有正確執行，`.fill()` 會靜默失敗（寫入到 submit button 而非 input）。

**驗證方式：** 在 `--show-browser` 模式下觀察 input 是否被選中並填入。

### 假說 4：重新命名 dialog 的 input selector 不匹配
SKILL.md Gotchas 記載：
> 「Rename dialog input class is `title-input` not `rename-input` — The overlay uses `input.title-input` inside `.cdk-overlay-pane`. Using wrong selector silently fails (returns true but doesn't rename)」

如果 NotebookLM UI 更新改變了 selector，重新命名會靜默失敗。

**驗證方式：** 在瀏覽器 DevTools 中檢查重新命名 dialog 的 input 的實際 class。

## 檢查清單

調查時請按順序確認：

- [ ] `--show-browser` 模式下，插入文字是否成功
- [ ] 插入後，是否正確找到最新的「貼上的文字」來源
- [ ] 三點選單是否正確打開
- [ ] 「重新命名來源」menuitem 是否正確點擊
- [ ] 重新命名 dialog 是否出現
- [ ] input 是否被正確 focus（而非 submit button）
- [ ] input 的 CSS selector 是否為 `input.title-input`
- [ ] 填入標題後，確認按鈕是否被點擊
- [ ] 點擊確認後，來源清單是否即時更新

## 相關檔案

- `scripts/add_source.py` — 主要邏輯
- `SKILL.md` L275-290 — Gotchas: Add Source 章節
- `scripts/browser_utils.py` — 瀏覽器工廠
- `scripts/config.py` — CSS selector 定義

## 備註

此問題在同一 session 中上傳 11 份來源時發現。前 10 份在 NotebookLM 來源清單中正確顯示標題，第 11 份（競品批評）雖然日誌顯示成功，但在來源清單中找不到對應標題。可能是 notebook 來源數量較多時（80+）才會觸發的邊緣案例。
