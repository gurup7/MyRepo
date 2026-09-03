#!/usr/bin/env python3
"""
JIL Excel Creator — Python equivalent of JobExcelCreator.java

SAME LOGIC as the Java version:
- Groups jobs by suffix (job name with leading numeric prefix stripped)
- Parses: insert_job, job_type, command, date_conditions, box_name
- Target classification: date_conditions=1 → "Openshift Jobs (Fixed Scheduled Time)"
                         date_conditions=0 → "Autosys (No Scheduled Time)"
- Produces the SAME 8 columns in the SAME order as the Java output

Usage:
    python jil_excel_creator_v2.py <input_jil_file> [output_csv_file]

Examples:
    python jil_excel_creator_v2.py HK_CA_UAT2.txt
    python jil_excel_creator_v2.py HK_CA_UAT2.txt HK_CA_UAT2_output.csv
    python jil_excel_creator_v2.py "150043_LINUX_JILS 1.txt" autosys_output.csv

Output:
    CSV file with 8 columns (opens directly in Excel):
    Job Name | Job Type | Box Name | Count | List of Jobs | Script Name | Target Job Type | Command

Zero external dependencies — uses only Python built-in modules (re, csv, sys, os).
No pip install needed. No Maven build. No test case required.
"""

import re
import sys
import os
import csv
from collections import OrderedDict

# --- Regex patterns ---
P_JOB      = re.compile(r"insert_job:\s*(\S+)")
P_TYPE     = re.compile(r"job_type:\s*(\S+)")
P_COMMAND  = re.compile(r"command:\s*(.+)")   # capture the FULL command line, not just first token
P_DATECOND = re.compile(r"date_conditions:\s*(\S+)")
P_BOXNAME  = re.compile(r"box_name:\s*(\S+)")

# Known shell interpreters/wrappers to skip when locating the real script name
_INTERPRETERS = {"sh", "bash", "ksh", "csh", "zsh", "perl", "python", "python3",
                 "sudo", "nohup", "time", "exec", ".", "source", "env"}


def extract_script_name(full_command):
    """
    Given a full command line, return the actual script name.
    Handles:
      - 'sh /path/to/script.sh ARG'      -> script.sh
      - 'bash /path/to/x.ksh a b c'      -> x.ksh
      - '/path/to/script.ksh HKG'        -> script.ksh
      - 'sudo -u user /path/run.sh'      -> run.sh
      - inline command with no script    -> 'cmd'
    """
    if not full_command:
        return "cmd"

    tokens = full_command.split()

    # 1) Prefer the first token that looks like a script file (.sh/.ksh/.pl/.py/.bat)
    for tok in tokens:
        # strip trailing punctuation that sometimes clings to paths
        candidate = tok.strip().strip('"').strip("'")
        low = candidate.lower()
        if (low.endswith(".sh") or low.endswith(".ksh") or low.endswith(".pl")
                or low.endswith(".py") or low.endswith(".bat") or low.endswith(".cmd")
                or low.endswith(".ps1")):
            return os.path.basename(candidate)

    # 2) No recognizable script extension. Take the first non-interpreter,
    #    non-flag token as the executable name.
    for tok in tokens:
        t = tok.strip().strip('"').strip("'")
        base = os.path.basename(t).lower()
        if base in _INTERPRETERS:
            continue
        if t.startswith("-"):   # skip flags like -u, -c
            continue
        return os.path.basename(t)

    # 3) Fallback
    return "cmd"


def read_text_file(file_name):
    """
    Parse JIL file — EXACT same logic as Java's readTextFile().
    Groups jobs by suffix (job name with leading digits stripped).
    Returns OrderedDict of suffix → {jobType, count, jobList, command, scriptName, targetJobType, boxName}
    """
    job_map = OrderedDict()
    prev_job_suffix = ""

    with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            # Skip irrelevant lines (same filter as Java)
            if not (line.startswith("insert_job:") or line.startswith("command:")
                    or line.startswith("date_conditions:") or line.startswith("box_name:")):
                continue

            if line.startswith("insert_job:"):
                job_match = P_JOB.search(line)
                type_match = P_TYPE.search(line)
                if job_match and type_match:
                    full_job_name = job_match.group(1)    # e.g., 123456_rt_finish
                    job_type = type_match.group(1)         # e.g., CMD

                    # Extract suffix after numeric prefix (same as Java: replaceFirst("^\\d+", ""))
                    job_suffix = re.sub(r"^\d+", "", full_job_name)  # e.g., _rt_finish

                    if job_suffix not in job_map:
                        job_map[job_suffix] = {
                            "jobType": "",
                            "count": 0,
                            "jobList": [],
                            "command": "",
                            "scriptName": "",
                            "targetJobType": "",
                            "boxName": "",
                        }

                    info = job_map[job_suffix]
                    info["jobType"] = job_type
                    info["count"] += 1
                    info["jobList"].append(full_job_name)
                    prev_job_suffix = job_suffix

            elif line.startswith("command:"):
                if prev_job_suffix not in job_map:
                    continue
                job_info = job_map[prev_job_suffix]

                cmd_match = P_COMMAND.search(line)
                if cmd_match:
                    # Full command line (everything after "command:"), trimmed
                    command = cmd_match.group(1).strip()
                else:
                    command = ""

                # Derive the real script name, skipping interpreters (sh/bash/ksh...)
                script_name = extract_script_name(command)

                job_info["command"] = command
                job_info["scriptName"] = script_name

            elif line.startswith("date_conditions:"):
                if prev_job_suffix not in job_map:
                    continue
                job_info = job_map[prev_job_suffix]

                dc_match = P_DATECOND.search(line)
                if dc_match:
                    date_condition = int(dc_match.group(1))
                    # SAME logic as Java: 1 → OpenShift, 0 → Autosys
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

    return job_map


def write_to_csv(job_data, output_file):
    """
    Write CSV with the SAME 8 columns as the Java Excel output.
    CSV opens directly in Excel without any library.
    """
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # Header — same 8 columns as Java version
        writer.writerow([
            "Job Name",
            "Job Type",
            "Box Name",
            "Count",
            "List of Jobs",
            "Script Name",
            "Target Job Type",
            "Command",
        ])

        # Data rows
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
            ])

    print(f"CSV file created successfully: {output_file}  ({len(job_data)} unique job suffixes)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python jil_excel_creator_v2.py <input_jil_file> [output_csv_file]")
        print()
        print("Examples:")
        print('  python jil_excel_creator_v2.py HK_CA_UAT2.txt')
        print('  python jil_excel_creator_v2.py HK_CA_UAT2.txt output.csv')
        print('  python jil_excel_creator_v2.py "150043_LINUX_JILS 1.txt" autosys.csv')
        sys.exit(1)

    input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        if not output_file.lower().endswith(".csv"):
            output_file = os.path.splitext(output_file)[0] + ".csv"
    else:
        output_file = os.path.splitext(input_file)[0] + "_output.csv"

    # Parse
    job_data = read_text_file(input_file)

    # Write
    write_to_csv(job_data, output_file)


if __name__ == "__main__":
    main()
