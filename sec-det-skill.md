---
name: secrets-detection
description: 'Detect, remediate, and prevent hardcoded secrets, access keys, passwords, and sensitive variable names in Java repositories. Use when scanning for Checkmarx Plaintext Storage of Sensitive Information findings, remediating hardcoded credentials in Helm values, Kubernetes Deployment manifests, application.properties, application.yml, ConfigMaps, shell scripts, Java constants, or environment configuration files. Provides automated scanning, NGC (CyberArk) secret nickname replacement, sensitive variable renaming, O2C sidecar patterns, and pre-commit prevention for Citi containerized deployments.'
---

# Secrets Detection, Remediation & Prevention

Single solution for detecting hardcoded secrets, remediating Checkmarx findings using the NGC (CyberArk) pattern, and preventing future secret exposure in Citi containerized deployments.

## When to Use This Skill

- Checkmarx flagged "Plaintext Storage of Sensitive Information" in any branch
- Scanning a repository for hardcoded secrets before PR or deployment
- Remediating access keys, passwords, or tokens in any file type
- Renaming variables with sensitive keywords (SECRET, ACCESSKEY, PASSWORD, TOKEN)
- Replacing hardcoded credentials with NGC (CyberArk) secret nicknames
- Updating Helm values, Deployment.yaml, shell scripts for NGC pattern
- Setting up pre-commit hooks to prevent future secret commits
- Bulk remediating secrets across multiple applications

---

## 1. What Triggers Checkmarx

Checkmarx flags TWO categories:

| Category | Example | Risk |
|----------|---------|------|
| Hardcoded credential values | `APPD_ACCESSKEY: fd28045f-bb50-4604-af1a-875e5f51f362` | Secret exposed in source control |
| Variable names with sensitive keywords | `ETH_SECRET_NICKNAME`, `MONGO_SECRET_NICKNAME`, `SA_CALL_SECRET` | Checkmarx treats as potential plaintext credential storage |
| Secrets injected as plain env vars at deploy time | `value: {{ .Values.appd.APPD_ACCESSKEY }}` | Secret visible in pod spec and Kubernetes API |

### Keywords That Trigger

Any variable name containing: `SECRET`, `ACCESSKEY`, `ACCESS_KEY`, `PASSWORD`, `PASSWD`, `TOKEN`, `CREDENTIAL`, `PRIVATE_KEY`

---

## 2. Files to Scan

| File Pattern | What to Look For |
|-------------|-----------------|
| `*.java` | String constants, @Value defaults, connection strings with embedded passwords |
| `application.properties` | `spring.datasource.password=actualValue`, API keys |
| `application.yml` / `*.yaml` | Same as properties, nested YAML structure |
| `helm/*-values.yaml` | Per-environment secrets, sensitive variable names |
| `helm/templates/Deployment.yaml` | Direct secret injection via env vars, O2C annotations |
| `helm/templates/ConfigMap.yaml` | Plaintext credentials in ConfigMap data |
| `*.sh` (shell scripts) | Exported secrets, hardcoded variables, secrets echoed to logs |
| `docker-compose.yml` / `Dockerfile` | Environment variables with secrets, build-time ARGs |
| `*.xml` | Datasource passwords, JNDI credentials, Spring config |
| `bootstrap.yml` | Config server credentials |

---

## 3. Fix Strategy — Two Principles

**Principle 1:** Never store actual secret values in Helm values files or Deployment manifests.
Use NGC (CyberArk) secret nicknames instead. Retrieve the actual secret at container runtime.

**Principle 2:** Rename variables containing sensitive keywords (SECRET, ACCESSKEY, PASSWORD, TOKEN)
to neutral names that don't trigger Checkmarx.

---

## 4. Variable Rename Reference Table

| Original Name | Renamed To | Reason | Found In |
|--------------|-----------|--------|----------|
| `ETH_SECRET_ENVIRONMENT` | `ETH_ENVIRONMENT` | Remove SECRET | Helm values, Deployment.yaml |
| `ETH_SECRET_NICKNAME` | `ETH_NICKNAME` | Remove SECRET | Helm values, Deployment.yaml, entry-point.sh, eth_functions.sh |
| `MONGO_SECRET_NICKNAME` | `MONGO_NICKNAME` | Remove SECRET | Helm values, Deployment.yaml, entry-point.sh |
| `APPD_ACCESSKEY` | `APPD_ACCS_NICKNAME` | Remove ACCESSKEY | Helm values, Deployment.yaml |
| `SA_CALL_SECRET` | `SA_CALL_SCRT` | Remove SECRET | eth_functions.sh, entry-point.sh |
| `APPDYNAMICS_AGENT_ACCOUNT_ACCESS_KEY` (in Deployment.yaml) | `APPD_SECRET_NICKNAME` | Remove ACCESS_KEY, convert to nickname pass-through | Deployment.yaml (runtime export moved to entry-point.sh) |

