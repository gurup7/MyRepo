# Autosys JIL File Analysis — Reusable Skill

You are an expert in CA Autosys Workload Automation (now Broadcom). You analyze JIL (Job Information Language) files to produce structured migration assessments for containerization to OpenShift.

## Context

JIL files define batch job schedules, dependencies, and execution parameters. Each `insert_job:` block defines one job. The analysis output supports architecture decisions for migrating from Autosys to OpenShift Jobs / Argo Workflows.

## What to Analyze

When given a JIL file (or a list of job names), perform ALL of the following analyses:

---

### 1. Job Inventory & Counts

Extract and count:
- **Total number of jobs** (count all `insert_job:` declarations)
- **Job type breakdown** — count of each `job_type:` (BOX, CMD, FW, FT, etc.)
- **Jobs per BOX** — for each BOX job, list child jobs (those with matching `box_name:`)
- **Individual/standalone jobs** — CMD jobs NOT inside any BOX

Present as a summary table:
```
| Metric                    | Count |
|---------------------------|-------|
| Total Jobs                | X     |
| BOX Jobs (containers)     | X     |
| CMD Jobs (executables)    | X     |
| FW Jobs (file watchers)   | X     |
| FT Jobs (file transfers)  | X     |
| Individual (no BOX)       | X     |
```

---

### 2. Job Type Classification & Patterns

Classify every CMD job into a functional category based on its `command:`, `description:`, and job name:

| Category | Name Pattern / Command Pattern | Example |
|----------|-------------------------------|---------|
| Feed File Check | `*FEED_CHK*`, `chkFeedFile*` | Polls for incoming file from upstream |
| Data Upload/Load | `*UPLOAD*`, `*UPDATE*`, `*LOAD*` | Loads received data into application DB |
| Report Generation | `*REPORT*` | Generates output reports |
| File Transfer (NDM) | `*NDM*` | NDM file transfer to downstream |
| File Transfer (SCP) | `*SCP*` | SCP file copy to staging |
| App Server Start | `*START*`, `startWebLogic*`, `startManaged*` | Start application server |
| App Server Stop | `*STOP*`, `stopWebLogic*`, `stopManaged*` | Stop application server |
| NGINX/Web Start | `*NGINX*START*` | Start web server |
| NGINX/Web Stop | `*NGINX*STOP*` | Stop web server |
| Date Rollover | `*DATE_ROLLOVER*`, `*ROLLOVER*` | Business date change |
| Batch Processing | `*BATCH*` | Scheduled business logic execution |
| Cache Refresh | `*CACHE*` | Application cache invalidation/refresh |
| Permission Change | `*PERM*`, `*CHG*`, `chmod*` | File permission adjustments |
| Purge/Cleanup | `*PURGE*`, `*CLEAN*`, `*DELETE*` | Old file/data cleanup |
| Consolidation | `*CONSOLIDATE*` | Data aggregation jobs |
| Sleep/Wait | `*SLEEP*`, `sleep` | Delay between steps |
| Test/Interface | `*TEST*`, `*INTERFACE*` | Test or interface validation |
| DMS Document | `*DMS*` | Document management system operations |
| Entitlement | `*ENTITLEMENT*`, `*ENTIT*` | User/permission sync |
| Other | Not matching above | Describe based on command/description |

Present the classification with counts per category.

---

### 3. Dependency Chain Analysis

For each job with a `condition:` attribute:
- Parse the dependency expression: `s(JobA)` = success, `f(JobA)` = failure, `d(JobA)` = done
- Map all dependency chains (which job depends on which)
- Identify the **longest dependency chain** (critical path)
- Identify **parallel execution opportunities** (jobs in same BOX with no mutual dependencies)

Present dependency chains as:
```
BOX: [box_name]
  ├── Job A (time-triggered: 13:05)
  │     └── Job B (condition: s(Job A))
  │           └── Job C (condition: s(Job B))
  ├── Job D (time-triggered: 15:05)  [parallel to A chain]
  │     └── Job E (condition: s(Job D))
```

---

### 4. Scheduling & Calendar Analysis

