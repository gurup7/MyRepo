# Code Discovery Skill

## What This Skill Does

Analyzes an existing codebase and produces a structured discovery report covering:

- Application purpose and architecture
- Entry points and execution flow
- Business logic mapping
- Component/class inventory
- Configuration and runtime dependencies
- External integrations (databases, APIs, messaging)
- Unused, dead, or obsolete code identification
- Modernization and refactoring opportunities
- **Citi-specific:** Internal framework usage, CyberArk secret retrieval patterns, pipeline/quality-gate inventory, and cross-service boilerplate duplication

## Primary Target

Java and Spring Boot applications. Adaptable to other JVM-based or general backend codebases.

**Optimized for:** Citi enterprise repositories using profile-based discovery (CMR services, ACE/Risk services, and mixed Java/Python delivery repos) with evidence-first detection of framework, pipeline, and security patterns.

## When to Activate

Use this skill when you need to:

| Goal | Example Prompt |
|------|---------------|
| Understand a codebase | "What does this application do?" |
| Map business logic | "Trace the order processing flow end-to-end" |
| Generate documentation | "Produce a component inventory for this module" |
| Find dead code | "Which classes and methods appear unused?" |
| Identify config requirements | "What configuration is needed to run this?" |
| Prepare for modernization | "What should be refactored or removed?" |
| Onboard new developers | "Create a handover document for this service" |
| Audit Citi-specific patterns | "Are CyberArk and pipeline configs correct across all services?" |
| Check quality gates | "What are the SonarQube/Snyk thresholds for this service?" |
| Find cross-service duplication | "Which boilerplate classes are duplicated across sibling services?" |
| Discover API surface | "What APIs does this service expose? What are the request/response contracts?" |
| Assess test coverage | "Which critical paths have no test coverage?" |
| Security audit | "Identify authentication/authorization gaps and input validation issues" |
| Data model review | "Map all JPA entities and their relationships" |
| Deployment readiness | "What's needed to containerize this service?" |
| Dependency risk | "List all external dependencies and flag deprecated or vulnerable ones" |

## How It Works

The skill instructs Copilot to analyze code in layers:

1. **Structure first** — identify module layout, build system, runtime stack, and Citi profile indicators (CMR, ACE/Risk, batch, Python)
2. **Entry points** — locate `main()`/Boot apps, controllers, runners, listeners, schedulers, and script launchers
3. **Flows** — trace request/data/event flows through service layers and data/integration boundaries; include framework-specific DAO wiring only when present
4. **Configuration** — map config files, profiles, environment overrides, secrets providers, governance files (`pipeline.yaml`, `threshold.json`)
5. **External integrations** — catalog databases, APIs, messaging, caching, cloud services, and Citi-specific framework dependencies
6. **API contracts** — document API surface (OpenAPI specs, versioning, DTOs, error contracts, pagination)
7. **Data model** — map JPA entities, relationships, migrations, schema ownership per service
8. **Deployment context** — identify containerization artifacts, health checks, scaling config, inter-service patterns
9. **Test coverage** — assess unit/integration test presence, coverage gaps, and test quality
10. **Security posture** — auth mechanisms, authorization model, input validation, CORS, vulnerable dependencies
11. **Dead code** — flag unreferenced classes, uncalled methods, stale artifacts, and cross-service boilerplate duplication
12. **Report** — produce findings in a consistent numbered format with prioritized follow-up actions

## Discovery Workflow (Recommended)

Use this execution sequence to improve consistency in large workspaces:

1. **Scope first** — identify modules included and explicitly list modules not covered.
2. **Read build files first** — determine versions, module graph, packaging, parent BOM usage, and Citi internal dependencies (`com.citi.*`).
3. **Read governance files** — inspect `pipeline.yaml`, `threshold.json`, and `renovate.json`; capture actual stage names, promoted environments, and gate values from file contents.
4. **Collect entry points** — HTTP, batch, message listeners, schedulers, startup hooks, and non-Java launchers/scripts where present.
5. **Trace 2-5 critical flows** — inbound trigger -> service -> data/integration boundary with concrete class/file-path chains.
6. **Inventory runtime config** — profiles, XML/property overlays, datasource and messaging blocks, secrets providers (CyberArk/Vault/env), and TLS/cert settings. Flag plaintext credentials as **Critical**.
7. **Flag risk and dead code** — attach confidence and caveats. Check for repeated boilerplate patterns across sibling services and version drift in shared internal dependencies.
8. **Close with prioritized actions** — security/credential issues first, operational risks second, quick wins third, modernization items last.

## Output Format

Reports follow this structure:

1. Repository Summary
2. Entry Points
3. Business Logic Map
4. Component Breakdown
5. Configuration Inventory
6. External Dependencies (API Contracts, Data Model, Deployment Topology)
7. Test Coverage Posture
8. Security Posture
9. Unused or Suspicious Code
10. Risks and Observations
11. Suggested Follow-Up Actions

