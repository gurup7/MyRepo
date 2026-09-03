#!/usr/bin/env python3
"""
JIL Excel Creator v4 — Auto-scan folder & consolidate multiple JIL files.

WHAT'S NEW IN v4 (over v2):
- Automatically picks up ALL JIL files in the folder (no need to pass a filename).
- Produces ONE consolidated CSV across all JIL files.
- Adds a "Source File" column so you can trace each job back to its JIL file.
- Still fixes the sh/bash/ksh script-name bug from v2.

HOW TO RUN (simplest):
    python jil_excel_creator_v4.py
        -> scans the CURRENT folder for *.txt and *.jil files
        -> writes  consolidated_jil_output.csv

OPTIONAL ARGUMENTS:
    python jil_excel_creator_v4.py <input_folder> <output_csv>
    python jil_excel_creator_v4.py C:\\autosys\\jils  consolidated.csv

Zero external dependencies — uses only Python built-in modules.
No pip install needed. No Maven. No proxy issues.
"""

import re
import sys
import os
import csv
import glob
from collections import OrderedDict

# --- Regex patterns ---
P_JOB      = re.compile(r"insert_job:\s*(\S+)")
P_TYPE     = re.compile(r"job_type:\s*(\S+)")
P_COMMAND  = re.compile(r"command:\s*(.+)")   # full command line
P_DATECOND = re.compile(r"date_conditions:\s*(\S+)")
P_BOXNAME  = re.compile(r"box_name:\s*(\S+)")

# File extensions treated as JIL files when scanning a folder
JIL_EXTENSIONS = ("*.txt", "*.jil", "*.JIL", "*.TXT")

# Known shell interpreters/wrappers to skip when locating the real script name
_INTERPRETERS = {"sh", "bash", "ksh", "csh", "zsh", "perl", "python", "python3",
                 "sudo", "nohup", "time", "exec", ".", "source", "env"}


def extract_script_name(full_command):
    """Return the actual script name, skipping interpreters (sh/bash/ksh) and flags."""
    if not full_command:
        return "cmd"

    tokens = full_command.split()

    # 1) Prefer the first token that looks like a script file
    for tok in tokens:
        candidate = tok.strip().strip('"').strip("'")
        low = candidate.lower()
        if (low.endswith(".sh") or low.endswith(".ksh") or low.endswith(".pl")
                or low.endswith(".py") or low.endswith(".bat") or low.endswith(".cmd")
                or low.endswith(".ps1")):
            return os.path.basename(candidate)

    # 2) No script extension -> first non-interpreter, non-flag token
    for tok in tokens:
        t = tok.strip().strip('"').strip("'")
        base = os.path.basename(t).lower()
        if base in _INTERPRETERS:
            continue
        if t.startswith("-"):
            continue
        return os.path.basename(t)

    # 3) Fallback
    return "cmd"


