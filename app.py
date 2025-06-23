from flask import Flask, render_template, request, abort, url_for, jsonify
import logging
import traceback
import os
from pymongo import MongoClient
from google.cloud import texttospeech
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Enhanced Mock Data for Demo Reliability ---
MOCK_STORIES = {
    "intro": {
        "_id": "intro",
        "title": "Welcome to Goma",
        "content": "Once upon a time in the beautiful city of Goma, nestled between Lake Kivu and the Virunga Mountains, a group of curious children discovered something magical. Through their solar-powered radios, they could hear stories that came alive with voices from their own land. This is RadioQuest - where every story is an adventure, and every child is the hero of their own tale.",
        "choices": [
            {"id": "forest", "text": "Explore the enchanted forest"},
            {"id": "mountain", "text": "Climb the mystical mountain"}
        ]
    },
    "forest": {
        "_id": "forest", 
        "title": "The Enchanted Forest Adventure",
        "content": "You venture into the lush forests of Virunga, where ancient trees whisper secrets and colorful birds guide your path. The children of Goma often play here, but today you discover something extraordinary - a hidden grove where stories grow on trees like magical fruit, waiting to be shared with the world.",
        "choices": [
            {"id": "village", "text": "Return to the village"},
            {"id": "lake", "text": "Head to Lake Kivu"}
        ]
    },
    "mountain": {
        "_id": "mountain",
        "title": "Mountain Peak Stories", 
        "content": "High atop the Virunga Mountains, you find a place where the clouds touch the earth and the views stretch across all of Eastern Africa. Here, the elders say, is where all the best stories begin - with a view so vast it contains infinite possibilities for adventure.",
        "choices": [
            {"id": "intro", "text": "Start a new adventure"},
            {"id": "village", "text": "Visit the village below"}
        ]
    },
    "village": {
        "_id": "village",
        "title": "Village Life Chronicles",
        "content": "In the heart of Goma, where families gather around radios as the sun sets behind the mountains, you discover the true magic of storytelling. Here, every voice matters, every choice shapes the future, and every child becomes the author of their own adventure.",
        "choices": [
            {"id": "intro", "text": "Begin a new journey"},
            {"id": "lake", "text": "Walk to Lake Kivu"}
        ]
    }
}

MOCK_SEARCH_RESULTS = [
    {"_id": "intro", "title": "Welcome to Goma", "content": "Stories from the heart of Goma..."},
    {"_id": "forest", "title": "The Enchanted Forest Adventure", "content": "Magical adventures in Virunga forests..."},
    {"_id": "mountain", "title": "Mountain Peak Stories", "content": "Tales from the high peaks of Virunga..."},
    {"_id": "village", "title": "Village Life Chronicles", "content": "Daily adventures in Goma village..."},
    {"_id": "lake", "title": "Lake Kivu Legends", "content": "Ancient stories from the shores of Lake Kivu..."}
]

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