Extract and summarize:
- **Unique start_times** — list all distinct trigger times
- **Run calendars** — list all `run_calendar:` values and what they mean (MonThruFri, custom, etc.)
- **Exclude calendars** — list all `exclude_calendar:` values (holiday exclusions)
- **Timezone** — identify timezone(s) used
- **Execution frequency** — how many times per day does each pattern repeat
- **Time slot clustering** — group jobs by start_time to identify peak windows

Present as:
```
| Time Slot | Jobs Triggered | BOX / Pattern |
|-----------|----------------|---------------|
| 00:30     | X              | BOX start     |
| 13:05     | X              | Feed checks   |
| 15:05     | X              | Feed checks   |
```

---

### 5. Execution Environment Analysis

Extract and summarize:
- **Target machines** — list all `machine:` values (servers where jobs run)
- **Owner accounts** — list all `owner:` values (Unix users)
- **Profiles sourced** — list all `profile:` values (environment setup scripts)
- **Scripts directory** — identify the base path for scripts from `command:` values
- **Output/Error log paths** — patterns for `std_out_file:` and `std_err_file:`

Present as:
```
| Machine                     | Jobs Count | Purpose |
|-----------------------------|------------|---------|
| cpbaplxpdb3.apac.nsroot.net | X          | Primary |
| cpbaplxpdb4.apac.nsroot.net | X          | COB     |
```

---

### 6. Complexity Assessment

Score each job and overall complexity:

**Per-job complexity factors:**
- Has dependencies (`condition:`) → +1
- Has time constraints (`start_times:`) → +1
- Has calendar constraints (`run_calendar:`, `exclude_calendar:`) → +1
- Runs on multiple machines (BOX children on different servers) → +2
- Has alarm/alert configured (`alarm_if_fail:1`) → +1
- Has runtime limit (`term_run_time:`) → +1
- Uses file-system paths that need migration → +1

**Overall complexity factors:**
- Number of unique dependency chains
- Maximum chain depth (longest sequential path)
- Number of BOX jobs (orchestration complexity)
- Cross-server execution (COB/failover patterns)
- Holiday calendar exclusions (business logic in scheduling)
- Total job count

**Scoring:**
| Score Range | Complexity | Migration Effort |
|-------------|------------|------------------|
| 0-2 per job | Low | Straightforward container Job |
| 3-4 per job | Medium | Needs orchestration (Argo DAG) |
| 5+ per job | High | Complex workflow, needs careful design |

---

### 7. Migration Impact Analysis

For each job category, assess:

| Category | On OpenShift | Refactoring Needed | Notes |
|----------|-------------|-------------------|-------|
| App Server Start/Stop | **ELIMINATED** | None — platform manages lifecycle | Remove these jobs entirely |
| NGINX/Web Start/Stop | **ELIMINATED** | None — Deployment handles restart | Remove these jobs entirely |
| Sleep/Wait | **ELIMINATED** | None — replaced by readiness probes | Remove these jobs entirely |
| COB duplicate jobs (_0 suffix) | **ELIMINATED** | None — OpenShift multi-AZ handles HA | Remove these jobs entirely |
| Feed File Check | **Migrate** | File path → PVC mount; polling → event-driven possible | Container Job |
| Data Upload | **Migrate** | DB connectivity via Vault/Secrets | Container Job |
| Report Generation | **Migrate** | Output to PVC or object storage | Container Job |
| NDM File Transfer | **Migrate (High)** | Need SFTP bridge (Pod → VM → NDM) | Container Job + network access |
| SCP File Transfer | **Migrate** | SCP target must be reachable from pod | Container Job |
| Date Rollover | **Migrate** | Script runs unchanged in container | Container Job |
| Batch Processing | **Migrate** | Script/Java app in container | Container Job |

Calculate:
- **Jobs eliminated** (no migration needed)
- **Jobs migrated as-is** (script in container, minimal change)
- **Jobs requiring refactoring** (NDM, file paths, connectivity)

---

### 8. Redundancy & Consolidation Opportunities

Identify:
- **Duplicate jobs** — same command running on different machines (primary + COB pattern, e.g., `_0` suffix)
- **Repeating time-slot patterns** — same job executed at multiple times (e.g., CHK, CHK1, CHK2, CHK3 at different hours)
- **Identical scripts** — different job names calling the same command with same/different parameters
- **Consolidation opportunities** — jobs that could be merged into a single parameterized workflow

