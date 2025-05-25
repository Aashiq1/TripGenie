from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import inputs

app = FastAPI()

# Basic CORS setup (use stricter config in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inputs.router)

@app.get("/ping")
def ping():
    return {"message": "pong"}
