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

## Primary Target

Java and Spring Boot applications. Adaptable to other JVM-based or general backend codebases.

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

## How It Works

The skill instructs Copilot to analyze code in layers:

1. **Structure first** — identify the project layout, build system, and framework
2. **Entry points** — locate main classes, controllers, schedulers, listeners
3. **Flows** — trace request/data/event flows through service layers
4. **Dependencies** — map external integrations and config requirements
5. **Dead code** — flag unreferenced classes, uncalled methods, stale artifacts
6. **Report** — produce findings in a consistent numbered format

## Output Format

Reports follow this structure:

1. Repository Summary
2. Entry Points
3. Business Logic Map
4. Component Breakdown
5. Configuration Inventory
6. External Dependencies
7. Unused or Suspicious Code
8. Risks and Observations
9. Suggested Follow-Up Actions

## Key Principles

- **Evidence over assumptions** — findings cite specific files and classes
- **Uncertainty is stated explicitly** — if the code is ambiguous, the report says so
- **No invented business meaning** — only what the code actually demonstrates
- **Read-only by default** — no modifications unless explicitly requested
- **Layered analysis** — structure first, details second, for large codebases

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

For large monorepos, scope your question to a module:

```
@workspace Analyze the order-service module and produce a discovery report.
```