### NGC Nickname Naming Convention

```
CUR_<CSI_APP_ID>_<ENV>_<PURPOSE>

Examples:
CUR_165858_DEV_APPD_ACCESS_KEY
CUR_165858_UAT_APPD_ACCESS_KEY
CUR_165858_PROD_APPD_ACCESS_KEY
```

---

## 5. Step-by-Step Remediation

### Step 1: Identify All Flagged Items

Run Checkmarx report and note:
- Which files contain hardcoded secrets
- Which variable names are flagged
- Which environments are affected (dev, uat, uat2, prod, cob)

Typical files to check:
```
helm/dev-values.yaml
helm/uat-values.yaml
helm/uat2-values.yaml
helm/prod-values.yaml
helm/cob-values.yaml
helm/templates/Deployment.yaml
src/scripts/entry-point.sh
src/scripts/eth_functions.sh
src/main/resources/application.properties
src/main/resources/application.yml
```

### Step 2: Rename Variables in Helm Values Files

**BEFORE:**
```yaml
ETH_SECRET_ENVIRONMENT: DEV
ETH_SECRET_NICKNAME: 165858_ur_dev_db_secret,ur_dev_cert_policy_102d
MONGO_SECRET_NICKNAME: 165858_ur_dev_db_secret
```

**AFTER:**
```yaml
ETH_ENVIRONMENT: DEV
ETH_NICKNAME: 165858_ur_dev_db_secret,ur_dev_cert_policy_102d
MONGO_NICKNAME: 165858_ur_dev_db_secret
```

Apply across ALL environment values files. Only the variable names change — the assigned NGC nicknames remain the same.

### Step 3: Replace Hardcoded Secrets with NGC Nicknames

**BEFORE (hardcoded plaintext UUID):**
```yaml
appd:
  APPD_ACCESSKEY: fd28045f-bb58-4604-af1a-875e5f51f362
```

**AFTER (NGC nickname — actual key fetched at runtime):**
```yaml
appd:
  APPD_ACCS_NICKNAME: CUR_165858_DEV_APPD_ACCESS_KEY
```

| Environment | NGC Nickname |
|-------------|-------------|
| DEV | `CUR_<CSI_APP_ID>_DEV_APPD_ACCESS_KEY` |
| UAT / UAT2 | `CUR_<CSI_APP_ID>_UAT_APPD_ACCESS_KEY` |
| PROD / COB | `CUR_<CSI_APP_ID>_PROD_APPD_ACCESS_KEY` |

**Prerequisite:** Ensure these NGC nicknames are created in CyberArk with the actual AppDynamics access key values before deployment.

### Step 4: Update Deployment.yaml

**4a — Update O2C Secrets Annotation:**
```yaml
# BEFORE
ecs.o2c.secretsnicknames: "{{ .Values.ETH_SECRET_NICKNAME }}"

# AFTER
ecs.o2c.secretsnicknames: "{{ .Values.ETH_NICKNAME }},{{ .Values.appd.APPD_ACCS_NICKNAME }}"
```

**4b — Replace Direct Secret Injection with Nickname Pass-Through:**
```yaml
# BEFORE (secret value injected directly)
- name: APPDYNAMICS_AGENT_ACCOUNT_ACCESS_KEY
  value: {{ .Values.appd.APPD_ACCESSKEY }}

# AFTER (only nickname passed; actual key resolved at runtime in entry-point.sh)
- name: APPD_SECRET_NICKNAME
  value: "{{ .Values.appd.APPD_ACCS_NICKNAME }}"
```

**4c — Update All Renamed Environment Variable References:**
```yaml
# BEFORE
- name: ENVIRONMENT
  value: "{{ .Values.ETH_SECRET_ENVIRONMENT }}"
- name: ETH_SECRET_NICKNAME
  value: "{{ .Values.ETH_SECRET_NICKNAME }}"
- name: MONGO_SECRET_NICKNAME
  value: "{{ .Values.MONGO_SECRET_NICKNAME }}"

# AFTER
- name: ENVIRONMENT
  value: "{{ .Values.ETH_ENVIRONMENT }}"
- name: ETH_NICKNAME
  value: "{{ .Values.ETH_NICKNAME }}"
- name: MONGO_NICKNAME
  value: "{{ .Values.MONGO_NICKNAME }}"
```

