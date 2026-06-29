# Migration Prompt Library

Reusable prompts for GitHub Copilot Chat, organized by migration workflow phase.
Each prompt is designed to trigger the corresponding skill and produce detailed, actionable output.

---

## How to Use These Prompts

1. Open the target application repo in VS Code
2. Use `@workspace` prefix for repo-aware prompts
3. Use `#file:path/to/file` for file-specific prompts
4. Paste tool output (RHMTA, TA, AMA) directly into the prompt where indicated
5. Chain prompts in sequence for complete analysis

---

## PHASE 1: Initial Assessment (migration-analysis skill)

### 1.1 — Repository Quick Scan

```
@workspace Perform an initial migration assessment of this repository.

Identify and report:
1. Build system and configured Java version (source/target/release)
2. Spring Boot version (exact version from parent POM or dependency management)
3. Spring Framework version
4. Application packaging type (WAR or JAR)
5. Application server dependencies (embedded Tomcat, external Tomcat, WAS, WebLogic)
6. Database technology and connection method (JNDI, Spring DataSource, etc.)
7. Security framework (Spring Security version, custom filters)
8. Messaging systems (JMS, Kafka, RabbitMQ)
9. Caching mechanisms (EhCache, Redis, Hazelcast)
10. External integrations (REST clients, SOAP, gRPC)
11. CyberArk or vault integration presence
12. Test frameworks and approximate test coverage
13. Existing containerization (Dockerfile, docker-compose, Kubernetes manifests)
14. CI/CD pipeline configuration

Output as a structured table with: Component | Current Version | Target Version | Migration Impact (High/Medium/Low/None)
```

### 1.2 — Dependency Matrix (Detailed)

```
@workspace #file:pom.xml

Analyze this POM and generate a complete dependency migration matrix.

For EVERY dependency (direct and managed), create a table row with:
| GroupId:ArtifactId | Current Version | Target Version (for Java 17 + Spring Boot 3.3) | Action | Breaking Changes | Effort |

Action must be one of:
- UPGRADE: New version needed
- REPLACE: Different artifact (e.g., javax→jakarta)
- REMOVE: No longer needed
- KEEP: Already compatible
- INVESTIGATE: Unknown compatibility

Rules:
- Do NOT summarize. List every single dependency.
- Include Maven plugins that need version updates.
- Flag any dependency that has no Jakarta-compatible version available.
- Identify transitive dependency conflicts.
- Note if any dependency is an internal/proprietary library (com.citi.*, com.ibm.*).
```

### 1.3 — javax Usage Inventory

```
@workspace Search the entire codebase for all javax.* imports that need to change to jakarta.*.

For each occurrence, report:
| File Path | Line | Import Statement | New Import (jakarta) | Auto-fixable (Y/N) |

Exclude javax packages that do NOT change:
- javax.sql.*
- javax.crypto.*
- javax.net.*
- javax.security.auth.*
- javax.naming.*
- javax.xml.parsers.*
- javax.swing.*

At the end, provide:
- Total files affected: X
- Total import lines to change: X
- Breakdown by package (javax.persistence: X, javax.servlet: X, etc.)
- Estimated time for automated find-replace: X minutes
- Files that need MANUAL review (where javax usage is in logic, not just imports)
```

### 1.4 — RHMTA Report Deep Analysis

```
I have the RHMTA migration analysis report for application [APP_NAME].
Migration path: Java 8 + Spring Boot 2.x + Tomcat 9 VM → Java 17 + Spring Boot 3.3 + Tomcat 10 container.

Here is the report data:

[PASTE RHMTA CSV/TEXT EXPORT HERE]

Provide a DETAILED analysis:

## 1. Summary Dashboard
- Total findings: X
- Mandatory: X (Y story points)
- Optional: X (Y story points)
- Potential: X (Y story points)

## 2. Mandatory Findings Breakdown
For EACH mandatory finding:
| Rule ID | Description | Affected Files | Current Code Pattern | Fixed Code Pattern | Auto-fixable | Effort (hrs) |

## 3. Automation Assessment
- Findings fixable with find-replace: X (list rule IDs)
- Findings fixable with IDE refactoring: X (list rule IDs)
- Findings requiring manual code changes: X (list rule IDs)
- Findings requiring architecture decisions: X (list rule IDs)

## 4. Critical Path Analysis
- Which mandatory findings BLOCK other fixes?
- What is the dependency order for fixes?
- Which findings must be fixed BEFORE Java upgrade vs AFTER?

## 5. False Positive Assessment
- Which findings don't apply to our target (Spring Boot 3.x on Tomcat 10)?
- Which findings are already handled by Spring Boot starters?

## 6. Risk Flags
- Findings related to CyberArk/vault: [list]
- Findings related to database/JNDI: [list]
- Findings related to security config: [list]
- Findings with no known fix: [list]
```

