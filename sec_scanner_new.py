"""
Secrets Scanner — Detects hardcoded credentials and sensitive variable names.

Based on Citi Checkmarx "Plaintext Storage of Sensitive Information" detection rules.
Scans: *.properties, *.yml, *.yaml, *.xml, *.sh, Dockerfile, docker-compose*
Excludes: *.java files (method/variable names are false positives in Java source)

Focuses only on HIGH and CRITICAL severity findings.

Usage:
    python secrets_scanner.py C:\\path\\to\\repo
    python secrets_scanner.py                      (scans current directory)

Output:
    - Console summary (HIGH + CRITICAL only)
    - CSV report auto-generated: secrets_scan_report_<repo_name>.csv
"""

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

# ============================================================================
# CONFIGURATION
# ============================================================================

# File patterns to scan (Java excluded — causes false positives)
SCAN_PATTERNS = [
    "*.properties",
    "*.yml",
    "*.yaml",
    "*.xml",
    "*.sh",
    "Dockerfile",
    "docker-compose*.yml",
    "docker-compose*.yaml",
]

# Directories to skip
EXCLUDE_DIRS = {
    ".git", "target", "build", "node_modules",
    ".mvn", ".gradle", ".idea", "bin", "obj", "__pycache__",
}

# Sensitive keywords in variable names (Checkmarx triggers)
SENSITIVE_KEYWORDS = [
    "SECRET", "ACCESSKEY", "ACCESS_KEY",
    "PASSWORD", "PASSWD", "TOKEN",
    "CREDENTIAL", "PRIVATE_KEY",
]

# ============================================================================
# DETECTION RULES
# ============================================================================

@dataclass
class Finding:
    file: str
    line: int
    finding_type: str
    severity: str
    matched_text: str
    description: str
    remediation: str


def build_sensitive_varname_pattern():
    keywords = "|".join(SENSITIVE_KEYWORDS)
    return re.compile(rf'\b\w*({keywords})\w*\b', re.IGNORECASE)


PATTERNS = {
    "uuid_secret": {
        "regex": re.compile(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            re.IGNORECASE
        ),
        "type": "HARDCODED_SECRET",
        "severity": "CRITICAL",
        "description": "UUID-format value — potential access key or secret",
        "remediation": "Replace with NGC (CyberArk) secret nickname",
    },
    "aws_key": {
        "regex": re.compile(r'(AKIA|ASIA)[A-Z0-9]{16}'),
        "type": "HARDCODED_SECRET",
        "severity": "CRITICAL",
        "description": "AWS access key pattern detected",
        "remediation": "Remove immediately. Use IAM roles or vault integration",
    },
    "private_key": {
        "regex": re.compile(r'-----BEGIN\s+(RSA\s+|EC\s+|DSA\s+)?PRIVATE KEY-----'),
        "type": "HARDCODED_SECRET",
        "severity": "CRITICAL",
        "description": "Private key embedded in source file",
        "remediation": "Move to secure vault. Never store private keys in source control",
    },
    "password_value": {
        "regex": re.compile(
            r'(password|passwd|pwd)\s*[:=]\s*[^\s${}\[\]#\"\']{4,}',
            re.IGNORECASE
        ),
        "type": "HARDCODED_SECRET",
        "severity": "CRITICAL",
        "description": "Hardcoded password value in configuration",
        "remediation": "Replace with ${ENV_VAR} placeholder or NGC nickname",
    },
    "connection_string": {
        "regex": re.compile(
            r'(jdbc|mongodb|mongodb\+srv|amqp|redis|mysql|postgresql):\/\/[^:]+:[^@\s]+@',
            re.IGNORECASE
        ),
        "type": "HARDCODED_SECRET",
        "severity": "CRITICAL",
        "description": "Connection string with embedded credentials",
        "remediation": "Separate credential from URL. Use spring.datasource.password with vault",
    },
    "base64_secret": {
        "regex": re.compile(r'[A-Za-z0-9+/]{40,}={0,2}'),
        "type": "HARDCODED_SECRET",
        "severity": "HIGH",
        "description": "Long Base64-encoded string — potential encoded secret",
        "remediation": "Verify if this is a credential. If yes, move to vault",
    },
    "sensitive_varname": {
        "regex": build_sensitive_varname_pattern(),
        "type": "SENSITIVE_VARNAME",
        "severity": "HIGH",
        "description": "Variable name contains sensitive keyword (Checkmarx trigger)",
        "remediation": "Rename variable to remove sensitive keyword (see rename table)",
    },
    "direct_injection": {
        "regex": re.compile(
            r'value:\s*\{\{\s*\.Values\.\w*(SECRET|ACCESSKEY|PASSWORD|TOKEN)\w*\s*\}\}',
            re.IGNORECASE
        ),
        "type": "DIRECT_INJECTION",
        "severity": "HIGH",
        "description": "Secret injected directly as env var in deployment manifest",
        "remediation": "Pass NGC nickname only. Resolve actual secret at runtime via O2C sidecar",
    },
}

# ============================================================================
# FALSE POSITIVE FILTERS
# ============================================================================

COMMENT_PATTERNS = [
    re.compile(r'^\s*#'),
    re.compile(r'^\s*//'),
    re.compile(r'^\s*\*'),
    re.compile(r'^\s*/\*'),
    re.compile(r'^\s*<!--'),
]

FALSE_POSITIVE_PATTERNS = [
    re.compile(r'NGC.*nickname', re.IGNORECASE),
    re.compile(r'CUR_\d+_\w+_\w+'),
    re.compile(r'ngc\s+getSecret', re.IGNORECASE),
    re.compile(r'\$\{[^}]*:-}'),
    re.compile(r'secretNickname'),
]