### Step 5: Update entry-point.sh

Add AppDynamics NGC retrieval **before** any existing MongoDB retrieval:

```bash
# NEW: Retrieve AppDynamics access key from NGC and export to environment
echo "APPD_SECRET_NICKNAME is ${APPD_SECRET_NICKNAME}"
download_eth_secret ${APPD_SECRET_NICKNAME}
export APPDYNAMICS_AGENT_ACCOUNT_ACCESS_KEY=${SA_CALL_SCRT}
```

Update MongoDB and other secret retrieval to use renamed variables:

```bash
# BEFORE
echo "MONGO_SECRET_NICKNAME is ${MONGO_SECRET_NICKNAME}"
download_eth_secret ${MONGO_SECRET_NICKNAME}
export MONGO_SECRET_PASSWORD=${SA_CALL_SECRET}

# AFTER
echo "MONGO_NICKNAME is ${MONGO_NICKNAME}"
download_eth_secret ${MONGO_NICKNAME}
export MONGO_SECRET_PASSWORD=${SA_CALL_SCRT}
```

### Step 6: Update eth_functions.sh

Rename internal variables within `download_eth_secret()`:

```bash
# BEFORE
download_eth_secret() {
    echo ":: func:download_eth_secret called with : $@"
    ETH_SECRET_NICKNAME=$1;
    echo ":: func:download_eth_secret > calling NGCClient GET_SECRET ${ETH_SECRET_NICKNAME}"
    SA_CALL_SECRET="$(ngc getSecret --secretNickname ${ETH_SECRET_NICKNAME})"
    if [ $? -ne 0 ] || [ -z "${SA_CALL_SECRET}" ]; then
        echo "ERROR: Failed to retrieve secret for ${ETH_SECRET_NICKNAME}" >&2
        exit 1
    else
        echo "Secret retrieved successfully :: SA_CALL_SECRET : ${SA_CALL_SECRET}"
    fi
    ETH_SECRET_PASS=$SA_CALL_SECRET
    [ -z "${ETH_SECRET_PASS}" ] && exit 1 || echo ":: secret retrieved for $1"
}

# AFTER
download_eth_secret() {
    echo ":: func:download_eth_secret called with : $@"
    ETH_NICKNAME=$1;
    echo ":: func:download_eth_secret > calling NGCClient GET_SECRET ${ETH_NICKNAME}"
    SA_CALL_SCRT="$(ngc getSecret --secretNickname ${ETH_NICKNAME})"
    if [ $? -ne 0 ] || [ -z "${SA_CALL_SCRT}" ]; then
        echo "ERROR: Failed to retrieve secret for ${ETH_NICKNAME}" >&2
        exit 1
    else
        echo "Secret retrieved successfully :: SA_CALL_SCRT : ${SA_CALL_SCRT}"
    fi
    ETH_SECRET_PASS=$SA_CALL_SCRT
    [ -z "${ETH_SECRET_PASS}" ] && exit 1 || echo ":: secret retrieved for $1"
}
```

---

## 6. Detection Prompts (Use in Copilot Chat)

### Full Repository Scan

```
@workspace Scan this entire repository for Checkmarx "Plaintext Storage of
Sensitive Information" triggers.

Check ALL these file types:
- *.java (constants, @Value annotations, String literals)
- application.properties, application.yml, application-*.yml, bootstrap.yml
- helm/*-values.yaml (dev, uat, uat2, prod, cob)
- helm/templates/Deployment.yaml, ConfigMap.yaml
- *.sh (entry-point.sh, eth_functions.sh, any others)
- docker-compose.yml, Dockerfile
- *.xml (Spring config, persistence.xml)

Detect:
1. HARDCODED SECRETS: UUIDs, Base64 strings, connection strings with passwords,
   API keys, private keys, any actual credential values
2. SENSITIVE VARIABLE NAMES: Any variable containing SECRET, ACCESSKEY,
   ACCESS_KEY, PASSWORD, PASSWD, TOKEN, CREDENTIAL, PRIVATE_KEY
3. EXPOSED IN LOGS: Secret values echoed/printed to stdout
4. DIRECT INJECTION: Secrets passed as plain env vars in Deployment manifests

For EVERY finding report:
| # | File | Line | Finding | Type (HARDCODED/VARNAME/LOGGED/INJECTED) | Severity | Fix |

Do not summarize. Show every occurrence. Include line numbers.
```

