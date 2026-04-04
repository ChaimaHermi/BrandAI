import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import clarifier, logo, market_analysis, naming, palette, pipeline, slogan

# Uvicorn configure le logging avant l’import : `basicConfig` peut être ignoré ; sans cela le
# niveau root reste souvent WARNING et les INFO de `brandai.*` ne s’affichent pas.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)
_root = logging.getLogger()
_root.setLevel(logging.INFO)
if not _root.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    _root.addHandler(_h)
for _name in ("brandai", "brandai.logo_agent", "brandai.logo_image_client", "brandai.llm_rotator"):
    logging.getLogger(_name).setLevel(logging.INFO)

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
app.include_router(naming.router, prefix="/api/ai")
app.include_router(slogan.router, prefix="/api/ai")
app.include_router(palette.router, prefix="/api/ai")
app.include_router(logo.router, prefix="/api/ai")


@app.get("/health")
def health():
    return {"status": "ok", "service": "brandai-ai"}

