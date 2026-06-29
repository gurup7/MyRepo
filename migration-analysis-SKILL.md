---
name: migration-analysis
description: 'Guide for analyzing Java application repositories for migration readiness using RHMTA, Transformation Advisor, and Application Modernization Accelerator (AMA). Use when performing initial codebase assessment, generating dependency analysis, interpreting migration tool reports, identifying migration blockers, estimating migration effort, creating a migration blueprint, or analyzing Maven/Gradle dependency trees for Java 8 to 17/21 and Spring Boot 2.x to 3.x upgrade scenarios. Covers report interpretation, issue prioritization, and blueprint document generation.'
---

# Migration Analysis & Dependency Assessment

This skill guides the initial analysis of a Java application repository to assess migration readiness, interpret tool reports from RHMTA, Transformation Advisor, and AMA, generate dependency matrices, and produce structured blueprint document sections.

## When to Use This Skill

- Starting a new migration assessment for a Java/Spring Boot application
- Interpreting RHMTA (Red Hat Migration Toolkit for Applications) HTML/CSV reports
- Analyzing Transformation Advisor output for migration complexity
- Using AMA (Application Modernization Accelerator) to assess containerization readiness
- Generating a dependency upgrade matrix from Maven/Gradle projects
- Creating the Analysis section of a migration Blueprint document
- Estimating effort and identifying blockers before code changes begin
- Correlating findings across multiple analysis tools

## Analysis Workflow Overview

```
Step 1: Repository Structure Scan
         ↓
Step 2: Maven/Gradle Dependency Analysis
         ↓
Step 3: RHMTA Analysis (migration issues)
         ↓
Step 4: Transformation Advisor (complexity & effort)
         ↓
Step 5: AMA Analysis (containerization readiness)
         ↓
Step 6: Correlate & Prioritize Findings
         ↓
Step 7: Generate Blueprint Analysis Section
```

## Step 1: Repository Structure Scan

Before running tools, understand the application structure:

### Key Files to Identify

| File/Pattern | What It Tells You |
|--------------|-------------------|
| `pom.xml` (root) | Maven project, parent POM version, Java version |
| `build.gradle` | Gradle project, plugin versions |
| `settings.xml` / `gradle.properties` | Multi-module structure |
| `src/main/webapp/WEB-INF/web.xml` | Traditional WAR deployment (servlet config) |
| `application.properties` / `application.yml` | Spring Boot app, profile configs |
| `Dockerfile` / `docker-compose.yml` | Already containerized (partial migration) |
| `server.xml` / `context.xml` | External Tomcat configuration |
| `persistence.xml` | JPA configuration outside Spring |
| `ejb-jar.xml` | EJB usage (WAS/WebLogic origin) |
| `ibm-web-bnd.xml` / `weblogic.xml` | App server-specific bindings |

### Initial Assessment Prompt Template

```
Analyze this repository structure and identify:
1. Build system (Maven/Gradle) and Java version configured
2. Spring Boot version (from parent POM or dependency)
3. Application type (WAR/JAR, web/batch/messaging)
4. Application server dependencies (Tomcat/WAS/WebLogic)
5. Key frameworks in use (Spring MVC, Spring Data, JMS, etc.)
6. Any existing containerization (Dockerfile present?)
7. Test coverage indicators (test frameworks, test directory structure)
```

## Step 2: Maven/Gradle Dependency Analysis

### Generating the Dependency Tree

```bash
# Maven — full dependency tree
mvn dependency:tree -DoutputType=text -DoutputFile=dependency-tree.txt

# Maven — only show conflicts
mvn dependency:tree -Dverbose -Dincludes=javax.*,jakarta.*

# Maven — analyze unused/undeclared dependencies
mvn dependency:analyze

# Gradle
gradle dependencies --configuration runtimeClasspath > dependency-tree.txt
```

### Dependency Classification Matrix

When analyzing dependencies, classify each into:

| Category | Description | Example |
|----------|-------------|---------|
| Must Upgrade | Incompatible with target Java/Spring version | Spring Boot 2.7, Hibernate 5.x |
| Must Replace | Package renamed (javax→jakarta) or removed | javax.persistence-api → jakarta.persistence-api |
| Must Remove | No longer needed on target stack | javax.xml.bind (if not used) |
| Version Bump | Compatible but needs newer version for Java 17 | Lombok 1.18.30+, Jackson 2.17+ |
| No Change | Already compatible with target | Apache Commons, SLF4J |
| Investigate | Unknown compatibility, needs manual check | Internal libraries, CyberArk SDK |

### Prompt Template for Dependency Analysis

```
Given this Maven dependency tree:

[paste dependency:tree output]

Target migration:
- Java 8 → Java 17
- Spring Boot 2.7.x → Spring Boot 3.3.x
- Tomcat 9 → Tomcat 10.1 (container)

Classify every dependency into:
1. MUST UPGRADE (incompatible with target)
2. MUST REPLACE (javax → jakarta rename)
3. MUST REMOVE (no longer needed)
4. VERSION BUMP (needs newer version)
5. NO CHANGE (already compatible)
6. INVESTIGATE (unknown, needs manual check)

For each MUST UPGRADE/REPLACE dependency, provide:
- Current version
- Target version
- Breaking changes to expect
```

## Step 3: RHMTA Report Interpretation

### What RHMTA Produces

RHMTA analyzes source code and produces findings categorized as:

| Category | Meaning | Action Required |
|----------|---------|-----------------|
| Mandatory | Must fix for app to compile/run on target | Always fix before deployment |
| Optional | Should fix for best practices | Fix during migration or as follow-up |
| Potential | May cause issues at runtime | Investigate and test |
| Information | Awareness items | Document, no action |

Each finding includes:
- **Rule ID** — Unique identifier for the issue type
- **Effort (Story Points)** — 1, 3, 5, 8, 13 (Fibonacci scale)
- **Source File** — Affected Java file(s)
- **Description** — What the issue is
- **Message** — Suggested fix

### RHMTA Report Analysis Prompt

```
Here is the RHMTA migration analysis report (exported as CSV/text):

[paste report data]

Migration target: Java 17 + Spring Boot 3.x + Tomcat 10 container

Please:
1. SUMMARIZE total findings by category (mandatory/optional/potential)
2. TOTAL story points by category
3. GROUP mandatory findings by type:
   - Namespace changes (javax → jakarta)
   - Removed APIs (Java EE modules)
   - Server-specific code (Tomcat/WAS bindings)
   - Configuration changes
   - Third-party library incompatibilities
4. IDENTIFY which findings are auto-fixable (regex/IDE refactoring)
   vs manual-fix-required
5. FLAG any findings related to:
   - CyberArk/vault integration
   - Database connectivity (JNDI, DataSource)
   - Security configuration
   - External service integrations
6. ESTIMATE effort:
   - Automated fixes: X story points (Y% of total)
   - Manual fixes: X story points (Y% of total)
   - Investigation needed: X story points
```

### Common RHMTA Rules for Java/Spring Migration

| Rule ID Pattern | What It Detects | Typical Fix |
|-----------------|-----------------|-------------|
| `java-ee-*` | Java EE API usage | Add Jakarta dependency |
| `javax-to-jakarta-*` | javax namespace | Rename to jakarta |
| `spring-boot-*` | Spring Boot deprecated APIs | Follow Spring migration guide |
| `embedded-framework-*` | Server-specific APIs | Replace with standard API |
| `javaee-technology-*` | EJB, JMS, CDI usage | Convert to Spring equivalents |
| `hibernate-*` | Hibernate version issues | Upgrade to Hibernate 6 |

## Step 4: Transformation Advisor Interpretation

### What TA Produces