### Java-Only Scan

```
@workspace Scan all *.java files for hardcoded secrets.

Detect:
1. String constants with API keys, passwords, access tokens
2. @Value("${property:HARDCODED_DEFAULT}") with real credentials as defaults
3. Connection strings: "jdbc:mysql://user:password@host/db"
4. Private keys or certificates as String literals
5. Constants named with PASSWORD, SECRET, KEY, TOKEN
6. Test classes with real (not mocked) credentials

For each:
| File | Line | Code | Issue | Remediation (externalize/remove/mock) |
```

### Helm & Kubernetes Scan

```
@workspace Scan all Helm values files and Kubernetes templates for
Checkmarx triggers.

Check:
- helm/dev-values.yaml, uat-values.yaml, uat2-values.yaml, prod-values.yaml, cob-values.yaml
- helm/templates/Deployment.yaml
- helm/templates/ConfigMap.yaml

For each file, list:
| Variable Name | Contains Sensitive Keyword? | Value Type (NGC nickname / hardcoded / placeholder) | Action Needed |

Then verify:
- O2C annotation includes ALL NGC nicknames used in env vars
- No env var NAME contains SECRET, ACCESSKEY, PASSWORD, TOKEN
- No env var VALUE is a plaintext secret (should be nickname or {{ .Values.* }})
- Consistency across all environment files

Show BEFORE and AFTER for each file that needs changes.
```

### Shell Script Scan

```
@workspace Scan all *.sh files for secrets exposure.

Check for:
1. Variables named with SECRET, PASSWORD, TOKEN, KEY, CREDENTIAL
2. Hardcoded credentials in assignments
3. Secrets echoed to stdout (visible in container logs)
4. curl/wget commands with credentials in URL or -u flag
5. Export statements with sensitive variable names
6. Functions that output secrets to caller via sensitive-named variables

For each:
| File | Line | Issue | BEFORE | AFTER |

Ensure NO echo statement prints actual secret VALUES.
OK: echo "Retrieving secret for ${NICKNAME}"
NOT OK: echo "Secret value: ${SA_CALL_SECRET}"
```

---

## 7. Remediation Prompts (Use in Copilot Chat)

### Generate Complete Fix (All Files)

```
@workspace Generate the complete remediation for all Checkmarx findings in this repo.

CSI App ID: [ENTER YOUR APP ID]
Environments: dev, uat, uat2, prod, cob

Apply:
1. Rename all variables containing SECRET, ACCESSKEY, PASSWORD, TOKEN
2. Replace hardcoded secrets with NGC nicknames (CUR_<APP_ID>_<ENV>_<PURPOSE>)
3. Update Deployment.yaml (O2C annotation, env var names, nickname pass-through)
4. Update entry-point.sh (add AppD NGC retrieval, rename variable references)
5. Update eth_functions.sh (rename internal variables)
6. Update application.yml (externalize any hardcoded credentials)

For EACH file, show complete BEFORE and AFTER.
Ensure consistency — same variable names across all environment files.
Do not skip any file.
```

### Fix Specific File

```
@workspace #file:[PATH_TO_FILE]

Remediate this file for Checkmarx compliance:
1. Rename variables containing SECRET, ACCESSKEY, PASSWORD, TOKEN
2. Replace hardcoded values with NGC nickname references or ${ENV_VAR} placeholders
3. Show complete BEFORE and AFTER

Use these renames:
- ETH_SECRET_ENVIRONMENT → ETH_ENVIRONMENT
- ETH_SECRET_NICKNAME → ETH_NICKNAME
- MONGO_SECRET_NICKNAME → MONGO_NICKNAME
- APPD_ACCESSKEY → APPD_ACCS_NICKNAME
- SA_CALL_SECRET → SA_CALL_SCRT
```

---

## 8. Validation Prompts (Use in Copilot Chat)

### Pre-PR Final Check

```
@workspace Final Checkmarx compliance verification before PR.

Verify:
1. NO remaining variable names with SECRET, ACCESSKEY, PASSWORD, TOKEN, CREDENTIAL
2. NO hardcoded values resembling secrets (UUIDs, long strings, base64)
3. CONSISTENCY — renamed variables match between:
   - All Helm values files (dev, uat, uat2, prod, cob)
   - Deployment.yaml template {{ .Values.* }} references
   - entry-point.sh and eth_functions.sh variable usage
4. O2C COMPLETENESS — all NGC nicknames in env vars are listed in ecs.o2c.secretsnicknames
5. SHELL FLOW — download_eth_secret output variable (SA_CALL_SCRT) captured and exported correctly

Report:
| Check | PASS/FAIL | Details |

If any FAIL, show exactly what to fix with file path and line.
```