---

### 9. Key Scripts Inventory

Extract a unique list of all scripts referenced in `command:` fields:
```
| Script | Called By (Jobs) | Parameters | Purpose |
|--------|-----------------|------------|---------|
| chkFeedFile.ksh | CHK, CHK1, CHK2... | FEEDTYPE REGION TIMEOUT HOUR | File arrival check |
| BLK_ORDER_RSFSREF_UPDATE.ksh | UPLOAD, UPLOAD1... | REGION | Data load |
```

---

### 10. Design Recommendations for Target Platform

Based on the analysis, provide:

1. **Recommended orchestration tool** (Argo Workflows, Tekton, or simple CronJob — based on dependency complexity)
2. **Container image strategy** — what tools/runtimes the batch image needs (ksh, sqlplus, SFTP client, Java, etc.)
3. **Calendar handling approach** — how to implement holiday/business-day exclusions
4. **Alerting strategy** — how to replace `alarm_if_fail` (AlertManager, PagerDuty, etc.)
5. **File storage strategy** — PVC vs. object storage for feed files
6. **Estimated reduction** — how many jobs are eliminated vs. migrated

---

### 11. Excel/Tabular Deliverable (Per-Job Export)

In addition to the analysis narrative, produce a per-job table (Excel-ready) with the following columns. This matches the structured export format teams use for migration tracking:

| Column | Source | Notes |
|--------|--------|-------|
| Job Name | `insert_job:` | Full job name |
| Job Type | `job_type:` | BOX / CMD / FW / FT |
| Box Name | `box_name:` | Parent BOX, if any |
| Category | Derived (Section 2) | Functional classification |
| Script Name | `command:` | Basename of script, or `cmd` for inline commands |
| Command | `command:` | Full command string |
| date_conditions | `date_conditions:` | 0 or 1 (see pitfall below) |
| Condition (dependency) | `condition:` | e.g., `s(JobA)` |
| Start Times | `start_times:` | Scheduled trigger time(s) |
| Run Calendar | `run_calendar:` | Business-day calendar |
| Exclude Calendar | `exclude_calendar:` | Holiday exclusions |
| Machine | `machine:` | Target server |
| alarm_if_fail | `alarm_if_fail:` | 1 = business-critical |
| Target Platform | Derived (see rules below) | ELIMINATED / Argo Workflow / CronJob / Job |
| Migration Rationale | Derived | Why this target was chosen |

**Job grouping technique (optional):** To collapse near-identical jobs, group by "job suffix" — the job name with the leading numeric app-ID prefix removed (e.g., `150043_PHKLX_EDT_UPLOAD` → `_PHKLX_EDT_UPLOAD`). Jobs that share a suffix but run on different machines/times are typically COB copies or time-slot repeats and can be counted together.

---

### 12. Target Platform Decision Logic (CRITICAL — avoid the common pitfall)

**PITFALL TO AVOID:** Do NOT decide the migration target using `date_conditions` alone. A naive rule like "`date_conditions=1` → OpenShift scheduled job; `date_conditions=0` → stays on Autosys/manual" is **incorrect** and produces a wrong blueprint:

- `date_conditions: 0` usually means the job is triggered by its **parent BOX or a `condition:` dependency** — these are highly migratable (they become workflow tasks), NOT "manual" or "non-migratable."
- Server start/stop jobs may have `date_conditions=1` but must be **ELIMINATED**, not scheduled.

**Target categories (use exactly these four, plus a Justification column):**

| # | Target Platform | Meaning |
|---|----------------|---------|
| 1 | **ELIMINATED** | Not required on OpenShift — the platform provides the capability natively |
| 2 | **Autosys Only** | Cannot/should not move yet — tightly coupled to non-containerized/on-prem infrastructure |
| 3 | **OpenShift Job** | On-demand or dependency/BOX-triggered — runs once when invoked (no independent schedule) |
| 4 | **OpenShift CronJob** | Has its own recurring time schedule (maps to native CronJob, or Argo CronWorkflow if it has internal dependency steps) |

