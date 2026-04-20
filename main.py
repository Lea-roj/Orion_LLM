from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine
from backend.db.models import Base
from backend.translate.ollama_service import call_ollama
from backend.api.routes import router
import threading

app = FastAPI()

def warmup():
    try:
        print("Warming up Ollama...")
        call_ollama("Extract entities from: John lives in Germany")
        print("Ollama ready")
    except Exception as e:
        print("Warmup failed:", e)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    threading.Thread(target=warmup, daemon=True).start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
