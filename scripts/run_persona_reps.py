#!/usr/bin/env python3
"""
Automated runner for Persona Effect Experiment (Repetition 2 and 3).
Strictly adheres to 2026-08-27-persona-effect-experiment-plan.md rules:
1. --fresh on every ask.
2. rm -rf advisor directory before adopting new persona.
3. Finish all questions in one group before switching persona.
4. Save raw JSON outputs for all runs.
"""

import os
import sys
import json
import shutil
import subprocess
import time
from pathlib import Path

VENV_PYTHON = "/Users/zhyz/Documents/Project/notebooklm-skill/.venv/bin/python"
STATE_BASE = Path("/Users/zhyz/.local/state/notebooklm-skill/persona-effect-20260827")
ADVISORS_DIR = STATE_BASE / "advisors"
CONFIGS_MAIN = STATE_BASE / "configs"
CONFIGS_QUOTA = STATE_BASE / "configs-quota2"
EVIDENCE_MAIN = STATE_BASE / "evidence"
EVIDENCE_QUOTA = STATE_BASE / "evidence-quota2"

NOTEBOOK_MAIN = "d8981101-012b-4d51-818e-2ce4289c89ca"
NOTEBOOK_QUOTA = "da79f874-b2ec-4fbc-a310-32c89ac9ed89"

QUESTIONS = {
    "q-lookup": "MCP 客戶端在收到 HTTP 401 時，應該用哪些方式取得授權伺服器的中繼資料？",
    "q-synthesis": "假設要把一個 2024 年寫成、把 authorization endpoint 寫死在設定檔中的 TypeScript MCP client 升級到目前規格，需要異動哪些元件？",
    "quota": "請舉出 10 個 MCP client 遷移時常見的錯誤模式案例。"
}

GROUPS = [
    {
        "name": "g1",
        "label": "Group 1 - Baseline",
        "main_config": CONFIGS_MAIN / "g1-baseline.json",
        "quota_config": CONFIGS_QUOTA / "g1-baseline.json",
        "main_advisor": "persona-exp-g1-baseline",
        "quota_advisor": "persona-exp-quota2-g1",
    },
    {
        "name": "g2",
        "label": "Group 2 - Role Only",
        "main_config": CONFIGS_MAIN / "g2-role-only.json",
        "quota_config": CONFIGS_QUOTA / "g2-role-only.json",
        "main_advisor": "persona-exp-g2-role-only",
        "quota_advisor": "persona-exp-quota2-g2",
    },
    {
        "name": "g3",
        "label": "Group 3 - Role + Strict Grounding",
        "main_config": CONFIGS_MAIN / "g3-strict-grounding.json",
        "quota_config": CONFIGS_QUOTA / "g3-strict-grounding.json",
        "main_advisor": "persona-exp-g3-strict-grounding",
        "quota_advisor": "persona-exp-quota2-g3",
    }
]

def run_cmd(cmd, outfile=None):
    print(f"[RUNNING] {' '.join(cmd)}")
    start = time.time()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    elapsed = time.time() - start
    print(f"[FINISHED] returncode={res.returncode}, elapsed={elapsed:.2f}s")
    if res.returncode != 0:
        print(f"[ERROR STDERR]: {res.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr}")
    
    if outfile:
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(res.stdout)
        print(f"[SAVED] {outfile} ({len(res.stdout)} chars)")
    return res.stdout

def setup_advisor(config_path, adopt_notebook_id, advisor_id):
    target_dir = ADVISORS_DIR / advisor_id
    if target_dir.exists():
        print(f"[CLEANUP] Removing existing advisor dir: {target_dir}")
        shutil.rmtree(target_dir)
    
    cmd = [
        VENV_PYTHON, "-m", "notebooklm_skill.cli",
        "--state-root", str(ADVISORS_DIR),
        "setup",
        "--config", str(config_path),
        "--adopt-notebook-id", adopt_notebook_id
    ]
    run_cmd(cmd)

def ask_question(advisor_id, question_text, outfile):
    cmd = [
        VENV_PYTHON, "-m", "notebooklm_skill.cli",
        "--state-root", str(ADVISORS_DIR),
        "ask",
        "--advisor-id", advisor_id,
        "--fresh",
        "--question", question_text
    ]
    run_cmd(cmd, outfile=outfile)

def run_group(group, rep):
    print(f"\n==========================================")
    print(f"Starting {group['label']} (Repetition {rep})")
    print(f"==========================================")
    
    # 1. Main questions (Q_lookup & Q_synthesis)
    main_lookup_out = EVIDENCE_MAIN / f"{group['name']}-q-lookup-rep{rep}.json"
    main_synthesis_out = EVIDENCE_MAIN / f"{group['name']}-q-synthesis-rep{rep}.json"
    
    if not (main_lookup_out.exists() and main_synthesis_out.exists()):
        print(f"--- Setting up Main Notebook for {group['name']} ---")
        setup_advisor(group["main_config"], NOTEBOOK_MAIN, group["main_advisor"])
        
        if not main_lookup_out.exists():
            print(f"--- Asking Q_lookup ({group['name']} rep{rep}) ---")
            ask_question(group["main_advisor"], QUESTIONS["q-lookup"], main_lookup_out)
        else:
            print(f"[SKIPPED] {main_lookup_out} already exists.")
            
        if not main_synthesis_out.exists():
            print(f"--- Asking Q_synthesis ({group['name']} rep{rep}) ---")
            ask_question(group["main_advisor"], QUESTIONS["q-synthesis"], main_synthesis_out)
        else:
            print(f"[SKIPPED] {main_synthesis_out} already exists.")
    else:
        print(f"[SKIPPED] Both main outputs already exist for {group['name']} rep{rep}")

    # 2. Quota question
    quota_out = EVIDENCE_QUOTA / f"{group['name']}-quota-rep{rep}.json"
    if not quota_out.exists():
        print(f"--- Setting up Quota Notebook for {group['name']} ---")
        setup_advisor(group["quota_config"], NOTEBOOK_QUOTA, group["quota_advisor"])
        print(f"--- Asking Q_quota ({group['name']} rep{rep}) ---")
        ask_question(group["quota_advisor"], QUESTIONS["quota"], quota_out)
    else:
        print(f"[SKIPPED] {quota_out} already exists.")

def main():
    print("Starting Persona Effect Experiment Pipeline...")
    for rep in [2, 3]:
        print(f"\n##########################################")
        print(f"   STARTING REPETITION {rep}")
        print(f"##########################################")
        for group in GROUPS:
            run_group(group, rep)
    print("\nAll repetitions completed successfully!")

if __name__ == "__main__":
    main()