### 1.5 — Transformation Advisor Report Analysis

```
Here is the Transformation Advisor assessment for [APP_NAME]:

[PASTE TA REPORT DATA HERE]

Our specific migration target: Spring Boot 3.3 on Tomcat 10.1 container (NOT Cloud Foundry, NOT OpenShift native).

Provide detailed analysis:

## 1. Complexity Assessment
- TA reported complexity: [X]
- ADJUSTED complexity for our target: [X] — explain why different
- TA estimated days: X
- ADJUSTED estimate: X — explain reasoning

## 2. Technology Findings (Detailed)
For each finding:
| Finding | Severity | Applies to Our Target? | If Yes: Fix Approach | If No: Why False Positive | Effort (hrs) |

## 3. False Positive Analysis
List every finding that does NOT apply because:
- We are migrating TO Spring Boot (not FROM it)
- We are staying on Tomcat (not changing app servers)
- Feature is already provided by Spring Boot
- Finding is for a technology we don't use

## 4. Revised Effort Estimate
After removing false positives:
- Actual blocking findings: X
- Actual high-effort findings: X
- Actual low-effort findings: X
- REVISED total effort: X days (vs TA original: Y days)

## 5. Items NOT Detected by TA
Based on our target stack, what issues will we likely encounter that TA didn't flag?
(e.g., Spring Security rewrite, Hibernate 6 changes, property key migrations)
```

### 1.6 — AMA Containerization Readiness

```
Here is the AMA (Application Modernization Accelerator) output for [APP_NAME]:

[PASTE AMA OUTPUT HERE]

VM Profile (from Truesight/Server-Info):
- CPU: [X] cores allocated, P95 utilization: [X]%
- Memory: [X] GB allocated, P95 utilization: [X]%
- Disk: [X] GB used
- OS: [RHEL/Windows]
- Current JDK: [OracleJDK/OpenJDK] [version]

Provide detailed containerization assessment:

## 1. Readiness Score: X/10
Justify each point deducted.

## 2. Blocking Issues (must fix BEFORE containerizing)
For each blocker:
| Issue | Current State | Required Change | Effort | Risk if Ignored |

## 3. Container Architecture Recommendation
- Approach: [Lift-and-shift WAR / Embedded JAR / Refactor]
- Justify why this approach over alternatives
- Base image recommendation: [specific image tag]
- Dockerfile pattern: [A/B/C/D from tomcat-containerization skill]

## 4. Resource Sizing
Based on VM utilization data:
- CPU request: [calculated]
- CPU limit: [calculated]
- Memory request: [calculated]
- Memory limit: [calculated]
- JVM heap configuration: [specific flags]
- Show calculation methodology

## 5. Non-Functional Concerns
- Session handling: [stateless/sticky/distributed]
- File system usage: [what moves to volumes/S3]
- Logging strategy: [stdout/file/centralized]
- Health check endpoints: [specific paths]
- Graceful shutdown: [configuration needed]

## 6. CyberArk Integration Pattern
- Current: [how credentials are retrieved today]
- Container pattern: [init-container/sidecar/CCP-REST]
- Configuration changes needed
```

### 1.7 — Cross-Tool Unified Blueprint