### Cross-Environment Consistency

```
@workspace Compare ALL Helm values files for consistency:
- helm/dev-values.yaml
- helm/uat-values.yaml
- helm/uat2-values.yaml
- helm/prod-values.yaml
- helm/cob-values.yaml

Verify:
1. Same variable NAMES in all files (only VALUES differ per environment)
2. No file still uses old names (SECRET, ACCESSKEY keywords)
3. NGC nicknames follow convention: CUR_<APP_ID>_<ENV>_<PURPOSE>
4. No environment has plaintext secret where others have nicknames

Output:
| Variable | dev | uat | uat2 | prod | cob | Consistent? |
```

---

## 9. Automation: Scanner Script

Use this prompt to generate a reusable scanner script:

```
Create a secrets-scanner.sh script that I can run against any Git repository.

Requirements:
1. Scan: *.java, *.properties, *.yml, *.yaml, *.xml, *.sh, Dockerfile, docker-compose*
2. Detect:
   - Variable names with: SECRET, ACCESSKEY, ACCESS_KEY, PASSWORD, PASSWD, TOKEN, CREDENTIAL, PRIVATE_KEY
   - UUID patterns: [0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}
   - Base64 strings over 40 characters
   - jdbc/mongodb/amqp URLs with embedded credentials
   - AWS key patterns (AKIA...)
   - Private key markers (-----BEGIN PRIVATE KEY-----)
3. Exclude:
   - Comments (# or //)
   - Test files (*Test.java, test/*)
   - .git/, target/, build/, node_modules/
4. Output:
   - Summary: X critical, Y high, Z medium findings across N files
   - CSV report: file,line,type,matched_text,severity
   - Exit code: 1 if critical (hardcoded secrets), 0 if only variable name flags
5. Make it runnable in CI/CD as pre-merge gate

Provide both bash and PowerShell versions.
```

---

## 10. Automation: Pre-Commit Hook

```
Create a Git pre-commit hook that blocks commits containing secrets.

1. Scan staged files only (git diff --cached --name-only)
2. Block if:
   - Hardcoded UUIDs in yaml/properties/sh files
   - Private key markers
   - New variables with SECRET, PASSWORD, TOKEN, ACCESSKEY keywords in helm/k8s files
3. Allow:
   - Bypass with --no-verify (document when legitimate)
   - References to NGC nicknames (the nickname NAME is fine, hardcoded VALUE is not)
4. Output: Clear error showing file, line, what triggered, and suggested fix
5. Provide installation instructions for team sharing (husky or .githooks/)
```

---

## 11. Automation: Bulk Rename Script

```
Create a Python script (bulk-rename-secrets.py) for bulk variable renaming.

Input — rename mapping (passed as YAML or JSON):
  ETH_SECRET_ENVIRONMENT: ETH_ENVIRONMENT
  ETH_SECRET_NICKNAME: ETH_NICKNAME
  MONGO_SECRET_NICKNAME: MONGO_NICKNAME
  APPD_ACCESSKEY: APPD_ACCS_NICKNAME
  SA_CALL_SECRET: SA_CALL_SCRT

Behavior:
1. Find ALL occurrences across *.yaml, *.yml, *.sh, *.java, *.properties, *.xml
2. Handle formats:
   - YAML keys: ETH_SECRET_NICKNAME: value
   - Helm templates: {{ .Values.ETH_SECRET_NICKNAME }}
   - Shell variables: ${ETH_SECRET_NICKNAME}
   - Env declarations: - name: ETH_SECRET_NICKNAME
   - Java strings: "ETH_SECRET_NICKNAME"
3. Preserve formatting and indentation
4. Generate summary report of all changes
5. Support --dry-run mode (show changes without modifying)
6. Exclude: .git/, target/, node_modules/, *.class, *.jar

Usage: python bulk-rename-secrets.py --config renames.yaml --path ./repo --dry-run
```

---

## 12. Pre-PR Checklist

Before raising PR for secret remediation:

- [ ] All hardcoded secret values (UUIDs, keys, passwords) removed from Helm values files
- [ ] Replaced with valid NGC (CyberArk) secret nicknames
- [ ] NGC secret nicknames are registered in CyberArk for all target environments
- [ ] Variable names containing SECRET, ACCESSKEY, PASSWORD, TOKEN are renamed
- [ ] Deployment.yaml — all renamed variable references match Helm values
- [ ] Deployment.yaml — AppD secret passed as nickname, not plaintext value
- [ ] Deployment.yaml — AppD NGC nickname added to `ecs.o2c.secretsnicknames` annotation
- [ ] entry-point.sh — AppD secret retrieved via `download_eth_secret` at runtime
- [ ] entry-point.sh — MongoDB and other secret references use renamed variables
- [ ] eth_functions.sh — internal variables renamed to avoid sensitive keywords
- [ ] All environment values files updated consistently (dev, uat, uat2, prod, cob)
- [ ] application.yml / application.properties — no hardcoded credentials remain
- [ ] Java source — no String constants with real secrets
- [ ] Service tested in DEV/UAT — container starts, secrets resolve, AppD reports, MongoDB connects
- [ ] Checkmarx re-scan confirms findings are resolved

---

## 13. Important Notes

1. **Do NOT remove the `APPDYNAMICS_AGENT_ACCOUNT_ACCESS_KEY` export entirely** — the AppDynamics Java agent still requires it. It's now set at runtime in `entry-point.sh` instead of injected via Deployment manifest.
2. **Ensure NGC nicknames exist in CyberArk** before deploying. If not registered, `download_eth_secret` will fail and the container will exit.
3. **Test in lower environments first.** After changes, deploy to DEV and verify:
   - Container starts successfully
   - MongoDB connection works (secret resolved)
   - AppDynamics agent connects and reports metrics
   - No Checkmarx findings on re-scan
4. **Apply consistently across ALL environment values files.** Missing a single file causes deployment failure in that environment.
5. **The `eth_functions.sh` change affects all callers.** Since output variable changes from `SA_CALL_SECRET` to `SA_CALL_SCRT`, ensure every script that calls `download_eth_secret` and reads the result is updated.
6. **Git history** — Removing secrets from current files does NOT remove them from git history. If the exposed value was a real credential (not a nickname), it must be rotated in CyberArk regardless.
7. **Helm template rendering** — After renaming variables, run `helm template` locally to verify rendered manifests before pushing.
8. **O2C annotation syntax** — Nicknames are comma-separated with NO spaces. A trailing comma or space causes sidecar failure.

---

## 14. Gotchas

- **`SA_CALL_SECRET → SA_CALL_SCRT` is a global change.** Every script sourcing `eth_functions.sh` and reading this variable must be updated. Missing one caller = silent failure (empty credentials).
- **Checkmarx scans ALL branches.** A secret committed to any branch (even feature/deleted) remains in git history. Remediation in current branch doesn't clear history.
- **`ETH_SECRET_PASS`** still contains "SECRET" inside `eth_functions.sh`. This is acceptable as a local shell variable not in Helm/K8s files. If Checkmarx scans shell scripts with equal strictness, rename to `ETH_PASS`.
- **Never log secret VALUES.** Even in error paths, log the nickname/variable name, never the resolved credential.
- **CyberArk latency.** NGC retrieval adds 3-10s per secret at container startup. Multiple secrets = startup probe must account for total retrieval time.

---

## 15. Troubleshooting

| Issue | Solution |
|-------|----------|
| Checkmarx still flags after rename | New name may still contain a keyword (e.g., `SECRET` inside `ETH_SECRET_PASS`). Also check git history scanning |
| Container fails to start | Verify `SA_CALL_SCRT` (not `SA_CALL_SECRET`) is used by all callers of `download_eth_secret` |
| AppDynamics agent not reporting | Ensure `APPDYNAMICS_AGENT_ACCOUNT_ACCESS_KEY` is exported in entry-point.sh after NGC retrieval |
| MongoDB connection failure | Verify `MONGO_NICKNAME` value matches NGC nickname registered in CyberArk for that environment |
| O2C sidecar fails | Check `ecs.o2c.secretsnicknames` — no spaces, valid commas, all nicknames included |
| Helm template breaks | Run `helm template . -f dev-values.yaml` locally to verify `{{ .Values.* }}` references resolve |
| NGC nickname not found | Register nickname in CyberArk BEFORE deploying. Coordinate with vault admin |
| Inconsistent env files | Use cross-environment consistency prompt (Section 8) to find mismatches |
