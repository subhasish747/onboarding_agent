from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from onboarding_agent.tools.github_tool import GitHubTeamTool
from onboarding_agent.tools.rag_tool import OnboardingRAGTool


@CrewBase
class OnboardingCrew:
    """
    Onboarding crew: classifies employee role via RAG, adds them to the
    appropriate GitHub team (developer or readonly), and generates a report.
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def role_classifier(self) -> Agent:
        return Agent(
            config=self.agents_config["role_classifier"],  # type: ignore[index]
            tools=[OnboardingRAGTool()],
            verbose=True,
        )

    @agent
    def github_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["github_manager"],  # type: ignore[index]
            tools=[GitHubTeamTool()],
            verbose=True,
        )

    @agent
    def onboarding_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["onboarding_reporter"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def classify_role_task(self) -> Task:
        return Task(config=self.tasks_config["classify_role_task"])  # type: ignore[index]

    @task
    def github_onboard_task(self) -> Task:
        return Task(config=self.tasks_config["github_onboard_task"])  # type: ignore[index]

    @task
    def onboarding_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["onboarding_report_task"],  # type: ignore[index]
            output_file="onboarding_report.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class OffboardingCrew:
    """
    Offboarding crew: removes employee from all GitHub teams and generates a report.
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def github_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["github_manager"],  # type: ignore[index]
            tools=[GitHubTeamTool()],
            verbose=True,
        )

    @agent
    def offboarding_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["offboarding_reporter"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def github_offboard_task(self) -> Task:
        return Task(config=self.tasks_config["github_offboard_task"])  # type: ignore[index]

    @task
    def offboarding_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["offboarding_report_task"],  # type: ignore[index]
            output_file="offboarding_report.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