```
I have completed analysis using all three tools for [APP_NAME].
Below are the consolidated findings.

RHMTA Summary:
[PASTE RHMTA SUMMARY - mandatory/optional/potential counts and top findings]

Transformation Advisor Summary:
[PASTE TA SUMMARY - complexity, effort, key findings]

AMA Summary:
[PASTE AMA SUMMARY - readiness score, blockers]

Additional context:
- Application: [name, CAI ID]
- Current: Java [X], Spring Boot [X], Tomcat [X], [VM OS]
- Target: Java 17, Spring Boot 3.3, Tomcat 10.1 container
- Team size: [X developers]
- Timeline constraint: [if any]

Generate a COMPLETE Blueprint Analysis document:

## Executive Summary (2-3 sentences)

## Application Profile Table

## Unified Findings (deduplicated across tools)
| ID | Finding | Source Tool(s) | Category | Severity | Auto-fixable | Effort (hrs) | Phase |

## Migration Phases
### Phase 1: Preparation (Java upgrade prerequisites)
- Tasks, effort, dependencies

### Phase 2: Java 8 → 17 Upgrade
- Tasks, effort, dependencies

### Phase 3: Spring Boot 2.x → 3.x
- Tasks, effort, dependencies

### Phase 4: Containerization
- Tasks, effort, dependencies

### Phase 5: Validation & Hardening
- Tasks, effort, dependencies

## Risk Register
| Risk | Probability | Impact | Mitigation | Owner |

## Effort Summary
| Phase | Automated (hrs) | Manual (hrs) | Total | Sprint Estimate |

## Dependencies & Blockers
- External dependencies (CyberArk, DBAs, infra team)
- Sequencing constraints
- Environment needs

## Recommendations
- Quick wins (do first)
- Parallel work streams
- Items to defer post-migration
```

---

## PHASE 2: Java Upgrade (java-version-upgrade skill)

### 2.1 — Java Build Configuration Fix

```
@workspace #file:pom.xml

Update this POM for Java 17 compilation. Provide the COMPLETE modified pom.xml with:
1. Java version properties updated to 17
2. maven-compiler-plugin updated to 3.13+ with release=17
3. maven-surefire-plugin updated to 3.5+
4. maven-failsafe-plugin updated to 3.5+
5. Any other plugins that need version bumps for Java 17
6. Maven Enforcer plugin rule updated if present

Show the complete <properties> and <build><plugins> sections.
Do not omit any existing configuration — show the full updated version.
```

### 2.2 — Removed Module Replacement

```
@workspace Scan the entire codebase for usage of removed Java EE modules:
- javax.xml.bind (JAXB)
- javax.xml.ws (JAX-WS)
- javax.activation
- javax.annotation (Common Annotations)

For each module found:
1. List every file and line that uses it
2. Provide the Maven dependency to add as replacement
3. Show any import changes needed in the code
4. If JAXB xjc code generation is used, show the updated plugin configuration

Output the complete <dependencies> section additions needed.
```

### 2.3 — Strong Encapsulation Audit

```
@workspace Identify all code that uses internal JDK APIs (sun.*, com.sun.*, jdk.internal.*).

For each usage:
| File | Line | Internal API Used | Standard Replacement | Code Before | Code After |

Also check for:
- Libraries that use reflection on JDK internals (via dependency:tree analysis)
- JVM flags in any script/Dockerfile/YAML that use --illegal-access
- Test code that mocks internal classes

Provide:
1. Immediate fixes (code changes to standard APIs)
2. Temporary --add-opens flags needed (with specific modules)
3. Library upgrades that resolve the issue transitively
```

### 2.4 — JVM Startup Script Migration

```
Our current JVM startup configuration is:

[PASTE CURRENT JVM FLAGS / startup script / JAVA_OPTS]

Target: Java 17 [or 21], containerized deployment.

For each flag:
| Current Flag | Status (removed/deprecated/valid) | Replacement | Notes |

Then provide the COMPLETE new JVM configuration optimized for:
- Container deployment (cgroup-aware)
- [Low-latency API / High-throughput batch / General purpose] workload
- [X] GB container memory limit

Include GC selection rationale and logging configuration.
```

---

## PHASE 3: Spring Boot Upgrade (springboot-upgrade skill)

### 3.1 — Spring Security Complete Rewrite

```
@workspace Find all Spring Security configuration classes in this project.

For EACH class, provide:

### [ClassName.java]
**Current implementation (full code):**
[show complete current file]

**Migrated implementation (full code for Spring Boot 3.x / Spring Security 6.x):**
[show complete rewritten file]

**Changes explained:**
- [list each API change and why]

Cover:
- WebSecurityConfigurerAdapter removal → SecurityFilterChain bean
- authorizeRequests() → authorizeHttpRequests()
- antMatchers() → requestMatchers()
- CSRF configuration changes
- AuthenticationManagerBuilder changes
- @EnableGlobalMethodSecurity → @EnableMethodSecurity
- Any custom filters that use javax.servlet → jakarta.servlet
```