def parse_jil_file(file_name, job_map, source_label):
    """
    Parse a single JIL file into the shared job_map (keyed by suffix).
    Same logic as v2. Records the source file for traceability.
    Jobs with the same suffix across files are merged (count accumulates,
    job names appended, source files combined).
    """
    prev_job_suffix = ""

    with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not (line.startswith("insert_job:") or line.startswith("command:")
                    or line.startswith("date_conditions:") or line.startswith("box_name:")):
                continue

            if line.startswith("insert_job:"):
                job_match = P_JOB.search(line)
                type_match = P_TYPE.search(line)
                if job_match and type_match:
                    full_job_name = job_match.group(1)
                    job_type = type_match.group(1)
                    job_suffix = re.sub(r"^\d+", "", full_job_name)  # strip numeric prefix

                    if job_suffix not in job_map:
                        job_map[job_suffix] = {
                            "jobType": "",
                            "count": 0,
                            "jobList": [],
                            "command": "",
                            "scriptName": "",
                            "targetJobType": "",
                            "boxName": "",
                            "sourceFiles": [],
                        }

                    info = job_map[job_suffix]
                    info["jobType"] = job_type
                    info["count"] += 1
                    info["jobList"].append(full_job_name)
                    if source_label not in info["sourceFiles"]:
                        info["sourceFiles"].append(source_label)
                    prev_job_suffix = job_suffix

            elif line.startswith("command:"):
                if prev_job_suffix not in job_map:
                    continue
                job_info = job_map[prev_job_suffix]
                cmd_match = P_COMMAND.search(line)
                command = cmd_match.group(1).strip() if cmd_match else ""
                job_info["command"] = command
                job_info["scriptName"] = extract_script_name(command)

            elif line.startswith("date_conditions:"):
                if prev_job_suffix not in job_map:
                    continue
                job_info = job_map[prev_job_suffix]
                dc_match = P_DATECOND.search(line)
                if dc_match:
                    date_condition = int(dc_match.group(1))
                    if date_condition == 1:
                        job_info["targetJobType"] = "Openshift Jobs (Fixed Scheduled Time)"
                    else:
                        job_info["targetJobType"] = "Autosys (No Scheduled Time)"

            elif line.startswith("box_name:"):
                if prev_job_suffix not in job_map:
                    continue
                job_info = job_map[prev_job_suffix]
                box_match = P_BOXNAME.search(line)
                if box_match:
                    job_info["boxName"] = box_match.group(1)


def find_jil_files(folder, script_own_name):
    """Return sorted list of JIL files in the folder, excluding this script and any CSVs."""
    files = []
    for pattern in JIL_EXTENSIONS:
        files.extend(glob.glob(os.path.join(folder, pattern)))
    # De-duplicate (case-insensitive globs may overlap) and exclude non-JIL artifacts
    seen = set()
    result = []
    for fp in files:
        real = os.path.abspath(fp)
        base = os.path.basename(fp).lower()
        if real in seen:
            continue
        seen.add(real)
        if base == script_own_name.lower():      # don't parse this script itself
            continue
        if base.endswith(".csv"):                 # never treat output as input
            continue
        result.append(fp)
    return sorted(result)


def write_consolidated_csv(job_data, output_file):
    """Write ONE consolidated CSV with a Source File column."""
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Job Name",
            "Job Type",
            "Box Name",
            "Count",
            "List of Jobs",
            "Script Name",
            "Target Job Type",
            "Command",
            "Source File(s)",
        ])
        for job_suffix, info in job_data.items():
            writer.writerow([
                job_suffix,
                info["jobType"],
                info["boxName"],
                info["count"],
                ", ".join(info["jobList"]),
                info["scriptName"],
                info["targetJobType"],
                info["command"],
                ", ".join(info["sourceFiles"]),
            ])


def main():
    script_own_name = os.path.basename(__file__)

    # Args: [folder] [output_csv]  — both optional
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "consolidated_jil_output.csv"
    if not output_file.lower().endswith(".csv"):
        output_file = os.path.splitext(output_file)[0] + ".csv"

    if not os.path.isdir(folder):
        print(f"ERROR: '{folder}' is not a folder. Pass a folder path, or run with no args to scan the current folder.")
        sys.exit(1)

    jil_files = find_jil_files(folder, script_own_name)

    if not jil_files:
        print(f"No JIL files (*.txt / *.jil) found in: {os.path.abspath(folder)}")
        sys.exit(1)

    print(f"Scanning folder: {os.path.abspath(folder)}")
    print(f"Found {len(jil_files)} JIL file(s):")
    for fp in jil_files:
        print(f"   - {os.path.basename(fp)}")

    # Consolidate all files into one job_map
    job_map = OrderedDict()
    for fp in jil_files:
        parse_jil_file(fp, job_map, os.path.basename(fp))

    write_consolidated_csv(job_map, output_file)

    print()
    print(f"Consolidated CSV created: {os.path.abspath(output_file)}")
    print(f"Total unique job suffixes: {len(job_map)}")
    total_jobs = sum(info["count"] for info in job_map.values())
    print(f"Total job instances across all files: {total_jobs}")


if __name__ == "__main__":
    main()
