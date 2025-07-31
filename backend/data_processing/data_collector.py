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

load_dotenv()


MONGO_URL = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("DATA_COLLECTION_NAME", "documents")
GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
GITHUB_REPO_URL: str = "https://github.com/mykeels/nigerian-constitution"

logger.info(f"Environment variables loaded:")
logger.info(f"MONGO_URI: {MONGO_URL}")
logger.info(f"MONGO_DB_NAME: {MONGO_DB_NAME}")
logger.info(f"DATA_COLLECTION_NAME: {MONGO_COLLECTION_NAME}")

def parse_github_repo_url(url: str) -> Optional[Tuple[str, str]]:
    try:
        if not url:
            return None
        clean_url = url.split('?')[0].split('#')[0]
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

class ConstitutionDataCollector:
    def __init__(self):
        if not MONGO_URL:
            raise ValueError("MONGO_URI environment variable is not set")
        if not MONGO_DB_NAME:
            raise ValueError("MONGO_DB_NAME environment variable is not set")

        self.db_manager = ConstitutionDb(MONGO_URL, MONGO_DB_NAME)
        
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

        parsed_url_parts = parse_github_repo_url(repo_url)
        if not parsed_url_parts:
            logger.error(f"Failed to parse GitHub repository URL: {repo_url}")
            return
        owner, repo_name = parsed_url_parts 

        try:
            temp_repo_path = f"/tmp/{owner}_{repo_name}_clone"

            logger.info(f"Starting GitHub repository scraping from: {repo_url}")
            clone_target_url = repo_url 

            if GITHUB_PERSONAL_ACCESS_TOKEN:
                clone_target_url = f"https://oauth2:{GITHUB_PERSONAL_ACCESS_TOKEN}@github.com/{owner}/{repo_name}.git"
                if not clone_target_url.endswith('.git'):
                    clone_target_url += '.git'
                logger.info("Using GitHub Personal Access Token for cloning.")
            else:
                logger.info("No GitHub Personal Access Token provided, cloning publically.")


            loader = GitLoader(
                repo_path=temp_repo_path,
                clone_url=clone_target_url,
                branch=branch,
                file_filter=lambda file_path: file_path.endswith(('.md', '.txt', '.pdf'))
            )

            langchain_docs: List[Document] = loader.load()
            repo_processed_count = 0

            if not langchain_docs:
                logger.info(f"No documents found in repository: {repo_url}")
                return

            for doc in langchain_docs:
                metadata = doc.metadata.copy()

                document_data = {
                    "url": doc.metadata.get("source", f"{repo_url}/{doc.metadata.get('file_path','unknown')}"),
                    "content": doc.page_content,
                    "scraped_at": datetime.utcnow(),
                    "source_type": "github",
                    "metadata": {
                        "repo_url": repo_url,
                        "file_path": metadata.get("file_path"),
                        "file_type": metadata.get("file_type"),
                        "branch": branch,
                        "title": metadata.get("title", os.path.basename(metadata.get("file_path", "unknown"))),
                        "commit_hash": metadata.get("commit"),
                        "last_modified": metadata.get("last_modified_at"),
                        "author": metadata.get("author")
                    }
                }

                document_data['document_id'] = hashlib.md5(document_data['url'].encode('utf-8')).hexdigest()
                if self.store_documents(document_data):
                    repo_processed_count += 1

            logger.info(f"Processed {repo_processed_count} documents from repository: {repo_url}")

        except Exception as e:
            logger.error(f"Error processing repository: {repo_url}. Error: {e}")
        finally:
            import shutil
            if os.path.exists(temp_repo_path):
                try:
                    shutil.rmtree(temp_repo_path)
                    logger.info(f"Cleaned up temporary repository: {temp_repo_path}")
                except OSError as e:
                    logger.error(f"Error removing temporary directory {temp_repo_path}: {e}")

        time.sleep(2)
    def __del__(self):
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close_connection()