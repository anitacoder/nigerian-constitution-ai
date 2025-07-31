import os
import re
from typing import List, Dict
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

class ConstitutionPreprocessor:
    def __init__(self):
        self.data_dir = "./data"
        self.faiss_index_path = os.path.join(self.data_dir, "faiss_index_constitution")
        os.makedirs(self.faiss_index_path, exist_ok=True)

        self.mongo_uri = os.getenv("MONGO_URI")
        self.mongo_db_name = os.getenv("MONGO_DB_NAME")
        self.mongo_collection_name = os.getenv("DATA_COLLECTION_NAME")
        
        self.mongo_client = None

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
            length_function=len,
        )

        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        print("Embedding model loaded.")

    def get_mongo_collection(self):
        if self.mongo_client is None:
            try:
                self.mongo_client = MongoClient(self.mongo_uri)
                self.mongo_client.admin.command('ping')
                db = self.mongo_client[self.mongo_db_name]
                collection = db[self.mongo_collection_name]
                print(f"Connected to MongoDB: {self.mongo_db_name}.{self.mongo_collection_name}")
                return collection
            except ConnectionFailure as e:
                print(f"MongoDB connection failed: {e}")
                return None
        return self.mongo_client[self.mongo_db_name][self.mongo_collection_name]

    def load_documents(self) -> List[Dict]:
        collection = self.get_mongo_collection()
        if collection is None:
            return []
        try:
            docs = list(collection.find({}))
            print(f"Loaded {len(docs)} raw documents.")
            return docs
        except Exception as e:
            print(f"Error loading documents: {e}")
            return []

    def clean_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
                   .replace('&quot;', '"').replace('&#x27;', "'").replace('&apos;', "'")
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'[\!\?]{2,}', '!', text)
        text = re.sub(r'[\,\;\-]{2,}', ',', text)
        text = re.sub(r'[^a-zA-Z0-9\s.,!?;:"\'\-\(\)\[\]]', '', text)
        return text.strip()

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        chunks = []
        for doc in documents:
            doc_id = doc.get("_id", doc.get("url", "unknown_id"))
            raw_content = doc.get("content", "")
            if not raw_content:
                continue
            cleaned = self.clean_text(raw_content)
            text_chunks = self.text_splitter.split_text(cleaned)

            for i, chunk in enumerate(text_chunks):
                metadata = {
                    "source": doc.get("url", "unknown"),
                    "doc_id": str(doc_id),
                    "chunk_index": i,
                    "title": doc.get("metadata", {}).get("title", "Nigerian Constitution")
                }

                chunks.append({
                    "doc_id": str(doc_id),
                    "chunk_id": f"{doc_id}_{i}",
                    "content": chunk,
                    "metadata": metadata
                })
        print(f"Total chunks created: {len(chunks)}")
        return chunks

    def filter_quality_chunks(self, chunks: List[Dict]) -> List[Dict]:
        filtered = []
        for chunk in chunks:
            content = chunk.get("content", "")
            if len(content) < 100:
                continue
            alphanum_ratio = len(re.findall(r'[a-zA-Z0-9]', content)) / len(content)
            digit_ratio = len(re.findall(r'\d', content)) / len(content)
            if alphanum_ratio < 0.5 or digit_ratio > 0.4:
                continue
            filtered.append(chunk)
        print(f"Quality chunks retained: {len(filtered)} / {len(chunks)}")
        return filtered

    def save_to_faiss(self, chunks: List[Dict]):
        if not chunks:
            print("No chunks to save to FAISS.")
            return
        documents = [Document(page_content=c["content"], metadata=c["metadata"]) for c in chunks]
        vectorstore = FAISS.from_documents(documents, self.embedding_model)
        vectorstore.save_local(self.faiss_index_path)
        print(f"FAISS index saved to: {self.faiss_index_path}")

    def run(self):
        print("Starting Constitution Data Preprocessing...")
        raw_docs = self.load_documents()
        chunks = self.chunk_documents(raw_docs)
        filtered_chunks = self.filter_quality_chunks(chunks)
        self.save_to_faiss(filtered_chunks)
        print("Data preprocessing pipeline completed.")


if __name__ == "__main__":
    preprocessor = ConstitutionPreprocessor()
    preprocessor.run()

    if os.path.exists(preprocessor.faiss_index_path):
        print(f"\nFAISS index directory created at: {preprocessor.faiss_index_path}")
    else:
        print("\nFAISS index not found.")