import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import inputs, auth, trip, activities
# from app.api import trip_refinement_endpoints  # Temporarily disabled due to type annotation issue

# Initialize FastAPI app
app = FastAPI(
    title="TripGenie - AI Travel Agent",
    description="Intelligent group trip planning powered by AI",
    version="2.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(inputs.router, prefix="/inputs")
app.include_router(auth.router, prefix="/auth")
app.include_router(trip.router, prefix="/trip")
app.include_router(activities.router, prefix="/activities")
# app.include_router(trip_refinement_endpoints.router)  # Temporarily disabled

@app.get("/")
async def root():
    return {
        "message": "🧳 TripGenie AI Travel Agent", 
        "version": "2.0.0",
        "features": ["AI-powered destination recommendations", "Intelligent itinerary planning", "Real-time cost analysis"],
        "ai_status": "🤖 AI agents ready" if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") else "⚠️ AI not configured"
    }

@app.get("/ping")
async def ping():
    return {"message": "TripGenie AI is alive! 🤖✈️"}