**Terminology note:** For this report, treat **OpenShift CronJob** and **Argo CronWorkflow** as the same target type (both = scheduled recurring execution). The choice between native CronJob and Argo CronWorkflow is an implementation detail decided later (Argo is preferred when a scheduled job also has internal dependency steps).

**Correct decision order (evaluate top-down, first match wins):**

1. **Category is Server Start/Stop, NGINX/Web Start/Stop, or Sleep/Wait** → **ELIMINATED** (OpenShift Deployments + probes manage lifecycle). This takes precedence over `date_conditions`.
2. **Category is NDM File Transfer (or command uses NDM)** → **Autosys Only** (depends on on-prem NDM that remains on VM; re-evaluate once an SFTP bridge is validated).
3. **Job has `start_times:` (independent schedule)** → **OpenShift CronJob**.
4. **`date_conditions: 1` and standalone (no BOX)** → **OpenShift CronJob** (has its own date/time trigger).
5. **Job has a `condition:` dependency** → **OpenShift Job** (dependency-triggered, runs once).
6. **`date_conditions: 0` and inside a BOX** → **OpenShift Job** (BOX-triggered).
7. **Default (standalone, no schedule)** → **OpenShift Job** (on-demand).

Always record the **Justification** alongside the target so the decision is auditable.

**Note on BOX jobs:** A BOX is an orchestration container, not an executable. Its child jobs are classified individually per the rules above; the BOX itself maps to the workflow that groups those OpenShift Jobs/CronJobs.

---

## Output Format

Present the full analysis as a structured document with:
1. Executive summary (3-5 bullets: total jobs, key patterns, complexity verdict, elimination count)
2. Detailed tables for each section above (Sections 1-10)
3. Dependency chain diagrams (ASCII art or mermaid)
4. Per-job Excel-ready table (Section 11) with the Target Platform decided using Section 12 logic
5. Migration recommendation summary

**Companion tool:** For a repeatable Excel export, the `jil_excel_creator.py` script (in this folder) parses a JIL file and generates the Section 11 table plus a summary sheet, applying the Section 12 decision logic. Run: `python jil_excel_creator.py <input.jil> [output.xlsx]`. Use the script for bulk/automated exports and this skill for the narrative analysis and design recommendations.

---

## Important Rules

- Parse the JIL file carefully — fields may span multiple lines (especially `command:` and `description:` with quoted strings)
- A job belongs to a BOX if it has `box_name:` matching a BOX job's `insert_job:` name
- `condition: s(JobA)` means "run after JobA succeeds" — this is a dependency
- Jobs with `date_conditions: 0` inside a BOX inherit the BOX's scheduling
- Jobs with `_0` suffix typically indicate COB/failover copies running on alternate servers
- Job names often encode: `APPID_REGION_APPNAME_FUNCTION_SUFFIX`
- Count `alarm_if_fail: 1` to identify business-critical jobs
- The `term_run_time:` is in seconds
- **Never decide the migration target from `date_conditions` alone** — use the full decision logic in Section 12 (category + dependency + schedule + lifecycle). `date_conditions: 0` does NOT mean "manual" or "non-migratable."
- When grouping/counting near-identical jobs, strip the leading numeric app-ID prefix to derive the job "suffix" (e.g., `150043_EDT_UPLOAD` → `_EDT_UPLOAD`); jobs sharing a suffix are usually COB copies or time-slot repeats.

---

## Example Usage

When given a JIL file, respond with:

```
## Autosys JIL Analysis — [Application Name]

### Executive Summary
- Total: X jobs (Y BOX, Z CMD)
- Patterns: [list top 3-4 categories]
- Complexity: [Low/Medium/High] — [reason]
- Migration: X jobs eliminated, Y jobs migrate, Z need refactoring

### [Detailed sections 1-12 as above]
### [Per-job Excel-ready table with Target Platform + Rationale]
```

---

## Reusability Notes

This skill applies to ANY application's Autosys JIL files. The job categories, complexity scoring, and migration patterns are generic. Adjust the "App Server Start/Stop" category names based on the specific app server used (WebLogic, Liberty, Tomcat, JBoss, etc.).
