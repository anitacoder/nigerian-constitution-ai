import os
import re
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

FOLDER_DIR = os.path.abspath("server/data/constitution/")
CHUNK_SIZE = 100
CHUNK_OVERLAP = 50
CHROMA_DIR = os.path.abspath("chroma_db")
EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_files_text():
    all_texts = []
    for root, _, files in os.walk(FOLDER_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
                if docs:
                    all_texts.extend(docs)
    return all_texts

def chunk():
    documents = load_files_text()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

def store_data_in_chromadb():
    chunk_data = chunk()
    embeddings = EMBEDDINGS
    embeddings = EMBEDDINGS,
    vectorstore = Chroma.from_documents(
        documents=chunk_data,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    vectorstore.persist()
    return vectorstore 

def load_vectorstore():
    try:
        return Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=EMBEDDINGS
        )
    except Exception as e:
       return None

def retrieve_context(vectorstore, query: str, k: int = 6) -> str:
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
    results = []
    for doc, _ in docs_with_scores:
        content = doc.page_content.split('\n')[-1].strip()
        content = re.sub(r'^\d+\.\s*', '', content)
        results.append(content)
    return "\n".join(results) 
    return results

if __name__ == "__main__":
    store_data_in_chromadb()