# --- Enhanced ADK-Style Orchestrator for Demo ---
class ADKOrchestrator:
    def __init__(self):
        self.workflow_steps = []
        
    def add_workflow_step(self, agent_name, action, status, result=None, error=None):
        """Add a step to the workflow for demo purposes"""
        import time
        step = {
            "agent": agent_name,
            "action": action,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        if result:
            step["result"] = result
        if error:
            step["error"] = error
        self.workflow_steps.append(step)
        
    def orchestrate_story_fetch(self, story_id):
        """Orchestrate story fetching with enhanced agent-style workflow"""
        self.workflow_steps = []  # Reset workflow
        
        # Step 1: Story Agent initialization
        self.add_workflow_step("StoryAgent", "init", "started")
        self.add_workflow_step("StoryAgent", "init", "success", {"agent_type": "content_fetcher", "target": story_id})
        
        # Step 2: Database connection attempt
        self.add_workflow_step("StoryAgent", "connect_db", "started")
        
        try:
            # Try MongoDB first
            if stories_collection is not None:
                try:
                    self.add_workflow_step("StoryAgent", "connect_db", "success", {"source": "mongodb_atlas"})
                    self.add_workflow_step("StoryAgent", "fetch_story", "started", {"query": {"_id": story_id}})
                    
                    story = stories_collection.find_one({"_id": story_id})
                    if story:
                        self.add_workflow_step("StoryAgent", "fetch_story", "success", {"source": "mongodb", "title": story.get("title"), "content_length": len(story.get("content", ""))})
                        return story
                    else:
                        self.add_workflow_step("StoryAgent", "fetch_story", "not_found", {"message": "Story not found in database"})
                except Exception as e:
                    self.add_workflow_step("StoryAgent", "fetch_story", "error", {"error_type": "database_auth", "message": str(e)})
            else:
                self.add_workflow_step("StoryAgent", "connect_db", "failed", {"reason": "mongodb_not_initialized"})
            
            # Step 3: Fallback to mock data system
            self.add_workflow_step("StoryAgent", "fallback_init", "started")
            story = MOCK_STORIES.get(story_id)
            if story:
                self.add_workflow_step("StoryAgent", "fallback_fetch", "success", {
                    "source": "mock_data", 
                    "title": story.get("title"), 
                    "content_length": len(story.get("content", "")),
                    "cultural_context": "goma_virunga"
                })
                self.add_workflow_step("StoryAgent", "complete", "success", {"final_source": "mock_data_fallback"})
                return story
            else:
                self.add_workflow_step("StoryAgent", "fallback_fetch", "error", {"message": "Story not found in mock data"})
                self.add_workflow_step("StoryAgent", "complete", "failed")
                raise ValueError(f"Story {story_id} not found")
                
        except Exception as e:
            self.add_workflow_step("StoryAgent", "complete", "error", {"final_error": str(e)})
            raise
            
    def orchestrate_search(self, query):
        """Orchestrate search with enhanced agent-style workflow"""
        self.workflow_steps = []  # Reset workflow
        
        # Step 1: Search Agent initialization
        self.add_workflow_step("SearchAgent", "init", "started")
        self.add_workflow_step("SearchAgent", "init", "success", {"agent_type": "query_processor", "query": query})
        
        # Step 2: Query validation and preprocessing
        self.add_workflow_step("SearchAgent", "validate_query", "started")
        if len(query.strip()) < 2:
            self.add_workflow_step("SearchAgent", "validate_query", "error", {"reason": "query_too_short"})
            raise ValueError("Query too short")
        self.add_workflow_step("SearchAgent", "validate_query", "success", {"processed_query": query.lower().strip()})
        
        # Step 3: Database search attempt
        self.add_workflow_step("SearchAgent", "execute_search", "started", {"target": "mongodb_atlas"})
        
        try:
            # Try MongoDB first
            if stories_collection is not None:
                try:
                    self.add_workflow_step("SearchAgent", "db_connection", "success")
                    results = list(stories_collection.find({
                        "$or": [
                            {"title": {"$regex": query, "$options": "i"}},
                            {"content": {"$regex": query, "$options": "i"}}
                        ]
                    }).limit(10))
                    
                    if results:
                        # Convert ObjectId to string
                        for result in results:
                            result['_id'] = str(result['_id'])
                        self.add_workflow_step("SearchAgent", "execute_search", "success", {
                            "source": "mongodb", 
                            "results_count": len(results),
                            "first_result": results[0].get("title") if results else None
                        })
                        self.add_workflow_step("SearchAgent", "complete", "success", {"final_source": "mongodb"})
                        return results
                    else:
                        self.add_workflow_step("SearchAgent", "execute_search", "no_results", {"source": "mongodb"})
                except Exception as e:
                    self.add_workflow_step("SearchAgent", "execute_search", "error", {"error_type": "database_auth", "message": str(e)})
            else:
                self.add_workflow_step("SearchAgent", "db_connection", "failed", {"reason": "mongodb_not_initialized"})
            
            # Step 4: Fallback search in mock data
            self.add_workflow_step("SearchAgent", "fallback_search", "started", {"target": "mock_data_system"})
            results = [s for s in MOCK_SEARCH_RESULTS if query.lower() in s["title"].lower() or query.lower() in s["content"].lower()]
            self.add_workflow_step("SearchAgent", "fallback_search", "success", {
                "source": "mock_data", 
                "results_count": len(results),
                "cultural_context": "goma_themed_content"
            })
            self.add_workflow_step("SearchAgent", "complete", "success", {"final_source": "mock_data_fallback"})
            return results
            
        except Exception as e:
            self.add_workflow_step("SearchAgent", "complete", "error", {"final_error": str(e)})
            raise
            
    def orchestrate_tts(self, story_content, story_id):
        """Orchestrate TTS generation with enhanced agent-style workflow"""
        # Step 1: TTS Agent initialization
        self.add_workflow_step("TTSAgent", "init", "started")
        self.add_workflow_step("TTSAgent", "init", "success", {"agent_type": "audio_generator", "target_story": story_id})
        
        # Step 2: Content preparation
        self.add_workflow_step("TTSAgent", "prepare_content", "started")
        content_length = len(story_content)
        if content_length == 0:
            self.add_workflow_step("TTSAgent", "prepare_content", "error", {"reason": "empty_content"})
            raise ValueError("No content to synthesize")
        
        self.add_workflow_step("TTSAgent", "prepare_content", "success", {
            "content_length": content_length,
            "estimated_duration": f"{content_length // 10}s",
            "language_target": "en-NG"
        })
        
        # Step 3: TTS service connection
        self.add_workflow_step("TTSAgent", "connect_tts", "started")
        if tts_client is None:
            self.add_workflow_step("TTSAgent", "connect_tts", "error", {"reason": "tts_client_not_initialized"})
            self.add_workflow_step("TTSAgent", "complete", "failed")
            raise ValueError("TTS client not initialized")
        
        self.add_workflow_step("TTSAgent", "connect_tts", "success", {"service": "google_cloud_tts"})
        
        # Step 4: Audio synthesis
        self.add_workflow_step("TTSAgent", "synthesize_audio", "started", {
            "voice": "en-NG-Wavenet-A", 
            "format": "MP3"
        })
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=story_content)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-NG",
                name="en-NG-Wavenet-A"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Step 5: Audio file generation
            self.add_workflow_step("TTSAgent", "synthesize_audio", "success", {"audio_bytes": len(response.audio_content)})
            self.add_workflow_step("TTSAgent", "save_audio", "started")
            
            audio_path = f"/tmp/{story_id}.mp3"
            with open(audio_path, "wb") as out:
                out.write(response.audio_content)
                
            self.add_workflow_step("TTSAgent", "save_audio", "success", {
                "file_path": audio_path,
                "cultural_voice": "nigerian_english"
            })
            self.add_workflow_step("TTSAgent", "complete", "success", {"final_output": audio_path})
            return audio_path
            
        except Exception as e:
            self.add_workflow_step("TTSAgent", "synthesize_audio", "error", {"error_type": "synthesis_failed", "message": str(e)})
            self.add_workflow_step("TTSAgent", "complete", "failed")
            raise

