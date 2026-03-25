#!/usr/bin/env python3
"""
Universal runner for NotebookLM skill scripts
Ensures all scripts run with the correct virtual environment
"""

import os
import sys
import subprocess
from pathlib import Path


def get_venv_python():
    """Get the virtual environment Python executable"""
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"

    if os.name == 'nt':  # Windows
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        venv_python = venv_dir / "bin" / "python"

    return venv_python


def ensure_venv():
    """Ensure virtual environment exists"""
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"
    setup_script = skill_dir / "scripts" / "setup_environment.py"

    # Check if venv exists
    if not venv_dir.exists():
        print("🔧 First-time setup: Creating virtual environment...")
        print("   This may take a minute...")

        # Run setup with system Python
        result = subprocess.run([sys.executable, str(setup_script)])
        if result.returncode != 0:
            print("❌ Failed to set up environment")
            sys.exit(1)

        print("✅ Environment ready!")

    return get_venv_python()


def run_daemon_command(venv_python, skill_dir, daemon_args):
    """Run browser_daemon.py with the given arguments."""
    daemon_script = skill_dir / "scripts" / "browser_daemon.py"
    if not daemon_script.exists():
        print(f"❌ browser_daemon.py not found: {daemon_script}")
        sys.exit(1)
    cmd = [str(venv_python), str(daemon_script)] + daemon_args
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main runner"""
    if len(sys.argv) < 2:
        print("Usage: python run.py <script_name> [args...]")
        print("       python run.py daemon <start|stop|status> [--timeout N]")
        print("\nAvailable scripts:")
        print("  ask_question.py    - Query NotebookLM")
        print("  notebook_manager.py - Manage notebook library")
        print("  session_manager.py  - Manage sessions")
        print("  auth_manager.py     - Handle authentication")
        print("  cleanup_manager.py  - Clean up skill data")
        print("\nDaemon commands:")
        print("  daemon start [--timeout 600]  - Start browser daemon in background")
        print("  daemon stop                   - Stop running daemon")
        print("  daemon status                 - Check daemon status")
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]

    # Handle daemon sub-commands: python run.py daemon <start|stop|status> [...]
    if script_name == "daemon":
        if not script_args:
            print("Usage: python run.py daemon <start|stop|status> [--timeout N]")
            sys.exit(1)
        skill_dir = Path(__file__).parent.parent
        venv_python = ensure_venv()
        run_daemon_command(venv_python, skill_dir, script_args)
        return  # run_daemon_command calls sys.exit, but be explicit

    # Handle both "scripts/script.py" and "script.py" formats
    if script_name.startswith('scripts/'):
        # Remove the scripts/ prefix if provided
        script_name = script_name[8:]  # len('scripts/') = 8

    # Ensure .py extension
    if not script_name.endswith('.py'):
        script_name += '.py'

    # Get script path
    skill_dir = Path(__file__).parent.parent
    script_path = skill_dir / "scripts" / script_name

    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        print(f"   Working directory: {Path.cwd()}")
        print(f"   Skill directory: {skill_dir}")
        print(f"   Looked for: {script_path}")
        sys.exit(1)

    # Ensure venv exists and get Python executable
    venv_python = ensure_venv()

    # Build command
    cmd = [str(venv_python), str(script_path)] + script_args

    # Run the script
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()