Transformation Advisor provides:
- **Migration Complexity Score**: Simple, Moderate, Complex, Very Complex
- **Development Cost Estimate**: Days of effort
- **Technology Findings**: Specific incompatibilities
- **Migration Bundle**: Recommended migration approach

### TA Complexity Mapping

| TA Complexity | Typical Characteristics | Estimated Team Effort |
|---------------|------------------------|----------------------|
| Simple | Pure Spring Boot, no server-specific code | 1-2 sprints |
| Moderate | Some Java EE APIs, standard patterns | 2-4 sprints |
| Complex | Heavy EJB, server bindings, custom classloading | 4-8 sprints |
| Very Complex | Tight app server coupling, proprietary APIs | 8+ sprints, possible redesign |

### TA Report Analysis Prompt

```
Here is the Transformation Advisor assessment:

[paste TA report data]

Migration target: Spring Boot 3.x on Tomcat 10 container

Please:
1. Interpret the complexity score — is it accurate for our target?
2. List technology findings grouped by:
   - Blocking (must fix before migration)
   - High effort (significant code changes)
   - Low effort (config/dependency changes)
3. Identify FALSE POSITIVES — findings that don't apply because:
   - We're going TO Spring Boot (not FROM it)
   - We're staying on Tomcat (not moving to a different server)
   - Finding is for a framework we don't actually use
4. Cross-reference with RHMTA findings (identify overlaps)
5. Provide a REVISED effort estimate after removing false positives
```

## Step 5: AMA (Application Modernization Accelerator)

### What AMA Produces

AMA focuses on containerization readiness:
- Application dependency graph
- External service dependencies
- Statefulness assessment
- Resource consumption patterns
- Containerization risk score

### AMA Analysis Prompt

```
Here is the AMA analysis for application [APP_NAME]:

[paste AMA output]

Target: Containerized deployment on Kubernetes

Please assess:
1. CONTAINERIZATION READINESS (1-10 score with justification)
2. BLOCKING ISSUES for containerization:
   - File system dependencies (local file writes/reads)
   - Session stickiness requirements
   - Hardcoded hostnames/IPs
   - JNI/native library dependencies
   - Licensed software embedded (Oracle drivers, etc.)
3. ARCHITECTURE CONCERNS:
   - Stateful vs stateless components
   - External service dependencies that need network policy
   - Shared resources with other applications
4. RECOMMENDED CONTAINERIZATION APPROACH:
   - Lift-and-shift (WAR in Tomcat container) vs
   - Repackage (embedded Tomcat JAR) vs
   - Refactor (break into microservices)
5. ESTIMATED RESOURCE REQUIREMENTS for container
```

## Step 6: Cross-Tool Correlation

### Unified Findings Template

After running all three tools, consolidate findings:

```
CROSS-TOOL CORRELATION for [APP_NAME]

I have findings from three analysis tools:

RHMTA Summary: [X mandatory, Y optional, Z potential — N total story points]
TA Summary: [Complexity: X, Development Cost: Y days]
AMA Summary: [Containerization readiness: X/10]

Combined findings (paste top issues from each tool)

Please:
1. DEDUPLICATE — identify same issue reported by multiple tools
2. GAP ANALYSIS — issues only one tool caught (unique value per tool)
3. UNIFIED PRIORITY LIST — single ranked list removing duplicates:
   Priority 1 (Blocking): [issues]
   Priority 2 (High effort): [issues]
   Priority 3 (Low effort): [issues]
   Priority 4 (Post-migration): [issues]
4. EFFORT SUMMARY:
   - Total unique issues: X
   - Automatable: X (Y%)
   - Manual: X (Y%)
   - Investigation: X (Y%)
5. RECOMMENDED MIGRATION SEQUENCE:
   Phase 1: [what to do first]
   Phase 2: [what depends on Phase 1]
   Phase 3: [cleanup and optimization]
```

## Step 7: Blueprint Analysis Section Generation

### Blueprint Document Template