def is_comment(line: str) -> bool:
    return any(p.match(line) for p in COMMENT_PATTERNS)


def is_false_positive(line: str) -> bool:
    return any(p.search(line) for p in FALSE_POSITIVE_PATTERNS)


# ============================================================================
# SCANNER
# ============================================================================

def should_scan_file(filepath: Path) -> bool:
    parts = filepath.parts
    if any(excluded in parts for excluded in EXCLUDE_DIRS):
        return False

    name = filepath.name
    for pattern in SCAN_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif "*" in pattern:
            prefix, suffix = pattern.split("*", 1)
            if name.startswith(prefix) and name.endswith(suffix):
                return True
        else:
            if name == pattern:
                return True
    return False


def scan_file(filepath: Path, repo_root: Path) -> List[Finding]:
    findings = []
    relative_path = str(filepath.relative_to(repo_root))

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except (IOError, OSError):
        return findings

    for line_num, line in enumerate(lines, start=1):
        if is_comment(line):
            continue
        if is_false_positive(line):
            continue

        for rule_name, rule in PATTERNS.items():
            matches = rule["regex"].finditer(line)
            for match in matches:
                matched_text = match.group(0).strip()

                if len(matched_text) < 4:
                    continue

                # Skip base64 false positives (XML namespaces, class paths)
                if rule_name == "base64_secret":
                    if "." in matched_text and "/" not in matched_text:
                        continue
                    if "xmlns" in line or "xsi:" in line:
                        continue

                severity = rule["severity"]

                # Only include HIGH and CRITICAL
                if severity not in ("HIGH", "CRITICAL"):
                    continue

                finding = Finding(
                    file=relative_path,
                    line=line_num,
                    finding_type=rule["type"],
                    severity=severity,
                    matched_text=matched_text[:80],
                    description=rule["description"],
                    remediation=rule["remediation"],
                )
                findings.append(finding)

    return findings


def scan_repository(repo_path: str) -> List[Finding]:
    repo_root = Path(repo_path).resolve()
    if not repo_root.is_dir():
        print(f"ERROR: {repo_path} is not a valid directory")
        sys.exit(1)

    all_findings = []
    files_scanned = 0

    for filepath in repo_root.rglob("*"):
        if filepath.is_file() and should_scan_file(filepath):
            files_scanned += 1
            findings = scan_file(filepath, repo_root)
            all_findings.extend(findings)

    print(f"\nScanned {files_scanned} files in {repo_root}")
    return all_findings


# ============================================================================
# REPORTING
# ============================================================================

def print_summary(findings: List[Finding]):
    if not findings:
        print("\n✓ No HIGH/CRITICAL secrets or sensitive variable names detected.")
        return

    severity_counts = {"CRITICAL": 0, "HIGH": 0}
    type_counts = {}
    file_counts = {}

    for f in findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
        type_counts[f.finding_type] = type_counts.get(f.finding_type, 0) + 1
        file_counts[f.file] = file_counts.get(f.file, 0) + 1

    print("\n" + "=" * 70)
    print("SECRETS SCAN REPORT (HIGH + CRITICAL ONLY)")
    print("=" * 70)

    print(f"\nTotal Findings: {len(findings)}")
    print(f"  CRITICAL: {severity_counts.get('CRITICAL', 0)}")
    print(f"  HIGH:     {severity_counts.get('HIGH', 0)}")

    print(f"\nBy Type:")
    for ftype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {ftype}: {count}")

    print(f"\nFiles with findings: {len(file_counts)}")
    for fpath, count in sorted(file_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {fpath}: {count} finding(s)")

    print("\n" + "-" * 70)
    print("DETAILED FINDINGS")
    print("-" * 70)

    for severity in ["CRITICAL", "HIGH"]:
        sev_findings = [f for f in findings if f.severity == severity]
        if not sev_findings:
            continue

        print(f"\n[{severity}] — {len(sev_findings)} findings\n")
        for f in sev_findings:
            print(f"  File: {f.file}:{f.line}")
            print(f"  Type: {f.finding_type}")
            print(f"  Match: {f.matched_text}")
            print(f"  Issue: {f.description}")
            print(f"  Fix: {f.remediation}")
            print()


def export_csv(findings: List[Finding], output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "File", "Line", "Type", "Severity",
            "Matched Text", "Description", "Remediation"
        ])
        for f in findings:
            writer.writerow([
                f.file, f.line, f.finding_type, f.severity,
                f.matched_text, f.description, f.remediation
            ])
    print(f"\nCSV report exported to: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Scan repository for hardcoded secrets (HIGH + CRITICAL only, excludes Java files)"
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the Git repository to scan (defaults to current directory)"
    )

    args = parser.parse_args()
    repo_path = os.path.abspath(args.repo_path)
    repo_name = os.path.basename(repo_path)

    # Run scan
    findings = scan_repository(repo_path)

    # Print summary to console
    print_summary(findings)

    # Always generate CSV report
    output_file = f"secrets_scan_report_{repo_name}.csv"
    export_csv(findings, output_file)

    # Exit code for CI/CD
    critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
    if critical_count > 0:
        print(f"\n✗ FAILED: {critical_count} CRITICAL finding(s). Secrets must be remediated.")
        sys.exit(1)
    elif findings:
        print(f"\n⚠ WARNING: {len(findings)} HIGH finding(s) detected. Review recommended.")
        sys.exit(0)
    else:
        print("\n✓ PASSED: No findings.")
        sys.exit(0)


if __name__ == "__main__":
    main()
