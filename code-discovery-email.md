
Hi Team,

I've developed a Code Discovery skill for GitHub Copilot that automates codebase analysis — specifically built for our Citi environment and the applications we work with.

The Pain Point

Every time we take on a new application or prepare for a migration, we spend significant time engaging client teams to understand their codebase: What does it do? What are the dependencies? How are secrets managed? What's the deployment model? What's tested?

This repeated engagement costs days per application and creates dependency on client availability.

What I've Built

A Copilot skill (two markdown files) that, when placed in any repository, gives Copilot deep knowledge of how to analyze Citi Java/Spring Boot applications. You open the repo, ask a question in Copilot Chat, and get a structured discovery report.

This is not generic code discovery. It has Citi-specific intelligence baked in:

Detects CMR framework patterns (CommonDAO, CMRExceptionHandler, Fault/MoreInfo error model)
Checks CyberArk/Vault integration posture and flags plaintext credential fallbacks as Critical
Parses pipeline.yaml and threshold.json for actual CI/CD stages and quality gate values
Tracks com.citi.* internal dependency versions and flags drift across sibling services
Identifies enterprise messaging patterns (TIBCO, JMS, Kafka with JNDI/SSL settings)
Flags cross-service boilerplate duplication and recommends shared library extraction
Covers 12 analysis layers: structure, entry points, flows, config, integrations, API contracts, data model, deployment context, test coverage, security posture, dead code, and risks
How It Works

Drop two files into the repo (
copilot-instructions.md
 + SKILL.md)
Open in IntelliJ/VS Code with Copilot Chat
Ask: @workspace Produce a complete code discovery report
Get a structured 11-section report with file paths, evidence, and prioritized actions
No tools to install. No Python. No CLI. Just your existing Copilot license.

Example Questions You Can Ask

"Trace the payment processing flow end-to-end"
"Which critical paths have no test coverage?"
"Are CyberArk and pipeline configs consistent across all services?"
"Analyze this for containerization readiness"
"Map all inter-service communication and identify circular dependencies"
What This Means for Us

Eliminate days of client engagement for codebase understanding
Consistent, repeatable discovery output across all applications
New team members can self-onboard to any codebase
Pre-migration assessments in minutes instead of days
Security and dependency risks surfaced automatically
The skill files are ready to use. Happy to walk through it in a 15-minute session or share the files directly.
