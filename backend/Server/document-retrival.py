import os
from langchain.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings 
from langchain.vectorstores import FAISS

FOLDER_DIR = "/Users/anitankwocha/Documents/Workspace/Nigerian_Constitution_ai/nigerian-constitution"
STORE_DIR = "datas/faiss_index"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MODEL_NAME = "all-MiniLM-L6-v2"

os.makedirs(STORE_DIR, exist_ok=True)


def load_files(folder_path):
    all_texts = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith((".md")):
                file_path = os.path.join(root, file)
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
                for doc in docs:
                    doc.metadata["source"] = file_path
                    all_texts.append(doc)
    return all_texts

print("Loading Files....")
documents = load_files(FOLDER_DIR)

text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)
chunks = text_splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

vectorStore = FAISS.from_documents(chunks, embeddings)
vectorStore.save_local(STORE_DIR)


print("Data has been stored successfull as FAISS index at:", STORE_DIR)