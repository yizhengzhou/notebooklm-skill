#!/usr/bin/env python3
"""
Browser Daemon for NotebookLM Skill
Keeps a single Playwright browser context alive between queries to eliminate
cold-start overhead. Accepts JSON requests over a Unix domain socket.

Protocol (newline-delimited JSON):
  Request:  {"action": "query", "notebook_url": "...", "question": "..."}
            {"action": "status"}
            {"action": "shutdown"}
  Response: {"status": "ok", "answer": "..."}
            {"status": "ok", "uptime": 123, "pages": 2}
            {"status": "ok", "message": "shutting down"}
            {"status": "error", "error": "..."}
"""

import argparse
import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from patchright.sync_api import sync_playwright, BrowserContext, Page, Playwright

# Add scripts directory to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from browser_utils import (
    BrowserFactory, StealthUtils,
    find_visible_input, snapshot_latest_response, poll_for_stable_response,
)
from config import DATA_DIR, QUERY_TIMEOUT_SECONDS

# ── Daemon socket / PID constants ─────────────────────────────────────────────
DAEMON_SOCK = str(DATA_DIR / "daemon.sock")
DAEMON_PID  = str(DATA_DIR / "daemon.pid")
DAEMON_LOG  = str(DATA_DIR / "daemon.log")

MAX_PAGES = 10  # LRU eviction cap


# ── Socket protocol helper ────────────────────────────────────────────────────