### 3.2 — Application Properties Migration

```
@workspace #file:src/main/resources/application.properties
[or #file:src/main/resources/application.yml]

Analyze this configuration file for Spring Boot 3.x compatibility.

For EVERY property:
| Current Key | Status | New Key (if changed) | Value Change Needed? | Notes |

Status values: UNCHANGED, RENAMED, REMOVED, RESTRUCTURED

Then provide the COMPLETE migrated configuration file.
Do not skip any property — show the full file.

Also check:
- application-{profile}.properties/yml files
- bootstrap.properties/yml (needs spring.config.import migration)
- Any custom property files loaded via @PropertySource
```

### 3.3 — Hibernate/JPA Entity Audit

```
@workspace Find all JPA entities (@Entity classes) in this project.

For each entity, check:
1. @GeneratedValue strategy — does it use GenerationType.AUTO?
   If yes, show the fix (explicit IDENTITY or SEQUENCE based on our database: [MySQL/Oracle/PostgreSQL])
2. @Type annotations using string form — show conversion to class reference
3. Any Hibernate-specific annotations that changed in version 6
4. Custom ID generators — compatibility check

Provide a table:
| Entity Class | File Path | Issues Found | Required Changes | Effort |

For entities with issues, show the before/after code.
```

### 3.4 — Spring Cloud Migration

```
@workspace Check if this project uses Spring Cloud.

If yes, identify:
1. Current Spring Cloud version/train
2. Required version for Spring Boot 3.3
3. All Spring Cloud dependencies that need version changes

Specifically check for:
- Spring Cloud Sleuth → Micrometer Tracing migration
- bootstrap.yml → spring.config.import migration
- Feign client configuration changes
- Circuit breaker (Hystrix → Resilience4j) if still on Hystrix
- Spring Cloud Gateway route predicate changes
- LoadBalancer (Ribbon → Spring Cloud LoadBalancer)

For each change found, show the complete before/after configuration.
```

### 3.5 — Auto-Configuration Migration

```
@workspace Check if this project has custom Spring Boot auto-configuration.

Look for:
1. META-INF/spring.factories with auto-configuration entries
2. @Configuration classes registered in spring.factories
3. Custom Spring Boot starters

If found, show:
- Current spring.factories content
- New file: META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
- Any @AutoConfiguration annotation changes needed
- Complete before/after for each affected file
```

---

## PHASE 4: Containerization (tomcat-containerization skill)

### 4.1 — Dockerfile Generation

```
@workspace Generate a production-ready Dockerfile for this application.

Application details:
- Packaging: [WAR/JAR]
- Java version: 17 [or 21]
- Spring Boot version: 3.3
- Build tool: Maven [or Gradle]
- Target: [Tomcat 10 container WAR / Embedded Tomcat JAR]

Requirements:
- Multi-stage build (builder + runtime)
- Eclipse Temurin base image (pin specific version, not latest)
- Non-root user
- Security hardening (remove unnecessary files)
- Container-optimized JVM flags
- Health check configuration
- Proper ENTRYPOINT with JAVA_OPTS support
- Layer caching optimization (for Spring Boot JAR: layered extraction)

Also provide:
- .dockerignore file content
- docker-compose.yml for local development
- Build command with proper tags
```

### 4.2 — Resource Sizing Calculation

```
Calculate container resource limits for this application.

VM Profile (from Truesight/Server-Info):
- Allocated: [X] CPU cores, [X] GB RAM
- CPU utilization — P50: [X]%, P95: [X]%, P99: [X]%
- Memory utilization — P50: [X]%, P95: [X]%, P99: [X]%
- Peak concurrent connections: [X]
- Application tier: [web API / batch processing / messaging consumer]

Calculate and provide:
1. CPU request (millicores) — with formula shown
2. CPU limit (millicores) — with formula shown
3. Memory request (Mi/Gi) — with formula shown
4. Memory limit (Mi/Gi) — with formula shown
5. JVM heap size (-XX:MaxRAMPercentage) — with breakdown:
   - Heap allocation
   - Metaspace estimate
   - Native memory estimate
   - Thread stack estimate
   - Buffer/overhead
6. Recommended replica count for HA
7. HPA configuration (min/max replicas, scale triggers)

Output as:
- Kubernetes resource spec (YAML)
- JVM flags (JAVA_OPTS)
- HPA manifest
```

