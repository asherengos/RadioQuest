import os
import logging
import sys
import traceback
from bson.objectid import ObjectId
from flask import Flask, render_template, abort, request, jsonify
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from google.cloud import texttospeech

# --- App Initialization ---
app = Flask(__name__)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,  # Log to console for Cloud Run
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Database Connection ---
db = None
MONGO_URI = os.environ.get("MONGO_URI")

def init_db():
    global db
    if not MONGO_URI:
        logger.critical("MONGO_URI environment variable is not set.")
        return

    try:
        logger.info("Attempting to connect to MongoDB...")
        # Increased timeout for serverless environments
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        # The ismaster command is cheap and does not require auth.
        mongo_client.admin.command('ismaster')
        db = mongo_client.get_database("RadioQuest")
        logger.info("Successfully connected to MongoDB.")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db = None

# --- AI Model Loading ---
MODEL_PATH = './models/all-MiniLM-L6-v2'
model = None
try:
    if os.path.exists(MODEL_PATH):
        logger.info(f"Loading sentence-transformer model from {MODEL_PATH}...")
        model = SentenceTransformer(MODEL_PATH)
        logger.info("Sentence-transformer model loaded successfully.")
    else:
        logger.warning(f"Local model path not found: {MODEL_PATH}. Search will not work.")
except Exception as e:
    logger.error(f"Failed to load sentence-transformer model: {e}")
    logger.error(traceback.format_exc())

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/healthz')
def healthz():
    return "ok", 200

@app.route('/story/<story_id>')
def story(story_id):
    if db is None:
        logger.error("Database connection is not available for the story route.")
        return "Database connection is not available.", 500
    try:
        story_segment = db.story_segments.find_one({"_id": story_id})
        if story_segment:
            return render_template('story.html', segment=story_segment)
        else:
            abort(404)
    except Exception as e:
        logger.error(f"Error fetching story segment {story_id}: {e}")
        logger.error(traceback.format_exc())
        abort(500)

@app.route('/search')
def search():
    if db is None or model is None:
        return "Search is unavailable.", 503

    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    query_embedding = model.encode(query).tolist()

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "story_embedding",
                "queryVector": query_embedding,
                "numCandidates": 10,
                "limit": 5
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "text": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    results = list(db.story_segments.aggregate(pipeline))
    return jsonify(results)

# --- Main Execution ---
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask app on host 0.0.0.0 and port {port}")
    # Use Gunicorn for production on Cloud Run, but this is a fallback for local dev
    app.run(host='0.0.0.0', port=port, debug=False) 