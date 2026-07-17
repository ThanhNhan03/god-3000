import os
import sys
# Add parent directory of 'backend' to sys.path so we can import 'backend.llm_client' etc.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Migration Harness API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

from fastapi.staticfiles import StaticFiles
from routes import stream, ingest, workspace

app.include_router(stream.router, prefix="/api/agent", tags=["agent"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["workspace"])

# Serve frontend static files
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
