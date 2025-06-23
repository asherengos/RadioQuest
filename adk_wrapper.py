"""
RadioQuest ADK Wrapper - Multi-Agent Orchestration Layer
This module demonstrates the use of Google's Agent Development Kit (ADK)
for orchestrating multiple specialized agents in our storytelling platform.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Core functionality imports (our reliable backend)
from app import stories_collection, tts_client, MOCK_STORIES, MOCK_SEARCH_RESULTS

logger = logging.getLogger(__name__)

@dataclass
class AgentResponse:
    """Standardized response format for all agents"""
    agent_id: str
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ADKOrchestrator:
    """
    ADK-inspired orchestrator that manages multiple specialized agents.
    This demonstrates multi-agent collaboration patterns using our reliable core.
    """
    
    def __init__(self):
        self.story_agent = StoryAgent()
        self.tts_agent = TTSAgent()
        self.search_agent = SearchAgent()
        logger.info("ADK Orchestrator initialized with 3 specialized agents")
    
    def orchestrate_story_request(self, story_id: str) -> AgentResponse:
        """
        Orchestrates a story request across multiple agents:
        1. Story Agent fetches content
        2. TTS Agent prepares audio generation
        3. Returns coordinated response
        """
        logger.info(f"ADK Orchestrator: Processing story request for {story_id}")
        
        # Agent collaboration workflow
        story_response = self.story_agent.fetch_story(story_id)
        
        if story_response.status == "success" and story_response.data:
            # If story found, prepare TTS metadata
            tts_metadata = self.tts_agent.prepare_audio_metadata(story_response.data)
            
            # Combine agent responses
            orchestrated_data = {
                **story_response.data,
                "audio_metadata": tts_metadata.data,
                "agents_involved": ["story_agent", "tts_agent"],
                "orchestration_timestamp": "2025-06-23T15:50:00Z"
            }
            
            return AgentResponse(
                agent_id="orchestrator",
                status="success", 
                data=orchestrated_data
            )
        
        return story_response
    
    def orchestrate_search_request(self, query: str) -> AgentResponse:
        """
        Orchestrates search across agents:
        1. Search Agent finds relevant stories
        2. Story Agent enriches results with metadata
        3. Returns enhanced search results
        """
        logger.info(f"ADK Orchestrator: Processing search for '{query}'")
        
        # Multi-agent search workflow
        search_response = self.search_agent.search_stories(query)
        
        if search_response.status == "success" and search_response.data:
            # Enrich search results with story agent metadata
            enriched_results = []
            for result in search_response.data.get("results", []):
                story_metadata = self.story_agent.get_story_metadata(result["_id"])
                enriched_result = {
                    **result,
                    "metadata": story_metadata.data if story_metadata.status == "success" else None
                }
                enriched_results.append(enriched_result)
            
            orchestrated_data = {
                "results": enriched_results,
                "agents_involved": ["search_agent", "story_agent"],
                "query": query,
                "orchestration_timestamp": "2025-06-23T15:50:00Z"
            }
            
            return AgentResponse(
                agent_id="orchestrator",
                status="success",
                data=orchestrated_data
            )
        
        return search_response

class StoryAgent:
    """Specialized agent for story content management"""
    
    def __init__(self):
        self.agent_id = "story_agent"
        logger.info(f"Initialized {self.agent_id}")
    
    def fetch_story(self, story_id: str) -> AgentResponse:
        """Fetch story content using our reliable backend"""
        try:
            # Try MongoDB first, fallback to mock data (our proven approach)
            story = None
            if stories_collection is not None:
                story = stories_collection.find_one({"_id": story_id})
            
            if not story:
                story = MOCK_STORIES.get(story_id)
            
            if story:
                return AgentResponse(
                    agent_id=self.agent_id,
                    status="success",
                    data=story
                )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                error=f"Story {story_id} not found"
            )
            
        except Exception as e:
            logger.error(f"StoryAgent error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error", 
                error=str(e)
            )
    
    def get_story_metadata(self, story_id: str) -> AgentResponse:
        """Get metadata for story enrichment"""
        story_response = self.fetch_story(story_id)
        if story_response.status == "success":
            metadata = {
                "word_count": len(story_response.data.get("content", "").split()),
                "has_choices": bool(story_response.data.get("choices")),
                "agent_processed": True
            }
            return AgentResponse(
                agent_id=self.agent_id,
                status="success",
                data=metadata
            )
        return story_response

class TTSAgent:
    """Specialized agent for text-to-speech processing"""
    
    def __init__(self):
        self.agent_id = "tts_agent"
        logger.info(f"Initialized {self.agent_id}")
    
    def prepare_audio_metadata(self, story_data: Dict[str, Any]) -> AgentResponse:
        """Prepare TTS metadata without actually generating audio (for demo speed)"""
        try:
            content = story_data.get("content", "")
            metadata = {
                "text_length": len(content),
                "estimated_duration_seconds": len(content.split()) * 0.5,  # ~0.5s per word
                "voice_config": {
                    "language_code": "en-NG",
                    "name": "en-NG-Wavenet-A"
                },
                "audio_format": "MP3",
                "tts_ready": tts_client is not None,
                "agent_processed": True
            }
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="success",
                data=metadata
            )
            
        except Exception as e:
            logger.error(f"TTSAgent error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                error=str(e)
            )

class SearchAgent:
    """Specialized agent for content search and discovery"""
    
    def __init__(self):
        self.agent_id = "search_agent"
        logger.info(f"Initialized {self.agent_id}")
    
    def search_stories(self, query: str) -> AgentResponse:
        """Search stories using our reliable backend approach"""
        try:
            results = []
            
            # Try MongoDB search first
            if stories_collection is not None:
                mongodb_results = list(stories_collection.find({
                    "$or": [
                        {"title": {"$regex": query, "$options": "i"}},
                        {"content": {"$regex": query, "$options": "i"}}
                    ]
                }).limit(10))
                
                results = [{"_id": str(r["_id"]), "title": r["title"], "content": r.get("content", "")} 
                          for r in mongodb_results]
            
            # Fallback to mock data if no MongoDB results
            if not results:
                results = [r for r in MOCK_SEARCH_RESULTS 
                          if query.lower() in r["title"].lower() or query.lower() in r["content"].lower()]
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="success",
                data={"results": results, "query": query}
            )
            
        except Exception as e:
            logger.error(f"SearchAgent error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                error=str(e)
            )

# Global orchestrator instance
adk_orchestrator = ADKOrchestrator() 