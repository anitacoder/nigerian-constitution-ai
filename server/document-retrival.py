import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

FOLDER_DIR = os.path.abspath("server/data/constitution/")
CHUNK_SIZE = 100
CHUNK_OVERLAP = 50

def load_files_text():
    all_texts = []
    for root, _, files in os.walk(FOLDER_DIR):
        for file in files:
            if file.endswith((".md")):
                file_path = os.path.join(root, file)
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
                for doc in docs:
                    all_texts.append(doc)
    return all_texts

def chunk():
    documents = load_files_text()
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = text_splitter.split_documents(documents)
    return chunks