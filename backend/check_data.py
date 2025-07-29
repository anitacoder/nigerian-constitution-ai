import os
import pymongo
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_data(collection):
    try:
        mongo_uri = os.getenv("MONGO_URI")
        mongo_db_name = os.getenv("MONGO_DB_NAME")

        client = pymongo.MongoClient(mongo_uri)
        db = client[mongo_db_name]
        collection = db[COLLECTION_NAME]
        count = collection.count_documents({})
        client.close()
        return count
    except Exception as e:
        logger.error(f"Error checking MongoDB data: {e}")
        return 0


if __name__ == "__main__":
    COLLECTION_NAME = "documents"
    doc_count = check_data(COLLECTION_NAME)
if doc_count == 0:
    logger.info(f"Collection '{COLLECTION_NAME}' is empty.")
    exit(1)
else:
    logger.info(f"Collection '{COLLECTION_NAME}' contains {doc_count} documents. Skipping data collection.")
    exit(0) 
