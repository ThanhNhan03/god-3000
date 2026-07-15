import json
import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from agents.orchestrator import Orchestrator

router = APIRouter()

WORKSPACE_DIR = "/Users/lilnhan/Documents/GitHub/god-3000/workspace/source"

@router.get("/stream")
async def stream_agent():
    """
    SSE endpoint for streaming orchestrator events.
    """
    orchestrator = Orchestrator(WORKSPACE_DIR)
    
    # Start the orchestrator run in the background
    asyncio.create_task(orchestrator.run())

    async def event_generator():
        while True:
            # Wait for an event from the orchestrator
            event_data = await orchestrator.queue.get()
            
            yield {
                "event": "message",
                "data": json.dumps(event_data)
            }
            
            if event_data.get("type") == "done":
                break

    return EventSourceResponse(event_generator())
