"""
FastAPI application for the Onboarding/Offboarding Agent.

Endpoints:
  GET  /health            - health check
  POST /onboard           - onboard a new employee
  POST /offboard          - offboard a departing employee
  POST /rag/reindex       - drop and re-index the ChromaDB knowledge base
  GET  /docs              - Swagger UI (auto-generated)
"""

import warnings
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI(
    title="Employee Onboarding/Offboarding Agent",
    description=(
        "AI-powered HR automation using CrewAI + Ollama (RAG) + GitHub.\n\n"
        "Automatically assigns new employees to the correct GitHub team based on their role, "
        "and removes access when they leave."
    ),
    version="0.1.0",
)


# --------------------------------------------------------------------------- #
# Request / Response models
# --------------------------------------------------------------------------- #


class OnboardRequest(BaseModel):
    employee_name: str
    github_username: str
    employee_role: str
    department: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_name": "Alice Smith",
                    "github_username": "alice-smith",
                    "employee_role": "Senior Software Engineer",
                    "department": "Platform Engineering",
                },
                {
                    "employee_name": "Bob Jones",
                    "github_username": "bob-jones",
                    "employee_role": "Product Manager",
                    "department": "Product",
                },
            ]
        }
    }


class OffboardRequest(BaseModel):
    employee_name: str
    github_username: str
    reason: Optional[str] = "Resignation"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_name": "Alice Smith",
                    "github_username": "alice-smith",
                    "reason": "Resignation",
                }
            ]
        }
    }


class AgentResponse(BaseModel):
    status: str
    employee: str
    github_username: str
    report: str


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "onboarding-agent"}


@app.post("/onboard", response_model=AgentResponse, tags=["Onboarding"])
def onboard(request: OnboardRequest):
    """
    Onboard a new employee:
    1. Classifies their role using Ollama RAG against company policies
    2. Adds them to the appropriate GitHub team (developer or readonly)
    3. Returns an onboarding report
    """
    from onboarding_agent.crew import OnboardingCrew

    inputs = {
        "employee_name": request.employee_name,
        "github_username": request.github_username,
        "employee_role": request.employee_role,
        "department": request.department,
    }
    try:
        result = OnboardingCrew().crew().kickoff(inputs=inputs)
        return AgentResponse(
            status="success",
            employee=request.employee_name,
            github_username=request.github_username,
            report=str(result),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/offboard", response_model=AgentResponse, tags=["Offboarding"])
def offboard(request: OffboardRequest):
    """
    Offboard a departing employee:
    1. Removes them from all GitHub teams (developer and readonly)
    2. Returns an offboarding report
    """
    from onboarding_agent.crew import OffboardingCrew

    inputs = {
        "employee_name": request.employee_name,
        "github_username": request.github_username,
        "reason": request.reason or "Resignation",
    }
    try:
        result = OffboardingCrew().crew().kickoff(inputs=inputs)
        return AgentResponse(
            status="success",
            employee=request.employee_name,
            github_username=request.github_username,
            report=str(result),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/reindex", tags=["RAG"])
def rag_reindex():
    """
    Drop and re-index the ChromaDB knowledge base from knowledge/*.md files.
    Call this after editing role policies without restarting the server.
    """
    from onboarding_agent.tools.rag_tool import reindex

    try:
        count = reindex()
        return {"status": "ok", "chunks_indexed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
