from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import time
from datetime import datetime
import json
import logging
import asyncio 

from .llm_interaction import NigerianConstitutionRAG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

allowed_cors_origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://frontend:3000"
]

app = FastAPI(
    title="Nigerian Constitution AI API",
    description="AI-powered assistant for Nigerian constitution questions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question to ask the AI assistant.")

rag_system: Optional[NigerianConstitutionRAG] = None

@app.on_event("startup")
async def startup_event():
    global rag_system
    logger.info("Initializing RAG system on startup...")
    try:
        rag_system = NigerianConstitutionRAG()
        logger.info("RAG system initialized successfully.")
    except FileNotFoundError:
        logger.error("FAISS index not found")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}", exc_info=True)

@app.post("/ask")
async def ask_question_stream(request: QuestionRequest):
    if rag_system is None:
        raise HTTPException(status_code=503, detail="Service Unavailable: RAG system not initialized.")

    question = request.question

    async def generate_chunks():
        try:
            start_time = time.time()

            logger.info(f"Streaming answer for question: '{question[:50]}...'")

            for chunk in rag_system.stream_answer(question):
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.02) 
            logger.info(f"Streaming completed in {time.time() - start_time:.2f} seconds.")

        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            error_chunk = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_chunks(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
             "Transfer-Encoding": "chunked"
        }
    )
