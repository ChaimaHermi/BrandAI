from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.step_runner_service import StepRunnerService


router = APIRouter(tags=["Market Strategy"])
step_runner = StepRunnerService()


class MarketStrategyStreamRequest(BaseModel):
    idea_id: int
    access_token: str


async def _stream_market_strategy(body: MarketStrategyStreamRequest):
    try:
        async for chunk in step_runner.stream_market_strategy(
            idea_id=body.idea_id,
            access_token=body.access_token,
        ):
            yield chunk
    except Exception as e:
        yield step_runner.sse_event("error", {"success": False, "message": str(e)})
        yield step_runner.sse_event("done", {"success": False})


@router.post("/market-strategy/stream")
async def market_strategy_stream(body: MarketStrategyStreamRequest):
    return StreamingResponse(
        _stream_market_strategy(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
