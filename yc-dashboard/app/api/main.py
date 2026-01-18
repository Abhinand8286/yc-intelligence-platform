from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# LOAD ENV FILES
load_dotenv(".env")
load_dotenv(".env.local")

from app.api.ai_explain import router as ai_router

print("AI KEY LOADED:", bool(os.getenv("OPENAI_API_KEY")))

app = FastAPI(title="YC Intelligence API")

#  CORS FIX (THIS IS THE IMPORTANT PART)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router, prefix="/api")
