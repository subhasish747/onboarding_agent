import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception


class GitHubTeamInput(BaseModel):
    action: str = Field(description="Action to perform: 'add' or 'remove'")
    github_username: str = Field(description="GitHub username of the employee")
    team_slug: str = Field(
        description="GitHub team slug: 'developer' or 'readonly'"
    )


class GitHubTeamTool(BaseTool):
    name: str = "GitHub Team Manager"
    description: str = (
        "Manages GitHub organization team memberships. "
        "Use to add or remove an employee from the 'developer' or 'readonly' team in the GitHub org."
    )
    args_schema: type[BaseModel] = GitHubTeamInput

    def _run(self, action: str, github_username: str, team_slug: str) -> str:
        token = os.getenv("GITHUB_TOKEN")
        org_name = os.getenv("GITHUB_ORG")

        if not token or not org_name:
            return (
                "ERROR: GITHUB_TOKEN and GITHUB_ORG environment variables must be set. "
                "Simulating success for POC: would have "
                f"{'added' if action == 'add' else 'removed'} @{github_username} "
                f"{'to' if action == 'add' else 'from'} the '{team_slug}' team."
            )

        if Github is None:
            return "ERROR: PyGithub is not installed. Run: pip install PyGithub"

        try:
            g = Github(token)
            org = g.get_organization(org_name)
            team = org.get_team_by_slug(team_slug)
            user = g.get_user(github_username)

            if action == "add":
                team.add_membership(user)
                return (
                    f"SUCCESS: Added @{github_username} to '{team_slug}' team "
                    f"in the {org_name} GitHub organization."
                )
            elif action == "remove":
                team.remove_membership(user)
                return (
                    f"SUCCESS: Removed @{github_username} from '{team_slug}' team "
                    f"in the {org_name} GitHub organization."
                )
            else:
                return f"ERROR: Unknown action '{action}'. Use 'add' or 'remove'."

        except GithubException as e:
            msg = e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
            return f"GitHub API error: {msg}"
        except Exception as e:
            return f"Unexpected error: {e}"
