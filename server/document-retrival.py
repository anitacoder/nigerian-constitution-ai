import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

FOLDER_DIR = os.path.abspath("server/data/constitution/")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHROMA_DIR = os.path.abspath("chroma_db")

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
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=chunk_data,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    vectorstore.persist()

if __name__ == "__main__":
    store_data_in_chromadb()
