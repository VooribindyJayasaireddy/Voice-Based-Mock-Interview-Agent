from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.interview import router

app = FastAPI(title="Voice Mock Interview Agent")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create audio directory if it doesn't exist
os.makedirs("audio", exist_ok=True)

# Mount static files directory
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

app.include_router(router, prefix="/interview")
