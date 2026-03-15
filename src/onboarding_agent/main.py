#!/usr/bin/env python
import sys
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """Start the FastAPI server with uvicorn."""
    import uvicorn
    uvicorn.run(
        "onboarding_agent.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


def train():
    """Train the OnboardingCrew for N iterations."""
    from onboarding_agent.crew import OnboardingCrew

    inputs = {
        "employee_name": "Test Employee",
        "github_username": "testuser",
        "employee_role": "Software Engineer",
        "department": "Engineering",
    }
    try:
        OnboardingCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"Training error: {e}")


def replay():
    """Replay OnboardingCrew from a specific task ID."""
    try:
        from onboarding_agent.crew import OnboardingCrew
        OnboardingCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"Replay error: {e}")


def test():
    """Test OnboardingCrew execution."""
    from onboarding_agent.crew import OnboardingCrew

    inputs = {
        "employee_name": "Test Employee",
        "github_username": "testuser",
        "employee_role": "Software Engineer",
        "department": "Engineering",
    }
    try:
        OnboardingCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"Test error: {e}")
