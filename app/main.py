from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import inputs, auth

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(inputs.router, prefix="/inputs", tags=["inputs"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/ping")
async def ping():
    return {"message": "pong"}