```
Generate a "Migration Analysis" section for the Blueprint document:

## 1. Application Profile
- Application Name:
- CAI ID:
- Current Stack: [Java version, Spring Boot version, App Server, OS]
- Target Stack: [Java 17/21, Spring Boot 3.x, Tomcat 10 container]
- Repository: [Git URL]
- Team/Owner:

## 2. Dependency Analysis Summary
| Category | Count | Story Points | Automatable |
|----------|-------|-------------|-------------|
| Must Upgrade | | | |
| Must Replace (javax→jakarta) | | | |
| Must Remove | | | |
| Version Bump Only | | | |
| No Change | | | |
| Investigate | | | |

## 3. Migration Tool Findings
### RHMTA Results
- Mandatory: X findings (Y story points)
- Optional: X findings (Y story points)
- Key blockers: [list]

### Transformation Advisor
- Complexity: [Simple/Moderate/Complex]
- Estimated effort: X days
- False positives removed: Y

### AMA Assessment
- Containerization readiness: X/10
- Blocking issues: [list]

## 4. Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|

## 5. Migration Plan
- Phase 1 (Java upgrade): X sprints
- Phase 2 (Spring Boot upgrade): X sprints
- Phase 3 (Containerization): X sprints
- Total estimated: X sprints

## 6. Dependencies & Blockers
- CyberArk integration: [status]
- Database migration: [status]
- External service dependencies: [list]
- Team availability: [constraints]
```

## Gotchas

- **RHMTA reports include false positives** for the Spring Boot target. RHMTA flags ALL Java EE usage, but some is already handled by Spring Boot starters. Filter findings against what Spring Boot auto-configures.
- **TA complexity scores assume full JEE migration**. If you're already on Spring Boot 2.x, the actual complexity is typically 1-2 levels lower than what TA reports (it's designed for WAS/WebLogic migrations).
- **AMA may not detect Spring Boot embedded Tomcat** as containerization-ready. An app with embedded Tomcat is already 80% containerized — just needs a Dockerfile.
- **Maven `dependency:tree` hides managed versions**. Use `mvn dependency:tree -Dverbose` to see the actual resolved versions including conflicts and overrides.
- **Internal/proprietary libraries** won't be recognized by any tool. Manually check all `com.citi.*` and `com.ibm.*` dependencies for Java 17 compatibility.
- **RHMTA story points are generic estimates**. A "5-point" javax→jakarta rename could take 10 minutes with find-and-replace. Use story points for relative prioritization, not sprint planning.
- **Run tools against the SAME branch/commit**. Tool results become inconsistent if the codebase changes between analyses.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| RHMTA shows 0 findings | Check that source code (not just compiled JARs) was analyzed. Verify the migration path is configured correctly (e.g., JBoss → Spring Boot) |
| TA marks everything as "Very Complex" | Likely analyzing against wrong target runtime. Configure target as "Spring Boot on Tomcat" not "Cloud Foundry" or "OpenShift" |
| AMA can't connect to repo | Verify Git credentials and network access. Try cloning locally first |
| Dependency tree too large to paste in Copilot | Filter: `mvn dependency:tree -Dincludes=org.springframework.*,javax.*,jakarta.*,org.hibernate.*` |
| Conflicting findings between tools | Trust RHMTA for code-level issues, TA for effort estimation, AMA for infra/container readiness |
| Tool not available in environment | Use Maven dependency analysis + manual code review as fallback. Copilot can help identify issues from pom.xml + source code |

## Validation

After completing analysis:

- [ ] All three tools run against same codebase version
- [ ] Dependency matrix generated and classified
- [ ] Findings deduplicated across tools
- [ ] False positives identified and removed
- [ ] Priority list created (blocking → nice-to-have)
- [ ] Effort estimated (automated vs manual)
- [ ] Blueprint Analysis section drafted
- [ ] Blockers identified and escalation path defined
- [ ] SME review scheduled for findings validation
