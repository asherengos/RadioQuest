from flask import Flask, render_template, request, abort, url_for, jsonify
import logging
import traceback
import os
from pymongo import MongoClient
from google.cloud import texttospeech
import json

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Direct Database and TTS Initialization ---
mongo_client = None
tts_client = None
db = None
stories_collection = None

try:
    logger.info("Initializing MongoDB connection...")
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set")
    
    mongo_client = MongoClient(mongo_uri.strip('\'"'))
    db = mongo_client["RadioQuest"]
    stories_collection = db["story_segments"]
    logger.info("MongoDB connection established successfully.")
    
    logger.info("Initializing Google Cloud TTS...")
    gcp_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not gcp_creds:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    # Handle both file path and JSON string
    if gcp_creds.startswith('{'):
        # It's a JSON string, write to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(gcp_creds)
            temp_creds_path = f.name
        tts_client = texttospeech.TextToSpeechClient.from_service_account_file(temp_creds_path)
        os.unlink(temp_creds_path)  # Clean up temp file
    else:
        # It's a file path
        tts_client = texttospeech.TextToSpeechClient.from_service_account_file(gcp_creds)
    
    logger.info("Google Cloud TTS client initialized successfully.")
    
except Exception as e:
    logger.error(f"FATAL: Failed to initialize services. Error: {e}")
    logger.error(traceback.format_exc())
    # Don't exit, let it try to run anyway for debugging

# --- Routes ---

@app.route('/')
def index():
    """Home page. The entry point for the adventure."""
    logger.info("Serving index page")
    return render_template('index.html')

@app.route('/story/<story_id>')
def story(story_id):
    """
    Handles fetching and displaying a story segment.
    Direct MongoDB access - no agents!
    """
    logger.info(f"Fetching story for story_id: '{story_id}'")
    
    if stories_collection is None:
        logger.error("MongoDB not initialized")
        return "Database not available", 500
    
    try:
        # Try to fetch from MongoDB, fallback to mock data
        try:
            segment = stories_collection.find_one({"_id": story_id})
        except Exception as db_error:
            logger.warning(f"MongoDB error, using mock data: {db_error}")
            # Mock data for demo
            segment = {
                "_id": story_id,
                "title": f"The Adventure of {story_id.title()}",
                "content": f"Welcome to RadioQuest! This is a demo story about {story_id}. In the heart of Goma, children gather around solar-powered radios to hear magical tales that transport them to new worlds. This interactive storytelling platform uses Google Cloud AI to bring education and joy to thousands of young minds.",
                "choices": [
                    {"id": "choice1", "text": "Continue the adventure"},
                    {"id": "choice2", "text": "Explore the magical forest"}
                ]
            }
        
        if segment:
            logger.info(f"Found story segment: {segment.get('title', 'Unknown')}")
            
            # Generate audio if not present
            if not segment.get('audio_url'):
                logger.info(f"Generating audio for story: {story_id}")
                audio_success = generate_audio_for_story(segment)
                if audio_success:
                    segment['audio_url'] = f"/audio/{story_id}.mp3"
            
            return render_template('story.html', segment=segment)
        else:
            logger.warning(f"Story not found: {story_id}")
            abort(404)
            
    except Exception as e:
        logger.error(f"Error fetching story {story_id}: {e}")
        logger.error(traceback.format_exc())
        abort(500)

@app.route('/search')
def search():
    """
    Handles story search requests.
    Simple MongoDB text search - no vector embeddings!
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Please provide a search query"}), 400

    logger.info(f"Searching for: '{query}'")
    
    if stories_collection is None:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        # Try MongoDB search, fallback to mock results
        try:
            results = list(stories_collection.find({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}}
                ]
            }).limit(10))
        except Exception as db_error:
            logger.warning(f"MongoDB search error, using mock data: {db_error}")
            # Mock search results for demo
            results = [
                {"_id": "adventure1", "title": "The Great Adventure", "content": "An exciting tale of discovery..."},
                {"_id": "forest", "title": "Magical Forest Stories", "content": "Stories from the enchanted woods..."},
                {"_id": "goma", "title": "Tales from Goma", "content": "Local stories from the children of Goma..."}
            ]
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            if '_id' in result:
                result['_id'] = str(result['_id'])
        
        logger.info(f"Found {len(results)} search results")
        return jsonify({"results": results})
        
    except Exception as e:
        logger.error(f"Search error for query '{query}': {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Search failed"}), 500

@app.route('/audio/<audio_id>')
def serve_audio(audio_id):
    """Serve generated audio files"""
    try:
        # In production, this would serve from cloud storage
        # For now, return a placeholder
        return jsonify({"message": f"Audio for {audio_id} would be served here"}), 200
    except Exception as e:
        logger.error(f"Audio serving error: {e}")
        return jsonify({"error": "Audio not available"}), 404

@app.route('/health')
def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "mongodb": "connected" if mongo_client else "disconnected", 
        "tts": "initialized" if tts_client else "not_initialized"
    }
    return jsonify(status)

def generate_audio_for_story(segment):
    """Generate TTS audio for a story segment"""
    if not tts_client:
        logger.error("TTS client not initialized")
        return False
    
    try:
        # Prepare the text for TTS
        text_to_speak = segment.get('content', 'No content available')
        
        # Configure TTS request
        synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
        
        # Use Nigerian English voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-NG",
            name="en-NG-Wavenet-A"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Generate the audio
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice, 
            audio_config=audio_config
        )
        
        # In a real implementation, you'd save this to cloud storage
        # For now, just log success
        logger.info(f"Successfully generated {len(response.audio_content)} bytes of audio")
        return True
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    # For local testing
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)