def _send_request(request: dict, timeout: int = 10) -> dict:
    """Send a JSON request to the daemon and return the parsed response."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(DAEMON_SOCK)
        sock.sendall((json.dumps(request) + "\n").encode())
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\n" in response:
                break
        return json.loads(response.decode().strip())
    finally:
        sock.close()


# ── Client helper (imported by ask_question.py) ───────────────────────────────

def daemon_query(notebook_url: str, question: str) -> Optional[str]:
    """
    Try to query via the background daemon.
    Returns the answer string, or None if the daemon is not running.
    Never raises.
    """
    if not os.path.exists(DAEMON_SOCK):
        return None
    try:
        result = _send_request(
            {"action": "query", "notebook_url": notebook_url, "question": question},
            timeout=180,
        )
        if result.get("status") == "ok":
            return result.get("answer")
        return None
    except Exception:
        return None


# ── Daemon implementation ─────────────────────────────────────────────────────

class NotebookDaemon:
    """
    Long-lived process that holds a Playwright browser context open and
    serves query requests via a Unix domain socket.
    """

    def __init__(self, idle_timeout: int = 600):
        self.idle_timeout = idle_timeout
        self.start_time = time.time()
        self.last_activity = time.time()

        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._pages: Dict[str, Page] = {}
        self._pages_lock = threading.Lock()
        # Per-URL locks prevent concurrent queries from racing on the same Page
        self._url_locks: Dict[str, threading.Lock] = {}
        self._url_locks_meta = threading.Lock()

        self._server_sock: Optional[socket.socket] = None
        self._running = False

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self):
        """Launch browser, bind socket, enter the request-handling event loop."""
        print(f"[daemon] Starting — idle_timeout={self.idle_timeout}s", flush=True)

        self._playwright = sync_playwright().start()
        self._context = BrowserFactory.launch_persistent_context(
            self._playwright, headless=True,
        )
        print("[daemon] Browser context ready", flush=True)

        if os.path.exists(DAEMON_SOCK):
            os.unlink(DAEMON_SOCK)
        self._server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_sock.bind(DAEMON_SOCK)
        self._server_sock.listen(5)
        print(f"[daemon] Listening on {DAEMON_SOCK}", flush=True)

        with open(DAEMON_PID, "w") as f:
            f.write(str(os.getpid()))

        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._running = True
        watchdog = threading.Thread(target=self._idle_watchdog, daemon=True)
        watchdog.start()

        self._accept_loop()

    def stop(self):
        """Tear down everything cleanly."""
        if not self._running:
            return
        self._running = False
        print("[daemon] Stopping…", flush=True)

        with self._pages_lock:
            for url, page in list(self._pages.items()):
                try:
                    page.close()
                except Exception:
                    pass
            self._pages.clear()

        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None
        for path in (DAEMON_SOCK, DAEMON_PID):
            if os.path.exists(path):
                os.unlink(path)

        print("[daemon] Stopped.", flush=True)

    def _signal_handler(self, signum, frame):
        print(f"[daemon] Received signal {signum}, shutting down", flush=True)
        self.stop()
        sys.exit(0)

    # ── Accept loop ───────────────────────────────────────────────────────────

    def _accept_loop(self):
        self._server_sock.settimeout(2.0)
        while self._running:
            try:
                conn, _ = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(target=self._handle_connection, args=(conn,), daemon=True)
            t.start()

    # ── Connection / request handling ─────────────────────────────────────────

    def _handle_connection(self, conn: socket.socket):
        try:
            data = b""
            conn.settimeout(10)
            while b"\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk

            if not data.strip():
                return

            request = json.loads(data.decode().strip())
            action = request.get("action", "")
            self.last_activity = time.time()

            if action == "query":
                response = self._dispatch_query(request)
            elif action == "status":
                response = self._dispatch_status()
            elif action == "shutdown":
                response = {"status": "ok", "message": "shutting down"}
                self._send_response(conn, response)
                conn.close()
                threading.Thread(target=self._delayed_stop, daemon=True).start()
                return
            else:
                response = {"status": "error", "error": f"Unknown action: {action!r}"}

            self._send_response(conn, response)
        except json.JSONDecodeError as e:
            try:
                self._send_response(conn, {"status": "error", "error": f"JSON parse error: {e}"})
            except Exception:
                pass
        except Exception as e:
            try:
                self._send_response(conn, {"status": "error", "error": str(e)})
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _delayed_stop(self):
        time.sleep(0.3)
        self.stop()
        sys.exit(0)

    @staticmethod
    def _send_response(conn: socket.socket, response: dict):
        conn.sendall((json.dumps(response) + "\n").encode())

    # ── Action dispatchers ────────────────────────────────────────────────────

    def _dispatch_query(self, request: dict) -> dict:
        notebook_url = request.get("notebook_url", "").strip()
        question = request.get("question", "").strip()

        if not notebook_url:
            return {"status": "error", "error": "Missing notebook_url"}
        if not question:
            return {"status": "error", "error": "Missing question"}

        try:
            answer = self._handle_query(notebook_url, question)
            self.last_activity = time.time()
            return {"status": "ok", "answer": answer}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _dispatch_status(self) -> dict:
        with self._pages_lock:
            page_count = len(self._pages)
        return {
            "status": "ok",
            "uptime": int(time.time() - self.start_time),
            "pages": page_count,
            "idle_seconds": int(time.time() - self.last_activity),
        }

    # ── Query implementation ──────────────────────────────────────────────────

    def _get_url_lock(self, url: str) -> threading.Lock:
        with self._url_locks_meta:
            if url not in self._url_locks:
                self._url_locks[url] = threading.Lock()
            return self._url_locks[url]

    def _handle_query(self, notebook_url: str, question: str) -> str:
        """Thread-safe: acquires per-URL lock to prevent concurrent Page access."""
        with self._get_url_lock(notebook_url):
            page = self._get_or_create_page(notebook_url)
            previous_answer = snapshot_latest_response(page)

            input_selector = find_visible_input(page, timeout=10000)
            if not input_selector:
                raise RuntimeError("Could not find query input textarea")
            StealthUtils.fast_fill(page, input_selector, question)
            page.keyboard.press("Enter")

            answer = poll_for_stable_response(
                page, previous_answer=previous_answer,
                timeout=QUERY_TIMEOUT_SECONDS,
                poll_interval=0.5, stable_threshold=2,
            )
            if not answer:
                raise TimeoutError(f"No response within {QUERY_TIMEOUT_SECONDS}s")
            return answer

    def _get_or_create_page(self, notebook_url: str) -> Page:
        with self._pages_lock:
            page = self._pages.get(notebook_url)

            if page is not None:
                if self._page_is_alive(page):
                    return page
                try:
                    page.close()
                except Exception:
                    pass
                del self._pages[notebook_url]

            # Evict oldest if at capacity
            if len(self._pages) >= MAX_PAGES:
                oldest_url = next(iter(self._pages))
                try:
                    self._pages[oldest_url].close()
                except Exception:
                    pass
                del self._pages[oldest_url]

            page = self._context.new_page()

        # Navigation outside the lock (slow I/O)
        page.goto(notebook_url, wait_until="domcontentloaded", timeout=30000)

        if "accounts.google.com" in page.url:
            page.close()
            raise RuntimeError("Authentication required. Run: python scripts/run.py auth_manager.py setup")

        input_sel = find_visible_input(page, timeout=30000)
        if not input_sel:
            page.close()
            raise RuntimeError("Query input not found after navigation")

        with self._pages_lock:
            self._pages[notebook_url] = page
        print(f"[daemon] New page created for {notebook_url}", flush=True)
        return page

    @staticmethod
    def _page_is_alive(page: Page) -> bool:
        try:
            _ = page.url
            return not page.is_closed()
        except Exception:
            return False

    # ── Idle watchdog ─────────────────────────────────────────────────────────

    def _idle_watchdog(self):
        while self._running:
            time.sleep(30)
            self._evict_dead_pages()
            idle = time.time() - self.last_activity
            if idle > self.idle_timeout:
                print(f"[daemon] Idle for {idle:.0f}s — shutting down", flush=True)
                self.stop()
                sys.stdout.flush()
                os._exit(0)

    def _evict_dead_pages(self):
        with self._pages_lock:
            dead = [url for url, page in self._pages.items()
                    if not self._page_is_alive(page)]
            for url in dead:
                try:
                    self._pages[url].close()
                except Exception:
                    pass
                del self._pages[url]
            if dead:
                print(f"[daemon] Evicted {len(dead)} dead pages", flush=True)


# ── CLI helpers ───────────────────────────────────────────────────────────────

def _read_pid() -> Optional[int]:
    try:
        with open(DAEMON_PID) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _daemon_is_running() -> bool:
    pid = _read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _cmd_start(timeout: int):
    if _daemon_is_running():
        print(f"Daemon is already running (PID {_read_pid()})")
        sys.exit(0)

    # Ensure data dir exists for socket/pid/log
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Starting daemon (idle timeout={timeout}s) — log: {DAEMON_LOG}")

    try:
        pid = os.fork()
    except AttributeError:
        import subprocess
        log_fd = open(DAEMON_LOG, "a")
        subprocess.Popen(
            [sys.executable, __file__, "_run", "--timeout", str(timeout)],
            stdout=log_fd, stderr=log_fd, close_fds=True,
        )
        print("Daemon started (subprocess mode)")
        return

    if pid > 0:
        time.sleep(1.5)
        if _daemon_is_running():
            print(f"Daemon started (PID {_read_pid()})")
        else:
            print("Warning: daemon may not have started — check " + DAEMON_LOG)
        return

    # --- Child process ---
    os.setsid()

    try:
        pid2 = os.fork()
    except Exception:
        pid2 = 0

    if pid2 > 0:
        os._exit(0)

    # Grandchild: redirect stdio properly
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    os.close(devnull)

    log_fd = os.open(DAEMON_LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(log_fd, 1)
    os.dup2(log_fd, 2)
    os.close(log_fd)

    sys.stdout = os.fdopen(1, "w", buffering=1)
    sys.stderr = sys.stdout

    daemon = NotebookDaemon(idle_timeout=timeout)
    try:
        daemon.start()
    except Exception as e:
        print(f"[daemon] Fatal error: {e}", flush=True)
        sys.exit(1)


def _cmd_stop():
    if not os.path.exists(DAEMON_SOCK):
        print("Daemon is not running (no socket found)")
        sys.exit(1)
    try:
        result = _send_request({"action": "shutdown"})
        print("Daemon:", result.get("message", result))
    except Exception as e:
        print(f"Could not reach daemon: {e}")
        sys.exit(1)


def _cmd_status():
    if not _daemon_is_running():
        print("Daemon is not running")
        sys.exit(1)
    if not os.path.exists(DAEMON_SOCK):
        print(f"Daemon PID {_read_pid()} exists but socket not found")
        sys.exit(1)
    try:
        result = _send_request({"action": "status"})
        pid = _read_pid()
        print(f"Daemon is running (PID {pid})")
        print(f"  Uptime      : {result.get('uptime', '?')}s")
        print(f"  Open pages  : {result.get('pages', '?')}")
        print(f"  Idle        : {result.get('idle_seconds', '?')}s")
    except Exception as e:
        print(f"Daemon socket error: {e}")
        sys.exit(1)


def _cmd_run(timeout: int):
    daemon = NotebookDaemon(idle_timeout=timeout)
    daemon.start()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM browser daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Commands:\n  start   Launch daemon in background\n  stop    Send shutdown\n  status  Check status\n",
    )
    subparsers = parser.add_subparsers(dest="command")

    start_p = subparsers.add_parser("start", help="Start the daemon in the background")
    start_p.add_argument("--timeout", type=int, default=600, help="Idle timeout in seconds (default: 600)")

    subparsers.add_parser("stop", help="Stop a running daemon")
    subparsers.add_parser("status", help="Show daemon status")

    run_p = subparsers.add_parser("_run")
    run_p.add_argument("--timeout", type=int, default=600)

    args = parser.parse_args()

    if args.command == "start":
        _cmd_start(args.timeout)
    elif args.command == "stop":
        _cmd_stop()
    elif args.command == "status":
        _cmd_status()
    elif args.command == "_run":
        _cmd_run(args.timeout)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
