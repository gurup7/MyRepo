#!/usr/bin/env python3
"""
JIL CSV Creator — ZERO external dependencies (no openpyxl, no pip install needed).

Uses only Python's built-in modules (re, sys, os, csv).
Outputs two CSV files that open directly in Excel:
    <output>.csv          - per-job detail (15 columns)
    <output>_summary.csv  - counts by category and target platform

Same parsing + skill-file decision logic as jil_excel_creator.py, but no library needed.

Usage:
    python jil_csv_creator.py "150043_LINUX_JILS 1.txt"
    python jil_csv_creator.py "150043_LINUX_JILS 1.txt" autosys.csv
"""

import re
import sys
import os
import csv

# --- Regex patterns for JIL fields ---
P_JOB     = re.compile(r"insert_job:\s*(\S+)")
P_TYPE    = re.compile(r"job_type:\s*(\S+)")
P_CMD     = re.compile(r"command:\s*(.+)")
P_BOX     = re.compile(r"box_name:\s*(\S+)")
P_DATE    = re.compile(r"date_conditions:\s*(\S+)")
P_COND    = re.compile(r"condition:\s*(.+)")
P_START   = re.compile(r"start_times:\s*(.+)")
P_RUNCAL  = re.compile(r"run_calendar:\s*(\S+)")
P_EXCAL   = re.compile(r"exclude_calendar:\s*(\S+)")
P_MACHINE = re.compile(r"machine:\s*(\S+)")
P_ALARM   = re.compile(r"alarm_if_fail:\s*(\S+)")


def classify_job(name: str, command: str) -> str:
    """Functional category based on job name + command."""
    n = (name + " " + command).upper()
    rules = [
        ("Server Start",      ["_START", "STARTWEBLOGIC", "STARTMANAGED", "START_SERVER"]),
        ("Server Stop",       ["_STOP", "STOPWEBLOGIC", "STOPMANAGED", "STOP_SERVER"]),
        ("NGINX/Web Start",   ["NGINX", "APACHE"]),
        ("Sleep/Wait",        ["SLEEP"]),
        ("Feed File Check",   ["FEED_CHK", "CHKFEEDFILE", "FEED_CHECK"]),
        ("Data Upload/Load",  ["UPLOAD", "_UPDATE", "_LOAD", "RSFSREF"]),
        ("Report Generation", ["REPORT"]),
        ("NDM File Transfer", ["NDM"]),
        ("SCP File Transfer", ["SCP"]),
        ("Date Rollover",     ["ROLLOVER"]),
        ("Cache Refresh",     ["CACHE"]),
        ("Permission Change", ["PERMCHG", "CHMOD", "_PERM"]),
        ("Purge/Cleanup",     ["PURGE", "CLEANUP", "CLEAN_LOG", "CLEAN LOGS"]),
        ("Consolidation",     ["CONSOLIDATE"]),
        ("DMS Document",      ["DMS", "LODGE"]),
        ("Entitlement",       ["ENTITLEMENT", "ENTITILEMENT", "ENTIT"]),
        ("Batch Processing",  ["BATCH"]),
        ("Test/Interface",    ["TEST", "INTERFACE"]),
    ]
    for category, keywords in rules:
        if any(k in n for k in keywords):
            if category == "NGINX/Web Start":
                return "NGINX/Web Stop" if "STOP" in n else "NGINX/Web Start"
            return category
    return "Other / Business Job"


def target_platform(category, date_condition, start_times, condition, box_name):
    """Skill-file Section 12 decision logic (top-down, first match wins)."""
    if category in ("Server Start", "Server Stop", "NGINX/Web Start", "NGINX/Web Stop"):
        return ("ELIMINATED", "Container lifecycle managed by OpenShift Deployment/probes")
    if category == "Sleep/Wait":
        return ("ELIMINATED", "Replaced by readiness/liveness probes")
    if condition:
        return ("Argo Workflow (DAG)", "Has condition dependency; needs orchestrated workflow")
    if start_times:
        return ("OpenShift CronJob / Argo CronWorkflow", "Fixed schedule via start_times")
    if str(date_condition) == "1":
        return ("OpenShift CronJob (Scheduled)", "date_conditions=1 (scheduled)")
    if str(date_condition) == "0":
        if box_name:
            return ("Argo Workflow task", "date_conditions=0, triggered within BOX")
        return ("On-demand OpenShift Job", "date_conditions=0, event/manually triggered")
    return ("OpenShift Job", "Default containerized job")


