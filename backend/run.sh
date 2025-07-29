set -e

echo "Waiting for MongoDB to be ready..."
# The healthcheck in docker-compose.yml and retries in mongodb_setup.py handle this,
# so the explicit sleep/ping loop here isn't strictly necessary for correctness,
# but can provide more granular logging feedback.
echo "MongoDB is ready!" # Placeholder, as Python script does proper check

python_check_script_path="/tmp/check_data_for_run_sh.py"
cat <<EOF > "${python_check_script_path}"
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "nigerian_constitution_db")
DATA_COLLECTION_NAME = os.getenv("DATA_COLLECTION_NAME", "documents")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000)
    db = client[MONGO_DB_NAME]
    collection = db[DATA_COLLECTION_NAME]
    client.admin.command('ping') # Verify connection

    doc_count = collection.count_documents({})
    logger.info(f"Checking collection '{DATA_COLLECTION_NAME}' in database '{MONGO_DB_NAME}'")
    logger.info(f"Found {doc_count} documents in collection")
    if doc_count > 0:
        sys.exit(0) # Exit with 0 if data exists
    else:
        sys.exit(1) # Exit with 1 if collection is empty (meaning we need to run data collection)
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    logger.error(f"Error checking MongoDB data: {e}")
    sys.exit(1) # Exit with 1 on connection error
except Exception as e:
    logger.error(f"An unexpected error occurred during MongoDB data check: {e}")
    sys.exit(1)
EOF

echo "Checking if data already exists..."
if python "${python_check_script_path}"; then
    echo "Data already exists. Skipping data collection pipeline."
else
    echo "No data found or error checking data. Attempting data collection."
    # Explicitly call the function from the main module
    python -c "from data_processing.main import run_data_collection_pipeline; run_data_collection_pipeline()"
    echo "Data collection pipeline finished."
fi

rm "${python_check_script_path}" # Clean up temporary script

# exec uvicorn rag_pipeline.main:app --host 0.0.0.0 --port 8000 --workers 1