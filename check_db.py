import os
from pymongo import MongoClient
import logging

# --- Configuration ---
MONGO_URI = os.environ.get("MONGO_URI")
if MONGO_URI:
    MONGO_URI = MONGO_URI.strip('\'"') # Strip both single and double quotes
# MONGO_URI = "mongodb+srv://radiogod:8rH7gF9pp5H9o0me@radioquestcluster.bows3jq.mongodb.net/?retryWrites=true&w=majority&appName=RadioQuestCluster"

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_db_contents():
    """Connects to MongoDB and checks the contents of the story_segments collection."""
    if not MONGO_URI:
        logging.error("MONGO_URI environment variable is not set. Cannot check database.")
        return

    try:
        logging.info("Connecting to MongoDB to verify seeding...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        db = client.get_database("RadioQuest")
        collection = db.story_segments
        logging.info("Connection successful.")

        segment_count = collection.count_documents({})
        logging.info(f"Found {segment_count} documents in the 'story_segments' collection.")

        if segment_count > 0:
            logging.info("Listing titles of existing segments:")
            for segment in collection.find({}, {"title": 1, "_id": 1}):
                logging.info(f"  - ID: {segment['_id']}, Title: {segment['title']}")
        else:
            logging.warning("The 'story_segments' collection is empty!")

    except Exception as e:
        logging.error(f"An error occurred while checking the database: {e}")

if __name__ == "__main__":
    check_db_contents() 