## Required Output Additions

Include these short blocks before section 1 for better transparency:

- **Modules Covered**: exact modules analyzed in this pass
- **Modules Not Covered**: modules intentionally skipped or not yet analyzed
- **Evidence Standard**: all key findings must cite class + file path
- **Confidence Usage**: `Confirmed`, `Likely`, `Uncertain`, `Assumption`

## Key Principles

- **Evidence over assumptions** — findings cite specific files and classes
- **Uncertainty is stated explicitly** — if the code is ambiguous, the report says so
- **No invented business meaning** — only what the code actually demonstrates
- **Read-only by default** — no modifications unless explicitly requested
- **Layered analysis** — structure first, details second, for large codebases
- **Coverage transparency** — state what was and was not analyzed in every report
- **No silent assumptions** — prefix inferred behavior with confidence label

## Scope Guardrails

Unless explicitly requested, exclude:

- Compiled/generated outputs (`target/`, `build/`, `out/`, generated stubs)
- Dependency/vendor folders (`node_modules/`, `.gradle/`, `.mvn/`)
- VCS internals (`.git/`)

If the workspace is large, summarize by module first and offer drill-down follow-ups.

## Citi Common Pattern Reference

When analyzing Citi repositories, treat patterns as profile-based and confirm each one from evidence:

| Pattern | Indicator | Why It Matters |
|---------|-----------|----------------|
| Internal dependency profile | `com.citi.*` artifacts and BOM parents in `pom.xml` | Version drift/exclusions can change runtime behavior across sibling modules |
| Governance files | `pipeline.yaml`, `threshold.json`, `renovate.json` in module root | CI/CD path and quality gates must be reported from source-of-truth files |
| Delivery packaging hooks | `maven-antrun-plugin`, `exec-maven-plugin`, `install/`, `scripts/` | Final deliverable may be assembled outside plain `target/` artifacts |
| Hybrid Spring configuration | `@ImportResource` + `spring*.xml` + property/yaml files | Bean wiring and env overrides may live in XML, not only annotations |
| Secrets integration | CyberArk/Vault/env settings or bootstrap scripts | Plaintext credentials or fallback secrets are critical findings |
| TLS/certificate posture | flags like disabled cert/hostname validation | Weak transport security is a high-impact operational risk |
| Quality gate source | `threshold.json` key/value inspection | Thresholds vary by repo; do not hardcode values in reports |
| Pipeline variability | build task can differ (`java-maven-build`, `python-build`, etc.) | Stage names/order are not universal; parse actual pipeline content |
| Optional CMR profile | `cmr-em-microserviceframework`, `CommonDAO`, `CMRExceptionHandler` | Enables framework-specific checks only when this profile is present |

### Cross-Service Boilerplate Duplication Rule
In workspaces with >= 3 sibling services in the same profile:
- If startup/security/config wrappers are near-identical across services -> **flag for shared library extraction**
- If exception handlers are single-exception thin wrappers everywhere -> **flag for consolidation**
- If DAO/service scaffolding repeats with minimal domain variance -> **flag for templating or framework centralization**

## Quality Checklist

Before finalizing a discovery report, verify:

- [ ] Build system and versions are confirmed from build files
- [ ] Module profile identified per service (CMR, ACE/Risk, Python, library, batch)
- [ ] Internal dependency versions and major exclusions reviewed for cross-module drift
- [ ] Entry points listed for each covered module (including non-HTTP/script runners when present)
- [ ] At least one flow is traced per major runtime style (HTTP, batch, messaging)
- [ ] Config/profile files inventoried (including XML imports); secret sources checked for plaintext leakage
- [ ] API contracts documented (endpoints, DTOs, error model, versioning)
- [ ] Data model mapped (entities, relationships, migrations, shared tables flagged)
- [ ] Deployment artifacts identified (Dockerfile, K8s manifests, health checks, scaling config)
- [ ] Test coverage assessed (ratio, gaps in critical paths, test quality indicators)
- [ ] Security posture reviewed (auth, authz, input validation, CORS, vulnerable deps)
- [ ] `threshold.json` quality gates documented from actual file values per module
- [ ] `pipeline.yaml` stages/environments documented from actual file content per module
- [ ] Dead/suspicious code includes confidence and caveat notes
- [ ] Cross-service boilerplate duplication checked for each detected profile
- [ ] Follow-up actions prioritized: security → operational → test gaps → maintainability → modernization

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file. Describes the skill for humans. |
| `.github/copilot-instructions.md` | System-level directives that Copilot follows when this skill is active. |

## Usage

In GitHub Copilot Chat, reference the workspace and ask discovery questions:

```
@workspace What does this application do? Produce a code discovery report.
```

