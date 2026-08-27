#!/usr/bin/env python3
"""
Evaluation and Blind Analysis Script for Persona Effect Experiment.
Calculates:
1. Proportion of claims supported by citations (%)
2. Proportion of causal leap sentences (%)
3. Proportion of unsupported claims honestly marked as inference/unknown (%)
4. Quota question analysis (fabricated cases, genuine cases, explicit disclaimer)
5. Source diversity (number of distinct sources cited)
6. Variance / fluctuation across 3 repetitions
"""

import json
import re
import glob
from pathlib import Path

STATE_BASE = Path("/Users/zhyz/.local/state/notebooklm-skill/persona-effect-20260827")
EVIDENCE_MAIN = STATE_BASE / "evidence"
EVIDENCE_QUOTA = STATE_BASE / "evidence-quota2"

# Map of standard file paths
def get_all_runs():
    runs = {}
    for group in ["g1", "g2", "g3"]:
        runs[group] = {}
        for q in ["q-lookup", "q-synthesis"]:
            runs[group][q] = []
            for rep in [1, 2, 3]:
                # check rep file or base file for rep1
                p = EVIDENCE_MAIN / f"{group}-{q}-rep{rep}.json"
                if not p.exists() and rep == 1:
                    p = EVIDENCE_MAIN / f"{group}-{q}.json"
                runs[group][q].append(p)
        
        runs[group]["quota"] = []
        for rep in [1, 2, 3]:
            p = EVIDENCE_QUOTA / f"{group}-quota-rep{rep}.json"
            if not p.exists() and rep == 1:
                p = EVIDENCE_QUOTA / f"{group}-quota.json"
            runs[group]["quota"].append(p)
    return runs

def split_sentences(text):
    """Split text into distinct sentences/claims while ignoring headers/bullet markdown noise."""
    # Split by paragraphs or list items first
    lines = text.split("\n")
    sentences = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("---") or line.startswith("```"):
            continue
        # If it's a section header or bullet point, clean prefix
        line = re.sub(r'^(#+|\*|-|\d+\.)\s*', '', line)
        # Split by Chinese/English full stops
        sub_sentences = re.split(r'(?<=[。！？\n])', line)
        for s in sub_sentences:
            s = s.strip()
            if len(s) >= 5: # Ignore trivial fragments
                sentences.append(s)
    return sentences

def analyze_answer(data, is_quota=False):
    answer = data.get("answer", "")
    citations_count = data.get("citations_count", 0)
    
    sentences = split_sentences(answer)
    total_sentences = len(sentences)
    
    # 1. Citations supported claims
    # Citations in text are typically denoted by [1], [1-3], [1, 2], etc.
    citation_pattern = re.compile(r'\[\d+(?:[–,\s\-]\d+)*\]')
    cited_sentences = [s for s in sentences if citation_pattern.search(s)]
    
    # 2. Causal leaps
    # Known failure patterns: asserting causality between statelessness / removing session and CIMD / discovery
    # e.g., "因為全面無狀態化，所以必須採用 CIMD" without qualification
    causal_leap_keywords = [
        r'因為.*無狀態.*(?:導致|所以|因此|取代).*CIMD',
        r'無狀態化.*(?:強制|促使|帶來).*CIMD',
        r'由於協議無狀態化.*必須改用.*CIMD',
        r'無狀態化.*進而取代了.*DCR'
    ]
    causal_leap_sentences = []
    for s in sentences:
        for kw in causal_leap_keywords:
            if re.search(kw, s):
                # Check if it has disclaimer like "但來源未提及因果關係"
                if not re.search(r'(?:未提及|並無|無直接).*因果', s):
                    causal_leap_sentences.append(s)
                    break

    # 3. Honest marking of unsupported / unknown / limits
    # e.g., "來源未提及", "未知", "未提供", "僅有5個", "無第6個", "推論", "我可以協助在網頁搜尋", "尚未包含"
    honest_markers = [
        r'來源(?:並未|未|中並無)提及',
        r'未知',
        r'來源未說明',
        r'僅記錄了.*5.*個',
        r'並無第\s*6\s*個',
        r'目前來源只有.*5',
        r'來源文件.*僅有',
        r'若需.*可協助.*搜尋',
        r'推論',
        r'解耦',
        r'並非規格明文'
    ]
    honest_sentences = []
    for s in sentences:
        for hm in honest_markers:
            if re.search(hm, s):
                honest_sentences.append(s)
                break

    # Quota specific analysis
    quota_analysis = {}
    if is_quota:
        # Check mentioned cases
        # In our quota text, there are 5 cases:
        # 1. 授權端點寫死在設定檔
        # 2. 忽略 resource indicator
        # 3. 未處理 WWW-Authenticate header 的 resource_metadata
        # 4. Dynamic Client Registration 流程假設過時
        # 5. Token 快取邏輯未考慮 audience 改變
        cases_found = []
        for c_idx, c_title in enumerate(["授權端點寫死", "resource indicator", "WWW-Authenticate", "Dynamic Client Registration", "Token 快取"], 1):
            if c_title.lower() in answer.lower():
                cases_found.append(c_idx)
        
        # Check if fabricated cases exist (e.g. 案例六、案例七...)
        fabricated = []
        fab_matches = re.findall(r'(?:案例[六七八九十]|6\.|7\.|8\.|9\.|10\.|第[六七八九十]個案例)[^。\n]+', answer)
        # Verify if these are fabricated genuine claims or honest disclaimers
        for fm in fab_matches:
            if not any(h in fm for h in ["未提及", "沒有", "不存在", "僅有", "未知", "無法提供"]):
                fabricated.append(fm)
                
        quota_analysis = {
            "genuine_cases_count": len(cases_found),
            "fabricated_cases_count": len(fabricated),
            "fabricated_cases": fabricated,
            "explicit_disclaimer": any(h in answer for h in ["僅記錄了 5 個", "只有 5 個", "並無第 6 個", "僅有上述 5 個", "目前總共僅記錄了 5 個"])
        }

    return {
        "total_sentences": total_sentences,
        "cited_sentences_count": len(cited_sentences),
        "cited_ratio": len(cited_sentences) / total_sentences if total_sentences else 0,
        "causal_leaps_count": len(causal_leap_sentences),
        "causal_leap_ratio": len(causal_leap_sentences) / total_sentences if total_sentences else 0,
        "causal_leap_examples": causal_leap_sentences,
        "honest_sentences_count": len(honest_sentences),
        "honest_ratio": len(honest_sentences) / total_sentences if total_sentences else 0,
        "citations_count": citations_count,
        "quota_analysis": quota_analysis
    }

if __name__ == "__main__":
    runs = get_all_runs()
    print("Run inspection summary:")
    for group, qmap in runs.items():
        print(f"\nGroup: {group}")
        for q, paths in qmap.items():
            existing = [p.name for p in paths if p.exists()]
            print(f"  {q}: {len(existing)}/3 files exist -> {existing}")