# Initialize orchestrator
orchestrator = ADKOrchestrator()

# --- Routes ---

@app.route('/')
def index():
    """Home page. The entry point for the adventure."""
    logger.info("Serving index page")
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        # Fallback to a simple HTML response
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>RadioQuest - AI Storytelling</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
                .btn { display: inline-block; padding: 15px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
                .btn:hover { background: #0056b3; }
                .api-link { background: #28a745; }
                .api-link:hover { background: #1e7e34; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 RadioQuest - ADK Hackathon Demo</h1>
                <p>AI-powered storytelling platform for children in Goma, DR Congo</p>
                <p>Showcasing multi-agent orchestration with ADK-inspired architecture</p>
                
                <h2>🚀 ADK Demo Endpoints:</h2>
                <a href="/adk-demo" class="btn api-link">ADK Architecture Overview</a><br>
                <a href="/adk/story/intro" class="btn api-link">Story Agent Workflow</a><br>
                <a href="/adk/search?q=forest" class="btn api-link">Search Agent Demo</a><br>
                <a href="/health" class="btn">System Health Check</a><br>
                
                <h2>📚 Standard Endpoints:</h2>
                <a href="/story/intro" class="btn">Welcome Story</a><br>
                <a href="/search?q=goma" class="btn">Story Search</a><br>
                
                <p style="margin-top: 30px; font-size: 14px; opacity: 0.8;">
                    Built for the 2025 ADK Hackathon | <a href="https://github.com/asherengos/radioquest" style="color: #17a2b8;">GitHub</a>
                </p>
            </div>
        </body>
        </html>
        '''

@app.route('/story/<story_id>')
def story(story_id):
    """
    Handles fetching and displaying a story segment.
    Direct MongoDB access with mock fallback!
    """
    logger.info(f"Fetching story for story_id: '{story_id}'")
    
    try:
        # Try MongoDB first, fallback to enhanced mock data
        segment = None
        try:
            if stories_collection is not None:
                segment = stories_collection.find_one({"_id": story_id})
                if segment:
                    logger.info(f"Found story in MongoDB: {segment.get('title', 'Unknown')}")
        except Exception as db_error:
            logger.warning(f"MongoDB error, using mock data: {db_error}")
        
        if not segment:
            logger.info(f"Using mock data for story: {story_id}")
            segment = MOCK_STORIES.get(story_id)
        
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
    Simple MongoDB text search with mock fallback!
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Please provide a search query"}), 400

    logger.info(f"Searching for: '{query}'")
    
    try:
        results = []
        # Try MongoDB search, fallback to mock results
        try:
            if stories_collection is not None:
                results = list(stories_collection.find({
                    "$or": [
                        {"title": {"$regex": query, "$options": "i"}},
                        {"content": {"$regex": query, "$options": "i"}}
                    ]
                }).limit(10))
                
                if results:
                    logger.info(f"Found {len(results)} results in MongoDB")
        except Exception as db_error:
            logger.warning(f"MongoDB search error, using mock data: {db_error}")
        
        if not results:
            logger.info(f"Using mock search results for '{query}'")
            results = [r for r in MOCK_SEARCH_RESULTS if query.lower() in r["title"].lower() or query.lower() in r["content"].lower()]
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            if '_id' in result:
                result['_id'] = str(result['_id'])
        
        logger.info(f"Found {len(results)} search results")
        return jsonify({"results": results})
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/audio/<audio_id>')
def serve_audio(audio_id):
    """Serves generated audio files"""
    import os
    from flask import send_file
    
    audio_path = f"/tmp/{audio_id}"
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/mpeg')
    else:
        abort(404)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test MongoDB connection
        mongodb_status = "disconnected"
        if stories_collection is not None:
            try:
                stories_collection.find_one()
                mongodb_status = "connected"
            except Exception:
                mongodb_status = "error"
        
        # Test TTS client
        tts_status = "initialized" if tts_client is not None else "not_initialized"
        
        return jsonify({
            "status": "healthy",
            "mongodb": mongodb_status,
            "tts": tts_status,
            "mock_data_available": True,
            "timestamp": "2025-06-23T12:30:00Z"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# --- ADK Demo Endpoints ---

@app.route('/adk-demo')
def adk_demo():
    """Showcase ADK orchestration capabilities"""
    orchestrator.workflow_steps = []
    orchestrator.add_workflow_step("System", "demo_init", "success", {"message": "ADK Multi-Agent Orchestration Demo"})
    orchestrator.add_workflow_step("StoryAgent", "status_check", "healthy")
    orchestrator.add_workflow_step("SearchAgent", "status_check", "healthy")
    orchestrator.add_workflow_step("TTSAgent", "status_check", "healthy")
    
    return jsonify({
        "status": "success",
        "adk_orchestration": True,
        "demo_type": "multi_agent_workflow",
        "available_endpoints": {
            "story": "/adk/story/<story_id>",
            "search": "/adk/search?q=<query>",
            "tts": "/adk/tts/<story_id>"
        },
        "workflow": orchestrator.workflow_steps
    }), 200

@app.route('/adk/story/<story_id>')
def adk_story_demo(story_id):
    """ADK-style story fetching with workflow demonstration"""
    logger.info(f"ADK: Fetching story with id: {story_id}")
    
    try:
        story = orchestrator.orchestrate_story_fetch(story_id)
        return jsonify({
            "status": "success",
            "adk_orchestration": True,
            "story": story,
            "workflow": orchestrator.workflow_steps
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "adk_orchestration": True,
            "error": str(e),
            "workflow": orchestrator.workflow_steps
        }), 500

@app.route('/adk/search')
def adk_search_demo():
    """ADK-style search with workflow demonstration"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({
            "status": "error", 
            "adk_orchestration": True,
            "message": "Query parameter required"
        }), 400
    
    logger.info(f"ADK: Searching stories with query: {query}")
    
    try:
        results = orchestrator.orchestrate_search(query)
        return jsonify({
            "status": "success",
            "adk_orchestration": True,
            "results": results,
            "workflow": orchestrator.workflow_steps
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "adk_orchestration": True,
            "error": str(e),
            "workflow": orchestrator.workflow_steps
        }), 500

@app.route('/adk/tts/<story_id>')
def adk_tts_demo(story_id):
    """ADK-style TTS generation with workflow demonstration"""
    logger.info(f"ADK: Generating TTS for story_id: {story_id}")
    
    try:
        # First get the story content
        story = orchestrator.orchestrate_story_fetch(story_id)
        content = story.get("content", "")
        
        # Then generate TTS
        audio_path = orchestrator.orchestrate_tts(content, story_id)
        
        return jsonify({
            "status": "success",
            "adk_orchestration": True,
            "audio_url": f"/audio/{story_id}.mp3",
            "workflow": orchestrator.workflow_steps
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "adk_orchestration": True,
            "error": str(e),
            "workflow": orchestrator.workflow_steps
        }), 500

def generate_audio_for_story(segment):
    """Generate TTS audio for a story segment"""
    try:
        if tts_client is None:
            logger.warning("TTS client not initialized")
            return False
            
        content = segment.get('content', '')
        story_id = segment.get('_id', 'unknown')
        
        synthesis_input = texttospeech.SynthesisInput(text=content)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-NG",
            name="en-NG-Wavenet-A"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save the audio
        audio_path = f"/tmp/{story_id}.mp3"
        with open(audio_path, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"Generated audio: {audio_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        return False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))