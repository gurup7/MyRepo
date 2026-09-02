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


def target_platform(category, date_condition, start_times, condition, box_name, command, machine):
    """
    4-category target model (top-down, first match wins). Returns (target, justification).
    Targets:
      1. ELIMINATED
      2. Autosys Only
      3. OpenShift Job        (on-demand / dependency-triggered)
      4. OpenShift CronJob    (scheduled; covers native CronJob or Argo CronWorkflow)
    """
    cmd_u = (command or "").upper()

    # --- 1. ELIMINATED: lifecycle jobs the platform handles natively ---
    if category in ("Server Start", "Server Stop", "NGINX/Web Start", "NGINX/Web Stop"):
        return ("ELIMINATED",
                "App/web server lifecycle is managed natively by OpenShift Deployments, "
                "ReplicaSets and health probes; explicit start/stop jobs are not required.")
    if category == "Sleep/Wait":
        return ("ELIMINATED",
                "Sleep/wait steps are replaced by Kubernetes readiness/liveness probes; "
                "no explicit delay job is needed.")

    # --- 2. Autosys Only: jobs that cannot/should not move (on-prem coupled) ---
    # NDM transfers to on-prem systems that stay on VM, or jobs bound to non-containerized infra.
    if category == "NDM File Transfer" or "NDM" in cmd_u:
        return ("Autosys Only",
                "Depends on NDM which remains on-premise (VM); transfer is tightly coupled to "
                "on-prem connectivity. Recommend retaining on Autosys until an SFTP bridge is "
                "validated, then re-evaluate for OpenShift.")

    # --- 4. OpenShift CronJob: has its own recurring schedule ---
    if start_times:
        return ("OpenShift CronJob",
                f"Has an independent time schedule (start_times={start_times}); maps to a "
                "recurring OpenShift CronJob (or Argo CronWorkflow if it has internal dependencies).")
    if str(date_condition) == "1" and not box_name:
        return ("OpenShift CronJob",
                "date_conditions=1 indicates an independent date/time trigger; runs on a recurring "
                "schedule, so it maps to an OpenShift CronJob.")

    # --- 3. OpenShift Job: on-demand or dependency/BOX-triggered ---
    if condition:
        return ("OpenShift Job",
                f"Triggered by a dependency (condition={condition}), not by the clock. Runs once when "
                "its predecessor completes; maps to an on-demand OpenShift Job orchestrated by the workflow.")
    if box_name:
        return ("OpenShift Job",
                "date_conditions=0 and triggered by its parent BOX; runs once when the BOX starts. "
                "Maps to an on-demand OpenShift Job as a workflow task.")
    return ("OpenShift Job",
            "On-demand / event-triggered job with no independent schedule; maps to an OpenShift Job "
            "invoked when required.")


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
        "Target Platform", "Justification",
    ]
    cats, targets = {}, {}
    # newline="" prevents blank rows in Excel on Windows
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for j in jobs.values():
            if j["job_type"] == "BOX":
                category = "BOX (container)"
                target, rationale = (
                    "OpenShift Job",
                    "BOX is an orchestration container; its child jobs are scheduled/triggered "
                    "individually. The BOX itself maps to the workflow that groups those OpenShift Jobs.",
                )
            else:
                category = classify_job(j["name"], j["command"])
                target, rationale = target_platform(
                    category, j["date_conditions"], j["start_times"], j["condition"],
                    j["box_name"], j["command"], j["machine"],
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
        # Fixed 4-category order so every bucket is always visible
        for k in ["ELIMINATED", "Autosys Only", "OpenShift Job", "OpenShift CronJob"]:
            w.writerow([k, targets.get(k, 0)])
        # any other target that appears (safety net)
        for k, v in sorted(targets.items(), key=lambda x: -x[1]):
            if k not in ("ELIMINATED", "Autosys Only", "OpenShift Job", "OpenShift CronJob"):
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
