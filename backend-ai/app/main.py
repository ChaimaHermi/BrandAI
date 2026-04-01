from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import clarifier, market_analysis, pipeline


app = FastAPI(title="BrandAI — IA Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clarifier.router, prefix="/api/ai")
app.include_router(market_analysis.router, prefix="/api/ai")
app.include_router(pipeline.router, prefix="/api/ai")


@app.get("/health")
def health():
    return {"status": "ok", "service": "brandai-ai"}

