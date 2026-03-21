# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-03-21

### Fixed / 修復
- **Multi-Account Auth Bug / 多帳號認證錯誤** - Users with multiple Google accounts no longer silently authenticate as the wrong account / 多 Google 帳號用戶不再靜默登入錯誤帳號
  - New `extract_authuser()` parses `authuser` parameter from notebook URLs / 新增 `extract_authuser()` 從 notebook URL 解析 `authuser` 參數
  - New `diagnose_access_denied()` detects "needs access" pages via text pattern matching (EN/zh-TW) / 新增 `diagnose_access_denied()` 以文字比對偵測「需要存取權」頁面
  - `setup_auth()` now saves which `authuser` index was used during login / `setup_auth()` 登入後儲存使用的 `authuser` 索引
  - `validate_auth()` checks authuser mismatch before launching browser / `validate_auth()` 在啟動瀏覽器前檢查 authuser 是否匹配
  - `ask_question.py` shows actionable error with re-auth instructions instead of generic DOM errors / `ask_question.py` 顯示可操作的錯誤訊息與重新認證指示，取代無意義的 DOM 錯誤
  - Single-account users are unaffected / 單帳號用戶不受影響（所有檢查以 authuser 存在為前提）

## [1.3.0] - 2025-11-21

### Added
- **Modular Architecture** - Refactored codebase for better maintainability
  - New `config.py` - Centralized configuration (paths, selectors, timeouts)
  - New `browser_utils.py` - BrowserFactory and StealthUtils classes
  - Cleaner separation of concerns across all scripts

### Changed
- **Timeout increased to 120 seconds** - Long queries no longer timeout prematurely
  - `ask_question.py`: 30s → 120s
  - `browser_session.py`: 30s → 120s
  - Resolves Issue #4

### Fixed
- **Thinking Message Detection** - Fixed incomplete answers showing placeholder text
  - Now waits for `div.thinking-message` element to disappear before reading answer
  - Answers like "Reviewing the content..." or "Looking for answers..." no longer returned prematurely
  - Works reliably across all languages and NotebookLM UI changes

- **Correct CSS Selectors** - Updated to match current NotebookLM UI
  - Changed from `.response-content, .message-content` to `.to-user-container .message-text-content`
  - Consistent selectors across all scripts

- **Stability Detection** - Improved answer completeness check
  - Now requires 3 consecutive stable polls instead of 1 second wait
  - Prevents truncated responses during streaming

## [1.2.0] - 2025-10-28

### Added
- Initial public release
- NotebookLM integration via browser automation
- Session-based conversations with Gemini 2.5
- Notebook library management
- Knowledge base preparation tools
- Google authentication with persistent sessions
