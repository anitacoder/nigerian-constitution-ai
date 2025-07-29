import hashlib
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
import time
from typing import List, Dict, Optional, Tuple
from langchain_community.document_loaders.git import GitLoader
from langchain_core.documents import Document
from .mongodb_setup import ConstitutionDb 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv() # Load .env variables

MONGO_URL = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("DATA_COLLECTION_NAME", "documents")
GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") # Make sure this is set if you need it for private repos or higher rate limits
GITHUB_REPO_URL: str = "https://github.com/mykeels/nigerian-constitution"

logger.info(f"Environment variables loaded:")
logger.info(f"MONGO_URI: {MONGO_URL}")
logger.info(f"MONGO_DB_NAME: {MONGO_DB_NAME}")
logger.info(f"DATA_COLLECTION_NAME: {MONGO_COLLECTION_NAME}")

def parse_github_repo_url(url: str) -> Optional[Tuple[str, str]]:
    """Extracts owner and repo name from a GitHub URL."""
    try:
        if not url:
            return None
        # Remove query parameters and fragments
        clean_url = url.split('?')[0].split('#')[0]
        # Remove trailing .git if present
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]

        path_segments = [segment for segment in clean_url.strip('/').split('/') if segment]

        if "github.com" in path_segments:
            github_index = path_segments.index("github.com")
            if len(path_segments) > github_index + 2:
                owner = path_segments[github_index + 1]
                repo_name = path_segments[github_index + 2]
                return owner, repo_name
        logger.warning(f"Could not parse GitHub repo URL: {url}")
        return None
    except Exception as e:
        logger.error(f"Error parsing GitHub repo URL {url}: {e}")
        return None

# The list of repos can be dynamically created or fixed.
# For now, we'll keep it using the single GITHUB_REPO_URL env variable.
# This variable is now solely used to determine if we should even attempt to parse it.
# The actual parsing happens inside get_github_repo_data.


class ConstitutionDataCollector:
    def __init__(self):
        if not MONGO_URL:
            raise ValueError("MONGO_URI environment variable is not set")
        if not MONGO_DB_NAME:
            raise ValueError("MONGO_DB_NAME environment variable is not set")

        # ConstitutionDb handles its own connection and retries.
        self.db_manager = ConstitutionDb(MONGO_URL, MONGO_DB_NAME)
        
        # Now, get the collection. This will implicitly use the connection established by db_manager.
        # get_collection also has a reconnect logic, which is good.
        self.collection = self.db_manager.get_collection(MONGO_COLLECTION_NAME)

        if self.collection is None:
            raise RuntimeError("Failed to obtain MongoDB collection. Check MongoDB connection.")

        logger.info("Constitution data collection initialized successfully.")

    def store_documents(self, data: Dict) -> bool:
        unique_identifier = data.get('url')
        if not unique_identifier:
            logger.error("Attempted to store document without a URL unique identifier.")
            return False

        data['doc_id'] = hashlib.md5(unique_identifier.encode('utf-8')).hexdigest()

        try:
            # Check if collection is still valid, in case it disconnected somehow
            if self.collection is None:
                logger.error("MongoDB collection is not available for storing documents.")
                return False

            result = self.collection.update_one(
                {"url": unique_identifier},
                {"$set": data},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Document with url: {unique_identifier} stored successfully (new).")
                return True
            elif result.modified_count > 0:
                logger.info(f"Document with url: {unique_identifier} updated successfully.")
                return True
            else:
                logger.debug(f"Document with url: {unique_identifier} already exists with same content.")
                return True
        except Exception as e:
            logger.error(f"Error storing document with url: {unique_identifier}. Error: {e}")
            return False

    def get_github_repo_data(self, repo_url: str, branch: str = "master"):
        if not repo_url:
            logger.info("GitHub repository URL is not provided.")
            return

        parsed_info = parse_github_repo_url(repo_url)
        if not parsed_info:
            logger.error(f"Failed to parse repository URL: {repo_url}. Skipping data collection for this repo.")
            return

        owner, repo_name = parsed_info
        repo_full_git_url = f"https://github.com/{owner}/{repo_name}.git"

        try:
            temp_repo_path = f"/tmp/{owner}_{repo_name}_clone" # Use a more unique temp path

            logger.info(f"Starting GitHub repository scraping from: {repo_full_git_url}")

            # Prepare auth if GITHUB_PERSONAL_ACCESS_TOKEN is set
            if GITHUB_PERSONAL_ACCESS_TOKEN:
                clone_url_with_auth = f"https://oauth2:{GITHUB_PERSONAL_ACCESS_TOKEN}@github.com/{owner}/{repo_name}.git"
                loader = GitLoader(
                    repo_path=temp_repo_path,
                    clone_url=clone_url_with_auth,
                    branch=branch,
                    file_filter=lambda file_path: file_path.endswith(('.md', '.txt', '.pdf'))
                )
            else:
                loader = GitLoader(
                    repo_path=temp_repo_path,
                    clone_url=repo_full_git_url,
                    branch=branch,
                    file_filter=lambda file_path: file_path.endswith(('.md', '.txt', '.pdf'))
                )

            langchain_docs: List[Document] = loader.load()
            repo_processed_count = 0

            if not langchain_docs:
                logger.info(f"No documents found in repository: {repo_full_git_url}")
                return

            for doc in langchain_docs:
                # Sanitize metadata for MongoDB storage if necessary (e.g., replace dots in keys)
                metadata = doc.metadata.copy()
                # Example: metadata.pop('some_unwanted_key', None)

                document_data = {
                    "url": doc.metadata.get("source", f"{repo_full_git_url}/{doc.metadata.get('file_path','unknown')}"),
                    "content": doc.page_content,
                    "scraped_at": datetime.utcnow(),
                    "source_type": "github",
                    "metadata": {
                        "repo_url": repo_full_git_url,
                        "file_path": metadata.get("file_path"),
                        "file_type": metadata.get("file_type"),
                        "branch": branch,
                        "title": metadata.get("title", os.path.basename(metadata.get("file_path", "unknown"))),
                        # Add more metadata as needed, e.g., 'commit_hash', 'author', 'last_modified'
                        "commit_hash": metadata.get("commit"),
                        "last_modified": metadata.get("last_modified_at"),
                        "author": metadata.get("author")
                    }
                }
                if self.store_documents(document_data):
                    repo_processed_count += 1

            logger.info(f"Processed {repo_processed_count} documents from repository: {repo_full_git_url}")

        except Exception as e:
            logger.error(f"Error processing repository: {repo_full_git_url}. Error: {e}")
        finally:
            # Clean up the temporary cloned repository regardless of success or failure
            import shutil
            if os.path.exists(temp_repo_path):
                try:
                    shutil.rmtree(temp_repo_path)
                    logger.info(f"Cleaned up temporary repository: {temp_repo_path}")
                except OSError as e:
                    logger.error(f"Error removing temporary directory {temp_repo_path}: {e}")

        time.sleep(2) # Small delay for good measure

    def __del__(self):
        # This might not always be called reliably, especially on container exit.
        # It's better to manage connection closing explicitly where possible.
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close_connection()