def parse_jil(path):
    jobs = {}
    current = None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            m = P_JOB.search(line)
            if m:
                name = m.group(1)
                t = P_TYPE.search(line)
                current = name
                jobs[name] = {
                    "name": name,
                    "job_type": t.group(1) if t else "",
                    "box_name": "", "command": "", "script": "",
                    "date_conditions": "", "condition": "", "start_times": "",
                    "run_calendar": "", "exclude_calendar": "", "machine": "", "alarm_if_fail": "",
                }
                continue
            if current is None:
                continue
            j = jobs[current]
            if line.startswith("box_name:"):
                mm = P_BOX.search(line); j["box_name"] = mm.group(1) if mm else ""
            elif line.startswith("command:"):
                mm = P_CMD.search(line)
                if mm:
                    cmd = mm.group(1).strip()
                    j["command"] = cmd
                    first = cmd.split()[0] if cmd.split() else cmd
                    j["script"] = os.path.basename(first) if ("/" in first or "\\" in first) else "cmd"
            elif line.startswith("date_conditions:"):
                mm = P_DATE.search(line); j["date_conditions"] = mm.group(1) if mm else ""
            elif line.startswith("condition:"):
                mm = P_COND.search(line); j["condition"] = mm.group(1).strip() if mm else ""
            elif line.startswith("start_times:"):
                mm = P_START.search(line); j["start_times"] = mm.group(1).strip() if mm else ""
            elif line.startswith("run_calendar:"):
                mm = P_RUNCAL.search(line); j["run_calendar"] = mm.group(1) if mm else ""
            elif line.startswith("exclude_calendar:"):
                mm = P_EXCAL.search(line); j["exclude_calendar"] = mm.group(1) if mm else ""
            elif line.startswith("machine:"):
                mm = P_MACHINE.search(line); j["machine"] = mm.group(1) if mm else ""
            elif line.startswith("alarm_if_fail:"):
                mm = P_ALARM.search(line); j["alarm_if_fail"] = mm.group(1) if mm else ""
    return jobs


def write_csv(jobs, out_path):
    headers = [
        "Job Name", "Job Type", "Box Name", "Category", "Script Name", "Command",
        "date_conditions", "condition (dependency)", "start_times",
        "run_calendar", "exclude_calendar", "machine", "alarm_if_fail",
        "Target Platform", "Migration Rationale",
    ]
    cats, targets = {}, {}
    # newline="" prevents blank rows in Excel on Windows
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for j in jobs.values():
            if j["job_type"] == "BOX":
                category = "BOX (container)"
                target, rationale = ("Argo Workflow (DAG)", "BOX maps to workflow orchestration")
            else:
                category = classify_job(j["name"], j["command"])
                target, rationale = target_platform(
                    category, j["date_conditions"], j["start_times"], j["condition"], j["box_name"]
                )
            cats[category] = cats.get(category, 0) + 1
            targets[target] = targets.get(target, 0) + 1
            w.writerow([
                j["name"], j["job_type"], j["box_name"], category, j["script"], j["command"],
                j["date_conditions"], j["condition"], j["start_times"],
                j["run_calendar"], j["exclude_calendar"], j["machine"], j["alarm_if_fail"],
                target, rationale,
            ])

    # Summary CSV
    summary_path = os.path.splitext(out_path)[0] + "_summary.csv"
    total = len(jobs)
    box = sum(1 for j in jobs.values() if j["job_type"] == "BOX")
    cmd = sum(1 for j in jobs.values() if j["job_type"] == "CMD")
    with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Metric", "Count"])
        w.writerow(["Total Jobs", total])
        w.writerow(["BOX Jobs", box])
        w.writerow(["CMD Jobs", cmd])
        w.writerow([])
        w.writerow(["Category", "Count"])
        for k, v in sorted(cats.items(), key=lambda x: -x[1]):
            w.writerow([k, v])
        w.writerow([])
        w.writerow(["Target Platform", "Count"])
        for k, v in sorted(targets.items(), key=lambda x: -x[1]):
            w.writerow([k, v])

    print(f"Detail CSV : {out_path}  ({total} jobs)")
    print(f"Summary CSV: {summary_path}")


def main():
    if len(sys.argv) < 2:
        print('Usage: python jil_csv_creator.py <input.jil> [output.csv]')
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(inp)[0] + "_output.csv"
    if not out.lower().endswith(".csv"):
        out = os.path.splitext(out)[0] + ".csv"
    jobs = parse_jil(inp)
    write_csv(jobs, out)


if __name__ == "__main__":
    main()