```
@workspace Trace the payment processing flow from controller to database.
```

```
@workspace Which classes in the service layer appear unused?
```

```
@workspace List all configuration files and explain what each controls.
```

```
@workspace Are CyberArk and pipeline configs consistent across all services?
```

```
@workspace What quality gates are enforced and are any services at risk of failing them?
```

For large monorepos, scope your question to a module:

```
@workspace Analyze the order-service module and produce a discovery report.
```

## Common Discovery Scenarios (Ready-to-Use Prompts)

### Full Codebase Onboarding
```
@workspace Produce a complete code discovery report covering all layers. I'm a new developer joining this team and need to understand the architecture, key flows, and dependencies.
```

### Pre-Containerization Assessment
```
@workspace Analyze this codebase for containerization readiness. Flag hardcoded paths, file I/O to local disk, localhost references, missing health checks, and environment-specific coupling.
```

### Security Audit Preparation
```
@workspace Identify all authentication and authorization mechanisms, secrets handling patterns, input validation gaps, CORS config, and potential SQL injection surfaces. Flag critical findings first.
```

### Dependency Risk Check
```
@workspace List all external dependencies with versions. Flag any that are deprecated, end-of-life, have known CVEs, or are internal Citi dependencies with version drift across modules.
```

### Technical Debt Inventory
```
@workspace Find dead code, duplicated logic across services, untested critical paths, and overly complex methods. Prioritize findings by impact and provide effort estimates for cleanup.
```

### API Surface Documentation
```
@workspace Document all REST APIs this service exposes. For each endpoint: HTTP method, path, request/response DTOs, validation rules, and error responses. Note any undocumented endpoints.
```

### Pre-Migration Impact Analysis
```
@workspace We plan to upgrade from Java 11 to 21 and Spring Boot 2.x to 3.x. Identify all code that will break: javax.* imports, removed/deprecated APIs, incompatible dependencies, and configuration changes needed.
```

### Cross-Service Architecture Map
```
@workspace Map all inter-service communication in this workspace. Show which service calls which, the protocol used (REST/messaging/gRPC), and identify any circular dependencies or tight coupling.
```


---

## EDT Enhancement: Containerization & Upgrade Discovery

### Additional Capabilities (EDT-Specific)

This skill has been enhanced with `copilot-instructions-edt.md` to support the EDT (eDeal Tickets) multi-repo analysis. The enhancement adds:

| Layer | Capability | Purpose |
|-------|-----------|---------|
| **Layer 9** | Containerization Readiness Assessment | Identifies blockers, warnings, and ready indicators for OpenShift |
| **Layer 10** | Technology Upgrade Assessment | EJB inventory, WebSphere deps, JSP→Angular scope, NDM strategy, DB access |
| **Layer 11** | Integration Mapping | Cross-repo integration matrix with containerization impact |
| **Layer 12** | Containerization Recommendation | Per-component deployment strategy, base images, pod estimates |
| **Layer 13** | Migration Roadmap | Phased approach with effort estimates and risk register |

### How to Use for EDT

1. **Import all 5 repos** into a single workspace folder
2. **Activate the EDT skill** by referencing the EDT copilot instructions:

```
@workspace #file:CodeDiscovery/copilot-instructions-edt.md

Analyze all EDT repositories and produce a containerization readiness report.
```

3. **Use targeted prompts** for specific areas:

| Goal | Prompt |
|------|--------|
| Full system analysis | `@workspace Analyze all 5 EDT repositories. Produce complete discovery + containerization readiness.` |
| EJB migration scope | `@workspace Inventory all EJBs with migration targets and effort.` |
| Integration map | `@workspace Map all integrations. Document containerization impact.` |
| NDM replacement | `@workspace Analyze NDM processes. Recommend container-friendly alternatives.` |
| Per-repo deep dive | `@workspace Analyze the Java backend repo. Focus on WebSphere dependencies and EJB patterns.` |
| Complexity rating | `@workspace Rate complexity for containerizing each EDT component. Provide phased roadmap.` |

### EDT Repository Setup

Recommended folder structure for multi-repo analysis:

```
EDT/
├── edt-ui/                  # Angular + legacy JSP
├── edt-java/                # Java backend (EJB, Servlets, Services)
├── edt-batch/               # Batch processing jobs
├── edt-ndm/                 # NDM/Connect:Direct configurations
├── edt-sql/                 # Database schemas, stored procs, migrations
└── CodeDiscovery/           # This skill (copy here or reference from parent)
    ├── SKILL.md
    ├── copilot-instructions.md
    └── copilot-instructions-edt.md
```

### Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — describes the skill |
| `copilot-instructions.md` | Base code discovery rules (all Java/Spring Boot apps) |
| `copilot-instructions-edt.md` | EDT-specific enhancements (containerization, upgrades, multi-repo) |
