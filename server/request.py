from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_interaction import query_text
from document_retrival import load_vectorstore, retrieve_context
import traceback

app = FastAPI()
vectorstore = None

class QuestionRequest(BaseModel):
    question: str

@app.on_event("startup")
def startup_event():
    global vectorstore
    vectorstore = load_vectorstore()

@app.post("/ask_question")
def ask_question(request: QuestionRequest):
    if not vectorstore:
        raise HTTPException(status_code=500, detail="Vectorstore not available")
    try:
        context = retrieve_context(vectorstore, request.question)
        answer = query_text(request.question, context)
        return {
            "question": request.question,
            "results": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))