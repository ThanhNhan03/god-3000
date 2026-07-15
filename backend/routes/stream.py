import json
import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from agents.orchestrator import Orchestrator

router = APIRouter()

WORKSPACE_DIR = "/Users/lilnhan/Documents/GitHub/god-3000/workspace/source"

# Global active orchestrator and its task (for demo purposes)
active_orchestrator = None
active_task = None

from backend.llm_client import set_api_key, test_api_key

class TestKeyReq(BaseModel):
    api_key: str

@router.post("/test-key")
async def test_key_endpoint(req: TestKeyReq):
    success = await test_api_key(req.api_key)
    return {"success": success}

@router.get("/stream")
async def stream_agent(prompt: str = "", api_key: str = ""):
    """
    SSE endpoint for streaming orchestrator events.
    """
    global active_orchestrator, active_task
    
    if api_key:
        set_api_key(api_key)
    
    if active_task and not active_task.done():
        active_task.cancel()
        try:
            await active_task
        except asyncio.CancelledError:
            pass

    active_orchestrator = Orchestrator(WORKSPACE_DIR, user_prompt=prompt)
    
    # Start the orchestrator run in the background
    active_task = asyncio.create_task(active_orchestrator.run())

    async def event_generator():
        while True:
            # Wait for an event from the orchestrator
            event_data = await active_orchestrator.queue.get()
            
            yield {
                "event": "message",
                "data": json.dumps(event_data)
            }
            
            if event_data.get("type") == "done":
                break

    return EventSourceResponse(event_generator())

class FeedbackReq(BaseModel):
    feedback: str

@router.post("/verify")
async def verify_plan():
    global active_orchestrator
    if active_orchestrator:
        active_orchestrator.feedback = ""
        active_orchestrator.approval_event.set()
    return {"status": "ok"}

@router.post("/feedback")
async def feedback_plan(req: FeedbackReq):
    global active_orchestrator
    if active_orchestrator:
        active_orchestrator.feedback = req.feedback
        active_orchestrator.approval_event.set()
    return {"status": "ok"}
