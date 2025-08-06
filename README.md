# Nigerian Constitution AI Assistant

This is an AI-powered assistant that helps users understand the Nigerian Constitution through a Retrieval-Augmented Generation (RAG) pipeline

## Features

- Ask questions about the Nigerian Constitution.
- Get answers backed by relevant sections.
- Built with a RAG pipeline (Retrieval-Augmented Generation).
- Dockerized backend for easy setup.
- Modern frontend with Next.js.


## Tech Stack

- **Frontend:** Next.js, TypeScript
- **Backend:** Python, FastAPI, LangChain
- **Database:** MongoDB
- **Vector Store:** FAISS
- **Containerization:** Docker, Docker Compose

## Getting Started

Follow these steps to set up and run the application locally using Docker Compose.

### Prerequisites

Make sure you have the following installed:

- [Node.js](https://nodejs.org/) (v16 or higher)
- [Docker](https://www.docker.com/)

### 1. Environment Configuration

This project relies on several environment variables for its services (MongoDB, Ollama, Backend API, etc.). These variables are sensitive and not committed to the repository.

**Steps:**

1.  Navigate to the root directory of this repository:
    ```
    cd nigerian-constitution-ai
    ```
2.  **Create your `.env` in the root directory

3.  Open the newly created `.env` file in your text editor, and put the following:
    ```
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB_NAME=nigerian_constitution_db
   DATA_COLLECTION_NAME=documents
    
   GITHUB_PERSONAL_ACCESS_TOKEN=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
    
   ME_CONFIG_MONGODB_SERVER=mongodb
   ME_CONFIG_MONGODB_PORT=27017
   ME_CONFIG_BASICAUTH_USERNAME=admin
   ME_CONFIG_BASICAUTH_PASSWORD=pass
   ME_CONFIG_MONGODB_URL=mongodb://localhost:27017
    
   FAISS_INDEX_PATH=data-storage/faiss_index_constitution.bin
    
   OLLAMA_BASE_URL_LOCAL=http://localhost:11434
   OLLAMA_BASE_URL_DOCKER=http://host.docker.internal:11434
   OLLAMA_MODEL_NAME=llama3.2:1b
    
   NEXT_PUBLIC_API_URL=http://backend:8000
   NEXT_PUBLIC_PYTHON_BACKEND_URL=http://localhost:8000
   ```

### 2. Running the Application

Once your `.env` file is configured:

1.  Make sure you are in the directory of the `run.sh` file, which is the (nigerian-constitution-ai)
2.  Execute the `run.sh` script to start all services:
    ```
    ./run.sh
    ```
