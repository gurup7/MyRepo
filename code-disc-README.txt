# Code Discovery Skill - Citi Edition

## Overview

A GitHub Copilot skill that performs deep, automated code discovery on any Java/Spring Boot repository — tailored with Citi-specific patterns, frameworks, and conventions baked in.

This is **not a generic code analyzer**. It understands Citi's internal ecosystem: CMR framework, CyberArk integration, internal `com.citi.*` dependencies, `pipeline.yaml` and `threshold.json` governance files, ACE/Risk service patterns, and enterprise-specific security postures.

## The Problem It Solves

Every time we onboard a new application, assess a codebase for modernization, or prepare for a migration, we spend days engaging the client team to understand:
- What does this service do?
- What are the entry points and key flows?
- What external systems does it talk to?
- What's the deployment model?
- Where are the secrets? Are they handled safely?
- What's tested? What's not?
- What's dead code vs active?

This skill eliminates that repeated engagement. Open the repo, ask Copilot, get a structured discovery report in minutes.

## What Makes This Citi-Specific

| Generic Code Discovery | This Skill |
|----------------------|-----------|
| Finds Spring Boot annotations | Also detects CMR framework patterns (CommonDAO, CMRExceptionHandler, Fault/MoreInfo) |
| Lists dependencies | Also flags `com.citi.*` version drift across sibling services and internal BOM mismatches |
| Identifies config files | Also parses `pipeline.yaml` stages, `threshold.json` quality gates, and `renovate.json` policies |
| Finds hardcoded values | Also checks CyberArk/Vault integration posture and flags plaintext credential fallbacks as Critical |
| Maps REST endpoints | Also identifies Citi service discovery patterns (Eureka), TIBCO/JMS enterprise messaging, and internal framework wiring |
| Flags dead code | Also detects cross-service boilerplate duplication common in Citi monorepos and recommends shared library extraction |
| Documents security | Also understands dual datasource patterns, JNDI SSL settings, and CyberArk startup risk sequences |

## Files

| File | Purpose | Who Reads It |
|------|---------|-------------|
| `SKILL.md` | Describes capabilities, when to use, example prompts | You and your team |
| `copilot-instructions.md` | Detailed behavioral rules Copilot follows | Copilot (the AI) |
| `README.md` | This file. Quick overview and setup guide | Everyone |

## Setup

1. Copy the `CodeDiscovery/` folder into your project root (or `.github/skills/code-discovery/`)
2. Copy `copilot-instructions.md` to `.github/copilot-instructions.md` in the target repo
3. Open the project in IntelliJ/VS Code with GitHub Copilot Chat enabled
4. Start asking questions

## Usage

Open Copilot Chat and ask:

### Full Discovery
```
@workspace Produce a complete code discovery report for this repository.
```

### Specific Flow
```
@workspace Trace the payment processing flow from controller to database.
```

### Pre-Migration
```
@workspace Analyze this codebase for containerization readiness. Flag hardcoded paths, file I/O, and missing health checks.
```

### Security Audit
```
@workspace Identify all authentication mechanisms, secrets handling, input validation gaps, and vulnerable dependencies.
```

### Cross-Service Analysis (Monorepo)
```
@workspace Compare all services in this workspace. Which share duplicated boilerplate? Are internal dependency versions consistent?
```

### Dependency Risk
```
@workspace List all external dependencies with versions. Flag deprecated, EOL, or vulnerable ones.
```

## What You Get Back

A structured report with:

1. **Repository Summary** — stack, versions, module layout
2. **Entry Points** — every way code gets triggered (HTTP, messaging, scheduler, batch)
3. **Business Logic Map** — traced flows with class chains and file paths
4. **Component Breakdown** — services, repositories, configurations
5. **Configuration Inventory** — profiles, env overrides, secrets sources
6. **External Dependencies** — APIs, databases, messaging, cloud, with contract details
7. **Test Coverage Posture** — what's tested, what's not, quality indicators
8. **Security Posture** — auth, authz, validation, vulnerable deps
9. **Unused/Suspicious Code** — with confidence levels and evidence
10. **Risks and Observations** — prioritized findings
11. **Follow-Up Actions** — security first, then operational, then modernization

## Requirements

- GitHub Copilot Chat (IntelliJ or VS Code)
- Repository cloned locally (or accessible via workspace)
- No additional tools or installations

## Limitations

- Static analysis only — cannot detect runtime-only behavior (reflection, dynamic proxies)
- Large monorepos may require module-scoped prompts for best results
- Copilot context window limits apply — for 50+ module repos, analyze in batches
- Does not execute code or run tests

## Contributing

To extend with new Citi profile patterns:
1. Add detection indicators to the "Citi Common Pattern Reference" table in `copilot-instructions.md`
2. Add corresponding checks under the relevant Layer
3. Update the Quality Checklist
4. Add example prompts to SKILL.md
