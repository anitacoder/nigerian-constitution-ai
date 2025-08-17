from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

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
