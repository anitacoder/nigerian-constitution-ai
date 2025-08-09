import os
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DIR = os.path.abspath("chroma_db")
vectorstore = None
app = FastAPI()

class QuestionRequest(BaseModel):
    question: str
    
@app.on_event("startup")
def load_vectorstore():
    global vectorstore
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )
    except Exception as e:
        vectorstore = None

@app.post("/ask_question")
def ask_question(request: QuestionRequest):
    try:
        docs_with_scores = vectorstore.similarity_search_with_score(request.question, k=6)
        results = []
        for doc, _ in docs_with_scores:
            content = doc.page_content.split('\n')[-1].strip()
            content = re.sub(r'^\d+\.\s*', '', content)
            results.append({"content": content})
        return {
            "question": request.question,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))