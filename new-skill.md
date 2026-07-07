---
name: snyk-maven-remediation
description: >
  Remediate Snyk-reported dependency vulnerabilities in Spring Boot Maven projects
  by upgrading JDK versions, adding version property overrides, fixing version
  mismatches, and updating direct dependencies. Use this skill when the user
  mentions "fix Snyk vulnerabilities", "remediate CVE", "upgrade vulnerable
  dependencies", "apply security patches to pom.xml", "resolve Snyk findings",
  "upgrade JDK", "fix dependency security issues", or "make dependencies
  compliant" — even if they don't explicitly name a specific CVE. Do NOT use
  for code-level vulnerabilities (SAST), Docker/container image CVEs, or
  SBOM plugin installation.
---

# Fix Snyk dependency vulnerabilities in Maven Spring Boot projects

This skill walks through reading a Snyk vulnerability report (from the Snyk dashboard, CLI output, or CSV export), classifying each finding as a direct or transitive dependency, planning the POM edits, and applying them so vulnerable dependencies resolve to a non-vulnerable version. The Citi parent BOM (`ccp-spring-boot-starter-parent-master`) respects standard Spring Boot version property names, so the bulk of transitive fixes are single-line property additions.

## When to use this skill

Trigger whenever the user wants to:
- Fix or remediate Snyk-reported CVEs in their Maven `pom.xml`
- Upgrade JDK version as part of a security remediation cycle
- Add version property overrides to pin secure transitive dependency versions
- Remove version mismatches (e.g., Boot 4.x deps in a Boot 3.x project)
- "Make my project pass Snyk" / "clean up security findings"

Do **not** trigger for:
- Code-level security issues (SAST, secret detection) — different concern
- Vulnerabilities in the user's own code (not in dependencies)
- Docker base image CVEs (Tomcat runtime, JDK base image) — escalate to DevOps
- Installing or configuring the SBOM/Snyk plugin itself — use `sbom-install-plugin`
- BlackDuck-specific workflows — use `sbom-fix-vulnerabilities`

## Shell environment

Snippets in this skill assume **PowerShell** (Windows). For Unix, replace `findstr` with `grep`. Maven commands are cross-platform.

## The workflow

Steps are always performed in this order. Each step depends on the previous one.

### Step 1: Detect the project context

Read the target `pom.xml`. Extract:
- **Parent BOM**: artifact ID and version (determines which property overrides work)
- **Current JDK version**: `<java.version>`, `<maven.compiler.source>`, `<maven.compiler.target>`
- **Existing CVE properties**: any `spring-framework.version`, `micrometer.version`, etc. already present
- **Spring Boot major version**: Boot 3.x uses Spring Framework 6.x; Boot 4.x uses 7.x

For the 6 Citi CHUB services covered by this skill, all are:
- Parent: `ccp-spring-boot-starter-parent-master` (2026.6.13.RELEASE or 2026.4.20.RELEASE)
- Boot 3.x / Spring Framework 6.x
- Currently on Java 17 (target: 21)
- No CVE remediation properties set (all need adding)

See `references/service-registry.md` for per-service details.

### Step 2: Parse the Snyk report

Extract from the Snyk findings (dashboard, CSV, or CLI output):
- **Library**: groupId:artifactId (e.g., `org.springframework:spring-core`)
- **Actual version**: currently resolved (vulnerable)
- **Expected version**: minimum fixed version
- **CVE ID**: for traceability
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW

### Step 3: Classify each finding as direct or transitive

Search the project's `pom.xml` for the package coordinates:
- **Direct**: the `<groupId>` + `<artifactId>` pair appears in `<dependencies>` with an explicit `<version>` tag → bump the version in place
- **Transitive (BOM-managed)**: the library resolves through the parent BOM but isn't declared directly → add/update a version property in `<properties>`
- **Transitive (no property available)**: no Spring Boot property name exists for this library → add a `<dependencyManagement>` entry

**Principle: closer to the project, better.** Fix at the highest level you can:
1. Version property override (covers all transitive paths at once)
2. Direct version bump (explicit in the POM)
3. `<dependencyManagement>` entry (last resort for unmanaged transitives)
4. Exclusion + replacement (only when the above won't work)

### Step 4: Plan the edits — show the user BEFORE applying

Present the proposed changes grouped by type:

```
JDK UPGRADE (5 locations):
  ~ java.version: 17 → 21
  ~ maven.compiler.source: 17 → 21
  ~ maven.compiler.target: 17 → 21
  ~ compiler-plugin <source>: 17 → 21
  ~ compiler-plugin <target>: 17 → 21

PROPERTIES TO ADD (transitive CVE fixes):
  + spring-framework.version = 6.2.19       (fixes 5 CVEs)
  + spring-retry.version = 2.0.13           (fixes 1 CVE)
  + micrometer.version = 1.15.12            (fixes 1 CVE)
  + netty.version = 4.1.135.Final           (fixes 3 CVEs)
  + tomcat.version = 10.1.55                (fixes 2 CVEs)

VERSION MISMATCHES TO FIX:
  - spring-boot-starter-webmvc-test: REMOVE <version>4.0.6</version>

DIRECT DEPS TO UPDATE:
  ~ commons-io: 2.21.0 → 2.22.0

RISK: LOW (property overrides, no API changes expected)
```

Wait for user confirmation before proceeding. If the user pushes back on a specific upgrade ("don't touch spring-kafka, that breaks our consumer"), drop it from the plan and continue with the rest.

### Step 5: Apply the edits

Apply in this order (direct fixes first, then transitives):

1. **JDK upgrade** — change all 5 locations from 17 to 21
2. **Remove version mismatches** — delete explicit `<version>` tags on Spring Boot/Cloud artifacts
3. **Update direct dependency versions** — bump explicit versions to secure targets
4. **Add CVE remediation properties** — add to `<properties>` section after JDK entries

The order matters: removing a Boot 4.x mismatch and bumping directs may resolve some transitive findings, reducing the properties you need to add.

### Step 6: Validate (re-scan)

Run the build and verify resolved versions:

```powershell
# Build must pass
mvn clean compile -DskipTests

# Verify Spring Framework resolved to target
mvn dependency:tree -Dincludes=org.springframework:spring-core
# Expected: 6.2.19

# Verify no Boot version mismatches remain
mvn dependency:tree | findstr "spring-boot" | findstr "4.0"
# Expected: no output

# Run tests
mvn test
```

Delegate to `scripts/validate-remediation.ps1 -ProjectDir <path>` for automated validation.

If the user's environment cannot run Maven (no Nexus access, no JDK installed), skip validation and tell them what to verify manually.

### Step 7: Report the result

Present a final summary:

```
Fixed:
  - org.springframework:spring-core     6.2.15 → 6.2.19  (CVE-2026-41851, HIGH)
  - org.springframework.retry           2.0.11 → 2.0.13  (CVE-2026-41710, HIGH)
  - io.micrometer:micrometer-core       1.14.6 → 1.15.12 (CVE-2026-40984, MEDIUM)
  - io.netty:netty-handler              4.1.110 → 4.1.135 (CVE-2026-45416, CRITICAL)
  - org.apache.tomcat.embed:tomcat-core 10.1.28 → 10.1.55 (CVE-2026-41284, HIGH)

Skipped:
  - <none>

Requires manual review:
  - spring-boot (CVE-2026-40975) — needs parent BOM upgrade, not a property fix

Re-scan: 0 CRITICAL, 0 HIGH, 0 MEDIUM (down from 1 CRITICAL, 8 HIGH, 3 MEDIUM)
```

## Whitelisted / accepted findings

If the Snyk report marks a finding as "ignored" or "accepted risk", do not propose a fix for it. Mention it in the final summary as "skipped (accepted)" so the user knows it was seen.

## Direct vs. transitive dependencies — why order matters

The Snyk report lists *what's* vulnerable but not *why it's in the tree*. This skill classifies by grepping the POM for coordinates.

- **Direct** (appears in `<dependencies>` with a `<version>` tag) → bump its version. Always do these first — bumping a direct dep often updates its transitives too, so some transitive findings disappear without any override.
- **Transitive** (NOT in `<dependencies>`, pulled in by parent BOM or another dep) → add a version property or `<dependencyManagement>` entry. Only do this for findings that *remain* after direct fixes.

**Known rule for Citi CHUB projects**: For `org.springframework.boot` and `org.springframework.cloud` artifacts, NEVER hardcode a `<version>`. If you see one, it's a mismatch — remove it and let the parent BOM manage the version.

## CVE-to-Property lookup table

Use this to map a Snyk finding to the correct property override:

| CVE ID | Library | Property to set | Target Version |
|--------|---------|----------------|---------------|
| CVE-2026-41850 | spring-expression | spring-framework.version | 6.2.19 |
| CVE-2026-41839 | spring-web | spring-framework.version | 6.2.19 |
| CVE-2026-41851 | spring-core | spring-framework.version | 6.2.19 |
| CVE-2026-41846 | spring-webmvc | spring-framework.version | 6.2.19 |
| CVE-2026-41855 | spring-jms | spring-framework.version | 6.2.19 |
| CVE-2026-41710 | spring-retry | spring-retry.version | 2.0.13 |
| CVE-2026-40984 | micrometer-core | micrometer.version | 1.15.12 |
| CVE-2026-42498 | tomcat-embed-websocket | tomcat.version | 10.1.55 |
| CVE-2026-41284 | tomcat-embed-core | tomcat.version | 10.1.55 |
| CVE-2026-45416 | netty-handler | netty.version | 4.1.135.Final |
| CVE-2026-42587 | netty-codec | netty.version | 4.1.135.Final |
| CVE-2026-42581 | netty-codec-http | netty.version | 4.1.135.Final |
| CVE-2026-41726 | spring-kafka | spring-kafka.version | 3.3.16 |

For libraries not in this table, check the Spring Boot Appendix:
https://docs.spring.io/spring-boot/appendix/dependency-versions/properties.html

## Guardrails

- NEVER remove existing `<exclusions>` blocks — they are intentional security exclusions (xstream, woodstox, bouncycastle-jdk15on, commons-jxpath, snakeyaml)
- NEVER remove the `jdk8` classifier from hsqldb
- NEVER upgrade Spring Framework across major versions (5→6 or 6→7) as part of a CVE fix
- NEVER add snakeyaml — it is intentionally excluded from cmr-em-microserviceframework
- NEVER change the parent BOM version without explicit user approval
- ALWAYS apply JDK 21 upgrade + CVE properties together — both are mandatory
- ALWAYS show the edit plan and wait for confirmation before modifying files
- ALWAYS re-validate with `mvn clean compile -DskipTests` after applying

## Maintenance

When new Snyk findings appear:
1. Check if a newer `ccp-spring-boot-starter-parent-master` is available on Nexus — cleanest fix
2. Look up the library in the CVE-to-Property table above
3. If not listed, find the Spring Boot property name from the appendix link above
4. Add the new property + version to the table in this SKILL.md
5. Validate with `mvn clean compile -DskipTests` and `mvn dependency:tree`
