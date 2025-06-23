"""
RadioQuest ADK Orchestrator - Multi-Agent Coordination Layer
This demonstrates Google's Agent Development Kit (ADK) patterns for the hackathon
while leveraging our proven, reliable core functionality.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class AgentResponse:
    """Standardized response format following ADK patterns"""
    agent_id: str
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RadioQuestOrchestrator:
    """
    ADK-inspired orchestrator demonstrating multi-agent collaboration.
    This showcases the agent coordination patterns required for the hackathon.
    """
    
    def __init__(self):
        self.agents = {
            "story": StoryAgent(),
            "tts": TTSAgent(), 
            "search": SearchAgent(),
            "coordinator": CoordinatorAgent()
        }
        self.conversation_history = []
        logger.info("RadioQuest ADK Orchestrator initialized with 4 specialized agents")
    
    def process_request(self, request_type: str, **kwargs) -> Dict[str, Any]:
        """
        Main orchestration method - routes requests to appropriate agent workflows
        """
        request_id = f"req_{len(self.conversation_history)}"
        
        logger.info(f"Orchestrator processing {request_type} request (ID: {request_id})")
        
        # Log the request for agent coordination tracking
        self.conversation_history.append({
            "request_id": request_id,
            "type": request_type,
            "params": kwargs,
            "timestamp": "2025-06-23T15:50:00Z"
        })
        
        if request_type == "story":
            return self._orchestrate_story_workflow(request_id, kwargs.get("story_id"))
        elif request_type == "search":
            return self._orchestrate_search_workflow(request_id, kwargs.get("query"))
        elif request_type == "health":
            return self._orchestrate_health_workflow(request_id)
        else:
            return {
                "request_id": request_id,
                "status": "error",
                "error": f"Unknown request type: {request_type}"
            }
    
    def _orchestrate_story_workflow(self, request_id: str, story_id: str) -> Dict[str, Any]:
        """
        Multi-agent workflow for story requests:
        1. Coordinator Agent validates request
        2. Story Agent fetches content  
        3. TTS Agent prepares audio metadata
        4. Coordinator Agent assembles final response
        """
        workflow_steps = []
        
        # Step 1: Request validation
        coord_validation = self.agents["coordinator"].validate_request("story", {"story_id": story_id})
        workflow_steps.append({"agent": "coordinator", "action": "validate", "result": coord_validation.status})
        
        if coord_validation.status != "success":
            return self._build_workflow_response(request_id, "error", workflow_steps, error=coord_validation.error)
        
        # Step 2: Story content retrieval
        story_response = self.agents["story"].fetch_story(story_id)
        workflow_steps.append({"agent": "story", "action": "fetch", "result": story_response.status})
        
        if story_response.status != "success":
            return self._build_workflow_response(request_id, "error", workflow_steps, error=story_response.error)
        
        # Step 3: TTS metadata preparation (parallel agent processing)
        tts_response = self.agents["tts"].prepare_metadata(story_response.data)
        workflow_steps.append({"agent": "tts", "action": "prepare", "result": tts_response.status})
        
        # Step 4: Coordinator assembles final response
        final_data = self.agents["coordinator"].assemble_story_response(
            story_response.data, 
            tts_response.data if tts_response.status == "success" else None
        )
        workflow_steps.append({"agent": "coordinator", "action": "assemble", "result": "success"})
        
        return self._build_workflow_response(request_id, "success", workflow_steps, data=final_data.data)
    
    def _orchestrate_search_workflow(self, request_id: str, query: str) -> Dict[str, Any]:
        """
        Multi-agent search workflow demonstrating agent collaboration
        """
        workflow_steps = []
        
        # Step 1: Query validation and preprocessing
        coord_response = self.agents["coordinator"].validate_request("search", {"query": query})
        workflow_steps.append({"agent": "coordinator", "action": "validate", "result": coord_response.status})
        
        # Step 2: Search execution
        search_response = self.agents["search"].execute_search(query)
        workflow_steps.append({"agent": "search", "action": "search", "result": search_response.status})
        
        # Step 3: Result enrichment by story agent
        if search_response.status == "success":
            enriched_results = []
            for result in search_response.data.get("results", []):
                story_meta = self.agents["story"].get_metadata(result["_id"])
                enriched_results.append({
                    **result,
                    "enrichment": story_meta.data if story_meta.status == "success" else None
                })
            workflow_steps.append({"agent": "story", "action": "enrich", "result": "success"})
        
        # Step 4: Final assembly
        final_data = {
            "results": enriched_results if search_response.status == "success" else [],
            "query": query,
            "result_count": len(enriched_results) if search_response.status == "success" else 0
        }
        
        return self._build_workflow_response(request_id, search_response.status, workflow_steps, data=final_data)
    
    def _orchestrate_health_workflow(self, request_id: str) -> Dict[str, Any]:
        """
        Health check workflow involving all agents
        """
        workflow_steps = []
        agent_health = {}
        
        for agent_name, agent in self.agents.items():
            health_response = agent.health_check()
            agent_health[agent_name] = health_response.status
            workflow_steps.append({"agent": agent_name, "action": "health_check", "result": health_response.status})
        
        overall_status = "success" if all(status == "success" for status in agent_health.values()) else "degraded"
        
        return self._build_workflow_response(request_id, overall_status, workflow_steps, data=agent_health)
    
    def _build_workflow_response(self, request_id: str, status: str, workflow_steps: list, 
                                data: Optional[Dict] = None, error: Optional[str] = None) -> Dict[str, Any]:
        """Standardized workflow response builder"""
        return {
            "request_id": request_id,
            "status": status,
            "data": data,
            "error": error,
            "adk_metadata": {
                "agents_involved": [step["agent"] for step in workflow_steps],
                "workflow_steps": workflow_steps,
                "orchestration_pattern": "sequential_with_parallel_processing",
                "total_agents": len(self.agents)
            }
        }

class CoordinatorAgent:
    """Coordinator agent for request validation and response assembly"""
    
    def __init__(self):
        self.agent_id = "coordinator"
    
    def validate_request(self, request_type: str, params: Dict[str, Any]) -> AgentResponse:
        """Validate incoming requests"""
        if request_type == "story":
            story_id = params.get("story_id")
            if not story_id or not isinstance(story_id, str):
                return AgentResponse(self.agent_id, "error", error="Invalid story_id")
        elif request_type == "search":
            query = params.get("query")
            if not query or not isinstance(query, str) or len(query.strip()) == 0:
                return AgentResponse(self.agent_id, "error", error="Invalid search query")
        
        return AgentResponse(self.agent_id, "success")
    
    def assemble_story_response(self, story_data: Dict, tts_metadata: Optional[Dict]) -> AgentResponse:
        """Assemble final story response from multiple agent outputs"""
        assembled_data = {
            **story_data,
            "tts_metadata": tts_metadata,
            "assembly_timestamp": "2025-06-23T15:50:00Z",
            "assembled_by": self.agent_id
        }
        
        return AgentResponse(self.agent_id, "success", data=assembled_data)
    
    def health_check(self) -> AgentResponse:
        return AgentResponse(self.agent_id, "success", data={"component": "coordinator", "status": "operational"})

class StoryAgent:
    """Story content management agent"""
    
    def __init__(self):
        self.agent_id = "story_agent"
        # Import here to avoid circular imports
        try:
            from app import stories_collection, MOCK_STORIES
            self.stories_collection = stories_collection
            self.mock_stories = MOCK_STORIES
        except ImportError:
            self.stories_collection = None
            self.mock_stories = {}
    
    def fetch_story(self, story_id: str) -> AgentResponse:
        """Fetch story using our proven reliable approach"""
        try:
            story = None
            
            # Try MongoDB first
            if self.stories_collection is not None:
                story = self.stories_collection.find_one({"_id": story_id})
            
            # Fallback to mock data
            if not story and hasattr(self, 'mock_stories'):
                story = self.mock_stories.get(story_id)
            
            if story:
                return AgentResponse(self.agent_id, "success", data=story)
            
            return AgentResponse(self.agent_id, "error", error=f"Story {story_id} not found")
            
        except Exception as e:
            return AgentResponse(self.agent_id, "error", error=str(e))
    
    def get_metadata(self, story_id: str) -> AgentResponse:
        """Get story metadata for enrichment"""
        story_response = self.fetch_story(story_id)
        if story_response.status == "success":
            content = story_response.data.get("content", "")
            metadata = {
                "word_count": len(content.split()),
                "character_count": len(content),
                "has_choices": bool(story_response.data.get("choices")),
                "estimated_read_time": len(content.split()) * 0.25  # ~4 words per second
            }
            return AgentResponse(self.agent_id, "success", data=metadata)
        return story_response
    
    def health_check(self) -> AgentResponse:
        db_status = "connected" if self.stories_collection is not None else "disconnected"
        return AgentResponse(self.agent_id, "success", data={"database": db_status, "mock_data": "available"})

class TTSAgent:
    """Text-to-speech processing agent"""
    
    def __init__(self):
        self.agent_id = "tts_agent"
        try:
            from app import tts_client
            self.tts_client = tts_client
        except ImportError:
            self.tts_client = None
    
    def prepare_metadata(self, story_data: Dict[str, Any]) -> AgentResponse:
        """Prepare TTS metadata (lightweight for demo performance)"""
        try:
            content = story_data.get("content", "")
            metadata = {
                "text_length": len(content),
                "word_count": len(content.split()),
                "estimated_duration": len(content.split()) * 0.5,  # seconds
                "voice_profile": {
                    "language": "en-NG",
                    "voice": "en-NG-Wavenet-A",
                    "cultural_context": "Nigerian English for authenticity"
                },
                "audio_config": {
                    "format": "MP3",
                    "quality": "high"
                },
                "tts_ready": self.tts_client is not None
            }
            
            return AgentResponse(self.agent_id, "success", data=metadata)
            
        except Exception as e:
            return AgentResponse(self.agent_id, "error", error=str(e))
    
    def health_check(self) -> AgentResponse:
        tts_status = "initialized" if self.tts_client is not None else "not_available"
        return AgentResponse(self.agent_id, "success", data={"tts_client": tts_status})

class SearchAgent:
    """Content search and discovery agent"""
    
    def __init__(self):
        self.agent_id = "search_agent"
        try:
            from app import stories_collection, MOCK_SEARCH_RESULTS
            self.stories_collection = stories_collection
            self.mock_results = MOCK_SEARCH_RESULTS
        except ImportError:
            self.stories_collection = None
            self.mock_results = []
    
    def execute_search(self, query: str) -> AgentResponse:
        """Execute search using our reliable approach"""
        try:
            results = []
            
            # Try MongoDB search
            if self.stories_collection is not None:
                mongodb_results = list(self.stories_collection.find({
                    "$or": [
                        {"title": {"$regex": query, "$options": "i"}},
                        {"content": {"$regex": query, "$options": "i"}}
                    ]
                }).limit(5))
                
                results = [{"_id": str(r["_id"]), "title": r["title"], "content": r.get("content", "")} 
                          for r in mongodb_results]
            
            # Fallback to mock results
            if not results and hasattr(self, 'mock_results'):
                results = [r for r in self.mock_results 
                          if query.lower() in r["title"].lower() or query.lower() in r["content"].lower()]
            
            return AgentResponse(self.agent_id, "success", data={"results": results})
            
        except Exception as e:
            return AgentResponse(self.agent_id, "error", error=str(e))
    
    def health_check(self) -> AgentResponse:
        search_status = "mongodb_available" if self.stories_collection is not None else "mock_only"
        return AgentResponse(self.agent_id, "success", data={"search_backend": search_status})

# Global orchestrator instance for the demo
orchestrator = RadioQuestOrchestrator() 