import os
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def query_text(question: str, context: str):
    llm = OllamaLLM(model="llama3.2:1b", base_url=OLLAMA_URL)

    prompt_response = "I am an intelligent expert on the Nigerian Constitution."

    if question.strip().lower() in ["who are you?", "what are you?"]:
        yield prompt_response
        return 
    
    full_prompt = """I am an intelligent expert on the Nigerian Constitution.
    Context:
    {context}
    Question:
    {question}
    Answer:"""

    prompt = PromptTemplate(template=full_prompt, input_variables=["context", "question"])
    chain = prompt | llm

    for chunk in chain.stream({"context": context, "question": question}):
        yield chunk
