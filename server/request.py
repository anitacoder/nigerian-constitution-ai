import os
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

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

def retrieve_context(query: str, k: int = 6) -> str:
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
    results = []

    for doc, _ in docs_with_scores:
        content = doc.page_content.split('\n')[-1].strip()
        content = re.sub(r'^\d+\.\s*', '', content)
        results.append(content)
    return results

def query_text(question: str, context: str) -> str:
    llm = Ollama(model="llama3.2:1b")
    prompt_response = """ I am an intelligent expert on nigeria constitution. 
    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    prompt = PromptTemplate(template=prompt_response, input_variables=["context","question"])
    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"context":context, "question": question})

@app.post("/ask_question")
def ask_question(request: QuestionRequest):
    try:
      context = retrieve_context(request.question)
      answer = query_text(request.question, context)
      return {
            "question": request.question,
            "results": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 