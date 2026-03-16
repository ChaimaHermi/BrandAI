from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from agents.base_agent import PipelineState
from agents.idea_clarifier import IdeaClarifierAgent


router = APIRouter(tags=["Idea Clarifier"])


class ClarifierStartRequest(BaseModel):
    idea_id: int
    name: str
    sector: str
    description: str
    target_audience: Optional[str] = ""


class ClarifierAnswerRequest(BaseModel):
    idea_id: int
    name: str
    sector: str
    description: str
    target_audience: Optional[str] = ""
    answers: List[str]


@router.post("/clarifier/start")
async def clarifier_start(body: ClarifierStartRequest):
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name,
        sector=body.sector,
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()
    result = await agent.run_interactive(state, user_answers=None)
    return result


@router.post("/clarifier/answer")
async def clarifier_answer(body: ClarifierAnswerRequest):
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name,
        sector=body.sector,
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()
    result = await agent.run_interactive(state, user_answers=body.answers)
    return result