### 4.3 — Kubernetes Deployment Complete

```
@workspace Generate complete Kubernetes deployment manifests for this application.

Requirements:
- Deployment with rolling update strategy (zero downtime)
- Service (ClusterIP)
- ConfigMap for non-sensitive configuration
- Health checks (liveness, readiness, startup probes)
- Resource limits (from sizing: CPU [X], Memory [X])
- Security context (non-root, read-only filesystem)
- CyberArk integration via [init-container / sidecar / environment variable]
- Spring profile activation for container environment
- Graceful shutdown configuration

Container specs:
- Image: registry.citi.com/[team]/[app]:[version]
- Port: 8080
- Health endpoint: /actuator/health
- Profiles: container,prod

Generate separate YAML files for:
1. deployment.yaml
2. service.yaml
3. configmap.yaml
4. hpa.yaml (horizontal pod autoscaler)
```

### 4.4 — VM to Container Migration Checklist

```
@workspace Generate a complete migration checklist for moving this application
from Tomcat VM to Tomcat container.

For each checklist item, provide:
| # | Task | Category | Pre-requisite | Validation Step | Done? |

Categories:
- Build: Dockerfile, CI/CD pipeline changes
- Config: application.yml, externalized config
- Security: non-root, secrets, network policies
- Infra: container registry, K8s namespace, DNS
- Integration: CyberArk, database connectivity, service discovery
- Observability: logging (stdout), metrics, tracing
- Resilience: health checks, graceful shutdown, resource limits
- Testing: smoke test, load test, failover test

Include items specific to this application (based on codebase analysis).
Flag any blocking dependencies on other teams (DBA, infra, security).
```

---

## PHASE 5: Validation & Security

### 5.1 — Snyk/SonarQube Remediation Plan

```
Here are the Snyk vulnerability findings after our migration:

[PASTE SNYK REPORT]

For each vulnerability:
| CVE | Severity | Affected Dependency | Current Version | Fixed Version | Breaking Changes on Upgrade | Auto-fixable |

Then prioritize:
1. Critical + exploitable: fix immediately
2. High + in production path: fix this sprint
3. Medium: fix next sprint
4. Low: backlog

For the top 10 critical/high findings, provide:
- Exact pom.xml change needed
- Any code changes required after the version bump
- Test impact (will existing tests break?)
```

### 5.2 — Post-Migration Validation Prompts

```
@workspace After migrating to Java 17 + Spring Boot 3.3, generate a
comprehensive validation test plan.

Include:
1. Build validation (compilation, all tests pass)
2. Startup validation (app starts, no reflection warnings, correct GC)
3. Functional validation (key endpoints respond correctly)
4. Security validation (auth flows work, CSRF correct, CyberArk retrieves)
5. Performance validation (response times within baseline ±10%)
6. Container validation (resource limits respected, health checks pass)
7. Integration validation (DB connects, external services reachable)

For each validation point:
| Test | Command/Step | Expected Result | Actual | Pass/Fail |

Provide specific curl commands, test scripts, or kubectl commands for each.
```

---

## PROMPT ENGINEERING TIPS

### Force Detailed Output
Add these suffixes to any prompt:
- `"Do not summarize. Show every item."`
- `"Output as a markdown table with one row per finding."`
- `"Show complete code, not just the changed lines."`
- `"I need this for a formal blueprint document — be exhaustive."`

### Control Scope
- `@workspace` = entire repo context
- `#file:path` = specific file focus
- Paste data directly = tool output analysis

### Iterative Deepening
1. Start broad: "Assess this repo for migration"
2. Go deep: "Now detail every javax import that needs changing"
3. Get code: "Show me the complete rewritten SecurityConfig"
4. Get tasks: "Convert this analysis into JIRA-ready task descriptions"

### Context Loading
If Copilot gives generic answers, it might not have loaded the skill.
Trigger it with keywords from the skill description:
- "migration readiness" → migration-analysis
- "Java 8 to 17" → java-version-upgrade
- "javax to jakarta" → springboot-upgrade
- "containerize this Tomcat app" → tomcat-containerization
