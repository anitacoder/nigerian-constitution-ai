from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import time
from datetime import datetime
import json
import logging

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
    title="Nigerian Laws AI API",
    description="AI-powered assistant for Nigerian laws questions",
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
    top_k = 5

    async def generate_chunks():
        try:
            start_time = time.time()
            relevant_info = rag_system.get_retriever().get_relevant_documents(question)
            context_parts = []
            context_length = 0

            for doc in relevant_info:
                doc_title = doc.metadata.get("title", "Nigerian Constitution")
                chunk_content = doc.page_content
                source_citation_text = f"Source: {doc_title}"
                chunk_text = f"{source_citation_text}\nContent: {chunk_content}\n\n"
                context_parts.append(chunk_text)
                context_length += len(chunk_text)

            context = "".join(context_parts)

            if not context:
                logger.warning("No relevant context found or context was empty after processing.")
                no_context_message = {
                    "type": "info",
                    "content": "No highly relevant information found in the knowledge base for this question. "
                               "Attempting to generate an answer with limited context."
                }
                yield f"data: {json.dumps(no_context_message)}\n\n"

            logger.info(f"Generating answer using model for: '{question[:50]}...'")
            prompt = rag_system.llm.invoke(
                rag_system.generate_answer(question)
            ) 

            initial_metadata = {
                "type": "metadata",
                "relevant_chunks_found": len(relevant_info),
                "context_chunks_used": len(context_parts),
                "model": "NigerianConstitutionRAG"
            }
            yield f"data: {json.dumps(initial_metadata)}\n\n"

            chunk_data = {"type": "chunk", "content": prompt}
            yield f"data: {json.dumps(chunk_data)}\n\n"

            final_message = {
                "type": "end",
                "full_answer": prompt,
                "timestamp": datetime.now().isoformat(),
                "generation_time": f"{time.time() - start_time:.2f} seconds"
            }
            yield f"data: {json.dumps(final_message)}\n\n"

        except Exception as e:
            logger.error(f"Error during streaming response generation for question '{question[:50]}...': {e}", exc_info=True)
            error_message = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_message)}\n\n"

    return StreamingResponse(
        generate_chunks(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )