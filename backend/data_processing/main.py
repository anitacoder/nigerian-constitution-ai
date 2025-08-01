import logging
from .data_collector import ConstitutionDataCollector, GITHUB_REPO_URL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_data_collection_pipeline():
    logger.info("Starting Nigerian Constitution Data Collection Pipeline")
    
    try:
        data_collector = ConstitutionDataCollector()
        
        if GITHUB_REPO_URL:
            logger.info(f"Starting GitHub repository scraping from: {GITHUB_REPO_URL}")
            data_collector.get_github_repo_data(GITHUB_REPO_URL, branch="master")
        else:
            logger.warning("No target GitHub repository URL defined.")
            
        logger.info("Nigerian Constitution Data Collection Pipeline completed successfully.")
        
    except Exception as e:
        logger.critical(f"An unhandled error occurred during data collection pipeline execution: {e}")
        raise 

if __name__ == "__main__":
    run_data_collection_pipeline()