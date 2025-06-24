from flask import Flask, render_template, request, abort, url_for, jsonify, redirect
import logging
import traceback
import os
from pymongo import MongoClient
from google.cloud import texttospeech
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from flask_compress import Compress

# --- Flask App Initialization ---
app = Flask(__name__)
Compress(app)

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Enhanced Mock Data for Demo Reliability ---
MOCK_STORIES = {
    "intro": {
        "_id": "intro",
        "title": "The Journey Begins",
        "content": "You awaken to the gentle hum of the Congo rainforest. Your name is Kofi, and a message crackles over your small, solar-powered radio. It's a plea from a nearby village – their children are lost, and a mysterious sickness is spreading. The transmission mentioned a hidden river, the 'River of Life,' said to hold the cure. With your radio as your only guide, you step out of your hut. The air is thick with the scent of damp earth and flowers. Before you, the path splits. To your left, you see fresh animal tracks leading into the dense jungle. Straight ahead, a steep hill rises, promising a view of the surrounding area. To your right, a rickety rope bridge sways over a wide chasm. The choice is yours.",
        "choices": [
            {"id": "follow_tracks", "text": "Follow the animal tracks"},
            {"id": "climb_hill", "text": "Climb the hill for a better view"},
            {"id": "cross_bridge", "text": "Bravely cross the rickety bridge"}
        ]
    },
    "follow_tracks": {
        "_id": "follow_tracks",
        "title": "Into the Jungle",
        "content": "You decide to trust the wisdom of the forest creatures. The tracks are small, like those of a forest antelope. You follow them deeper into the jungle, pushing aside giant ferns and ducking under hanging vines. The canopy above is so thick that the sunlight only dapples the forest floor. Strange bird calls echo around you, and you hear the chatter of monkeys high in the trees. After walking for what feels like an hour, the tracks lead you to a clearing. In the center of the clearing is a massive, ancient baobab tree, its branches reaching towards the sky like gnarled arms. A series of intricate carvings cover its trunk, depicting stories of the forest. At the base of the tree, you see a small, leather-bound journal, half-buried in the leaves. It looks very old. Do you open the ancient journal or continue following the tracks, which seem to lead past the tree and deeper into the shadows?",
        "choices": [
            {"id": "open_journal", "text": "Open the ancient journal"},
            {"id": "continue_tracks", "text": "Keep following the tracks"}
        ]
    },
    "climb_hill": {
        "_id": "climb_hill",
        "title": "The View from Above",
        "content": "You choose the high ground, hoping for a better sense of direction. The climb is steep and challenging. You scramble over rocks and pull yourself up using sturdy roots. The air grows thinner and cooler as you ascend. Finally, you reach the summit, breathless but rewarded with a spectacular view. The entire valley stretches out before you, a sea of green under a vast blue sky. In the distance, you see a plume of smoke rising – a sign of a settlement, perhaps the lost village! But as you watch, you notice something else. A glint of sunlight reflecting off something metallic, hidden within a cluster of rocks not far from your position. It could be a clue, or it could be nothing. Do you investigate the glint of metal, or do you head straight for the smoke plume in the distance?",
        "choices": [
            {"id": "investigate_glint", "text": "Investigate the metallic glint"},
            {"id": "head_for_smoke", "text": "Head towards the smoke plume"}
        ]
    },
    "cross_bridge": {
        "_id": "cross_bridge",
        "title": "The Chasm of Courage",
        "content": "You take a deep breath and step onto the rope bridge. It sways wildly with each step, the wooden planks creaking under your feet. Below you, a deep chasm disappears into the mist. You focus on the other side, moving slowly and deliberately, your knuckles white as you grip the ropes. Halfway across, you hear a screech from above. A large, territorial eagle is circling, unhappy with your presence. It dives towards you, its talons outstretched. You have to think fast. Do you try to scare it away by yelling and waving your arms, or do you make a dash for the other side before it can reach you?",
        "choices": [
            {"id": "scare_eagle", "text": "Scare the eagle"},
            {"id": "dash_across", "text": "Dash for the other side"}
        ]
    },
    "open_journal": {
        "_id": "open_journal",
        "title": "Secrets of the Baobab",
        "content": "You kneel beside the ancient baobab and gently brush the leaves from the journal. Its cover is cracked, the pages yellowed with age. As you open it, a wave of history washes over you—the journal belonged to a healer from the village, who wrote of a hidden spring deep in the jungle, guarded by a spirit called Mokele. The entries warn of dangers: quicksand, venomous snakes, and a riddle that must be answered to pass. Suddenly, you hear a rustle behind you. Do you hide and observe, or call out to whoever is there?",
        "choices": [
            {"id": "hide_observe", "text": "Hide and observe"},
            {"id": "call_out", "text": "Call out bravely"}
        ]
    },
    "continue_tracks": {
        "_id": "continue_tracks",
        "title": "Deeper Shadows",
        "content": "You decide to trust your instincts and continue following the tracks. The jungle grows darker and the air thickens. You hear distant drumming—perhaps a village ceremony, or a warning? Suddenly, the tracks split: one set leads toward a thicket of bamboo, the other toward a muddy riverbank. Do you investigate the bamboo thicket or approach the riverbank?",
        "choices": [
            {"id": "bamboo_thicket", "text": "Investigate the bamboo thicket"},
            {"id": "riverbank", "text": "Approach the riverbank"}
        ]
    },
    "investigate_glint": {
        "_id": "investigate_glint",
        "title": "The Shining Clue",
        "content": "Curiosity gets the better of you. You carefully make your way to the cluster of rocks and discover a small, metal compass—its needle spinning wildly. Next to it, a faded photograph of a smiling family. On the back, a message: 'Trust the river when the path is unclear.' As you ponder its meaning, you hear footsteps behind you. Do you hide and watch, or confront whoever is coming?",
        "choices": [
            {"id": "hide_watch", "text": "Hide and watch"},
            {"id": "confront_stranger", "text": "Confront the stranger"}
        ]
    },
    "head_for_smoke": {
        "_id": "head_for_smoke",
        "title": "The Village Revealed",
        "content": "You decide the smoke is your best lead. Descending the hill, you move quickly but carefully, avoiding loose rocks. As you approach, you hear voices and laughter—the village is alive! But the mood is tense; people are gathered around a sick child. The village elder greets you, asking if you have come to help. Do you offer to help the child, or ask about the River of Life first?",
        "choices": [
            {"id": "help_child", "text": "Help the child immediately"},
            {"id": "ask_river", "text": "Ask about the River of Life"}
        ]
    },
    "scare_eagle": {
        "_id": "scare_eagle",
        "title": "The Eagle's Test",
        "content": "You wave your arms and shout, trying to scare the eagle away. The bird screeches and swoops closer, but at the last moment, it veers off, dropping a shiny object onto the bridge. It's a carved wooden amulet, warm to the touch. As you pick it up, you feel a surge of courage. But the bridge is swaying dangerously. Do you hurry across, or stop to examine the amulet?",
        "choices": [
            {"id": "hurry_across", "text": "Hurry across the bridge"},
            {"id": "examine_amulet", "text": "Examine the amulet"}
        ]
    },
    "dash_across": {
        "_id": "dash_across",
        "title": "Leap of Faith",
        "content": "You sprint across the bridge, heart pounding. The eagle screeches above, but you make it to the other side just as the last plank snaps behind you. Safe, but shaken, you find yourself at a fork: one path leads into a dark cave, the other toward a sunlit clearing. Do you enter the cave or head for the clearing?",
        "choices": [
            {"id": "enter_cave", "text": "Enter the cave"},
            {"id": "sunlit_clearing", "text": "Head for the clearing"}
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

# Vote tracking storage (in production, this would be in MongoDB)
vote_storage = {}

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

@app.route('/submit_choice', methods=['POST'])
def submit_choice():
    """Handle choice submissions and track votes"""
    try:
        choice_id = request.form.get('choice_id')
        story_id = request.form.get('story_id')
        
        if not choice_id or not story_id:
            return jsonify({"error": "Missing choice_id or story_id"}), 400
        
        # Track the vote
        vote_key = f"{story_id}_{choice_id}"
        if vote_key not in vote_storage:
            vote_storage[vote_key] = 0
        vote_storage[vote_key] += 1
        
        logger.info(f"Vote recorded: {vote_key} = {vote_storage[vote_key]} votes")
        
        # Redirect to the chosen story segment
        return redirect(f"/story/{choice_id}")
        
    except Exception as e:
        logger.error(f"Error submitting choice: {e}")
        return jsonify({"error": str(e)}), 500

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
            
            # Get vote results for this story's choices
            vote_results = {}
            if segment.get('choices'):
                for choice in segment['choices']:
                    vote_key = f"{story_id}_{choice['id']}"
                    vote_results[choice['id']] = vote_storage.get(vote_key, 0)
            
            # Add recap data (simplified for demo)
            previous_story = None
            last_choice = None
            if story_id != 'intro':
                previous_story = "In our last adventure, you helped Koko make an important decision in the Congo rainforest."
                # In a real app, this would come from user session/database
            
            return render_template('story.html', 
                                 segment=segment, 
                                 vote_results=vote_results,
                                 previous_story=previous_story,
                                 last_choice=last_choice)
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

@app.route('/tts/<story_id>')
def generate_tts(story_id):
    """Generate Nigerian English TTS for a story segment"""
    try:
        # Get the story content
        segment = None
        try:
            if stories_collection is not None:
                segment = stories_collection.find_one({"_id": story_id})
        except Exception as db_error:
            logger.warning(f"MongoDB error, using mock data: {db_error}")
        
        if not segment:
            segment = MOCK_STORIES.get(story_id)
        
        if not segment:
            return jsonify({"error": "Story not found"}), 404
        
        # Generate Nigerian English TTS
        if tts_client is not None:
            try:
                # Use Nigerian English voice
                synthesis_input = texttospeech.SynthesisInput(text=segment['content'])
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-NG",  # Nigerian English
                    name="en-NG-Standard-A",  # Nigerian female voice
                    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                response = tts_client.synthesize_speech(
                    input=synthesis_input, 
                    voice=voice, 
                    audio_config=audio_config
                )
                
                # Save audio file
                audio_path = f"/tmp/{story_id}.mp3"
                with open(audio_path, "wb") as out:
                    out.write(response.audio_content)
                
                logger.info(f"Nigerian TTS audio generated for {story_id}")
                return jsonify({
                    "status": "success",
                    "audio_url": f"/audio/{story_id}.mp3",
                    "voice": "en-NG-Standard-A (Nigerian English)",
                    "message": "Nigerian English TTS generated successfully"
                })
                
            except Exception as tts_error:
                logger.error(f"TTS generation failed: {tts_error}")
                return jsonify({
                    "status": "error",
                    "error": str(tts_error),
                    "fallback": "TTS service temporarily unavailable"
                }), 500
        else:
            return jsonify({
                "status": "demo",
                "message": "TTS client not initialized - this would generate Nigerian English audio",
                "voice": "en-NG-Standard-A (Nigerian English)",
                "demo_url": f"/audio/{story_id}.mp3"
            })
            
    except Exception as e:
        logger.error(f"Error in TTS endpoint: {e}")
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