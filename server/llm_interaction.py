import os
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def query_text(question: str, context: str) -> str:
    llm = OllamaLLM(model="llama3.2:1b", base_url=OLLAMA_URL)

    prompt_response = """I am an intelligent expert on the Nigerian Constitution.
    Context:
    {context}
    Question:
    {question}
    Answer:"""

    prompt = PromptTemplate(template=prompt_response, input_variables=["context", "question"])
    chain = prompt | llm

    result = chain.invoke({"context": context, "question": question})
    return str(result)
