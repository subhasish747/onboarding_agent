# Onboarding Role Policies

## GitHub Team Assignment Rules

### Developer Team (team slug: developer)
Employees with the following roles are assigned to the Developer team.
The Developer team has read and write access to all engineering repositories.

Roles in the Developer team:
- Software Engineer
- Senior Software Engineer
- Staff Engineer
- Principal Engineer
- Lead Engineer
- Backend Engineer
- Frontend Engineer
- Full Stack Engineer
- DevOps Engineer
- Platform Engineer
- Site Reliability Engineer
- SRE
- Data Engineer
- ML Engineer
- AI Engineer
- Security Engineer
- Mobile Engineer
- iOS Engineer
- Android Engineer

### ReadOnly Team (team slug: readonly)
Employees with the following roles are assigned to the ReadOnly team.
The ReadOnly team has read-only access to repositories for visibility purposes.

Roles in the ReadOnly team:
- Product Manager
- Senior Product Manager
- Project Manager
- Program Manager
- Business Analyst
- QA Analyst
- Quality Assurance Engineer
- Designer
- UX Designer
- UI Designer
- Technical Writer
- Documentation Specialist
- Scrum Master
- Agile Coach
- Marketing Manager
- Sales Engineer
- Customer Success Manager
- Account Manager
- HR Manager
- Recruiter
- Finance Analyst
- Legal Counsel

## Default Rule
If a role is not listed above, apply this rule:
- If the role contains "Engineer", "Developer", "Architect", or "Scientist": assign to developer team
- Otherwise: assign to readonly team

## Onboarding Process
1. New employee submits onboarding request with name, role, department, and GitHub username
2. Role Classifier agent searches this knowledge base to determine the correct GitHub team
3. GitHub Manager agent adds the employee to the appropriate team
4. Onboarding Reporter generates a summary report

## Offboarding Process
1. Departing employee offboarding is triggered with name and GitHub username
2. GitHub Manager agent removes the employee from all teams (developer and readonly)
3. Offboarding Reporter generates a confirmation report

## Team Descriptions
- **developer**: Full repository access for engineering contributors. Members can push code, review PRs, and manage issues.
- **readonly**: Read-only repository access for non-engineering stakeholders. Members can view code and issues but cannot push.
