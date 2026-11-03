Hi Team,

Based on our recent discussions, we understand that there have been frequent code changes across the Retail Risk and ACE Digital applications, involving both manual changes and the use of Devin.

We have also observed multiple SonarQube and Snyk vulnerabilities being reported in the main branch, which required the team to address them during the recent code cut.

To get a better understanding of the current development and release practices, could you please clarify the following:

Code Changes: Are the frequent code changes (manual/Devin-assisted) being merged only into the main branch, or have these changes also been deployed to production?

Vulnerability Management: Are code changes with open SonarQube/Snyk vulnerabilities being released to production, or are these vulnerabilities addressed before deployment?

Production Fixes: Are the teams carrying out production fixes or hotfixes frequently? If yes, how are these changes managed and merged back into the main branch?

CI/CD Pipeline: Are the applications using Jenkins pipelines for build, code quality checks, security scanning, and deployment, or are they leveraging LSE?

This information will help us understand the current development and release practices, identify any gaps, and align on the appropriate approach going forward.
