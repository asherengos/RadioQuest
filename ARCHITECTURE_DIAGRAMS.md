# RadioQuest Architecture Diagrams - Multiple Formats

## 1. ASCII Art Diagram

```
                    RadioQuest Multi-Agent Architecture
                    ===================================

    👨‍💻 Children in Goma
           |
           v
    📻 Solar Radio Interface
           |
           v
    🌐 RadioQuest Web Platform (Flask)
           |
           v
    ┌─────────────────────────────────────────────────────────────┐
    │                🎯 ADK Orchestrator                          │
    │              (Central Coordinator)                          │
    └─────────────────┬───────────────────────────────────────────┘
                      |
         ┌────────────┼────────────┬────────────┬────────────┐
         │            │            │            │            │
         v            v            v            v            v
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │📚 Story │  │🔍 Search│  │🔊 TTS   │  │🌍 Cultural│  │⚙️ Health│
    │ Agent   │  │ Agent   │  │ Agent   │  │ Agent    │  │ Monitor │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
         │            │            │            │            │
         v            v            v            v            v
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │🍃 MongoDB│  │🍃 MongoDB│  │🎙️ Google │  │🗄️ Firestore│  │📊 Metrics│
    │ Atlas   │  │ Atlas   │  │Cloud TTS│  │Database │  │Dashboard│
    └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
         │            │            │            │            │
         └────────────┼────────────┼────────────┼────────────┘
                      v            v            v
                 ┌─────────────────────────────────────┐
                 │     ☁️ Google Cloud Platform        │
                 │  ┌─────────┐ ┌─────────┐ ┌─────────┐│
                 │  │Cloud Run│ │Storage  │ │Firestore││
                 │  └─────────┘ └─────────┘ └─────────┘│
                 └─────────────────────────────────────┘
```

## 2. Python Class Structure Diagram

```python
# RadioQuest Architecture as Python Classes

class RadioQuestArchitecture:
    """Complete system architecture representation"""
    
    def __init__(self):
        self.user_layer = UserLayer()
        self.platform_layer = PlatformLayer()
        self.orchestration_layer = OrchestrationLayer()
        self.agent_layer = AgentLayer()
        self.service_layer = ServiceLayer()
        self.infrastructure_layer = InfrastructureLayer()

class UserLayer:
    """User interface and interaction points"""
    def __init__(self):
        self.children_in_goma = "👨‍💻 Primary Users"
        self.solar_radio = "📻 Main Interface"
        self.mobile_devices = "📱 Secondary Interface"

class PlatformLayer:
    """Web application and API layer"""
    def __init__(self):
        self.flask_app = "🌐 RadioQuest Web Platform"
        self.rest_api = "🔌 RESTful Endpoints"
        self.cultural_ui = "🦁 Amazing Africa Interface"

class OrchestrationLayer:
    """Central coordination and workflow management"""
    def __init__(self):
        self.adk_orchestrator = ADKOrchestrator()
        self.workflow_tracker = WorkflowTracker()
        self.error_handler = ErrorHandler()

class ADKOrchestrator:
    """Main orchestration engine"""
    def __init__(self):
        self.story_agent = StoryAgent()
        self.search_agent = SearchAgent()
        self.tts_agent = TTSAgent()
        self.cultural_agent = CulturalAgent()
        self.health_monitor = HealthMonitor()
    
    def coordinate_workflow(self, request_type, payload):
        """Coordinate multi-agent workflows"""
        if request_type == "story_request":
            story_result = self.story_agent.fetch_content(payload['story_id'])
            if story_result['status'] == 'success':
                tts_task = self.tts_agent.generate_audio(story_result['content'])
                cultural_check = self.cultural_agent.validate_content(story_result)
                return self.merge_results(story_result, tts_task, cultural_check)

class StoryAgent:
    """Content management and story fetching"""
    def __init__(self):
        self.mongodb_client = MongoDBClient()
        self.fallback_data = MockDataService()
    
    def fetch_content(self, story_id):
        try:
            return self.mongodb_client.get_story(story_id)
        except Exception:
            return self.fallback_data.get_mock_story(story_id)

class TTSAgent:
    """Audio generation and voice synthesis"""
    def __init__(self):
        self.google_tts_client = GoogleCloudTTSClient()
        self.voice_config = {
            'language_code': 'en-NG',
            'name': 'en-NG-Wavenet-A',
            'speaking_rate': 0.9,
            'pitch': 2.0
        }
```

## 3. Component Flow Diagram

```
RadioQuest Request Flow
======================

USER REQUEST → PLATFORM → ORCHESTRATOR → AGENTS → SERVICES → RESPONSE

Step 1: User Interaction
📻 Solar Radio → HTTP Request → 🌐 Flask App (Port 8080)

Step 2: Request Routing  
🔌 API Endpoints:
├── /adk/story/<id>     → Story Workflow
├── /adk/search?q=<>    → Search Workflow  
├── /adk/tts/<id>       → TTS Workflow
└── /adk-demo           → Architecture Demo

Step 3: Orchestration
🎯 ADK Orchestrator:
├── Workflow Tracking   → Log each step
├── Agent Coordination  → Delegate tasks
├── Error Handling      → Graceful fallbacks
└── Result Aggregation  → Merge responses

Step 4: Agent Processing
📚 Story Agent    → 🍃 MongoDB Atlas     → Story Content
🔍 Search Agent   → 🍃 MongoDB Atlas     → Search Results  
🔊 TTS Agent      → 🎙️ Google Cloud TTS → Audio Files
🌍 Cultural Agent → 🗄️ Firestore        → Validation Rules

Step 5: Service Integration
☁️ Google Cloud Platform:
├── Cloud Run      → Serverless scaling
├── Cloud Storage  → Audio file hosting
├── Firestore      → Real-time data
└── TTS Service    → Nigerian English synthesis

Step 6: Response Delivery
📱 JSON Response → 🌐 Web Interface → 📻 Radio → 👨‍💻 Children
```

## 4. Agent Interaction Matrix

```python
# Agent Dependencies and Communication Patterns

AGENT_INTERACTIONS = {
    'StoryAgent': {
        'depends_on': ['MongoDB', 'MockData'],
        'communicates_with': ['TTSAgent', 'CulturalAgent'],
        'provides_to': ['Orchestrator', 'TTSAgent']
    },
    'SearchAgent': {
        'depends_on': ['MongoDB', 'SearchIndex'],
        'communicates_with': ['CulturalAgent'],
        'provides_to': ['Orchestrator', 'UserInterface']
    },
    'TTSAgent': {
        'depends_on': ['GoogleCloudTTS', 'AudioSamples'],
        'communicates_with': ['StoryAgent', 'CulturalAgent'],
        'provides_to': ['Orchestrator', 'AudioDelivery']
    },
    'CulturalAgent': {
        'depends_on': ['Firestore', 'CommunityRules'],
        'communicates_with': ['StoryAgent', 'SearchAgent', 'TTSAgent'],
        'provides_to': ['Orchestrator', 'ContentValidation']
    }
}

# Workflow Patterns
WORKFLOW_PATTERNS = {
    'sequential': ['StoryAgent', 'CulturalAgent', 'TTSAgent'],
    'parallel': ['TTSAgent', 'CulturalAgent'],
    'conditional': 'if story_valid then generate_audio else fallback'
}
```

## 5. Deployment Architecture

```yaml
# Google Cloud Run Configuration
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: radioquest-adk
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/radioquest:latest
        ports:
        - containerPort: 8080
        env:
        - name: MONGO_URI
          valueFrom:
            secretKeyRef:
              name: mongo-credentials
              key: uri
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: "/etc/secrets/gcp-creds.json"
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
```

## 6. Real-time Monitoring

```python
class RadioQuestMonitor:
    """System health and performance tracking"""
    
    def __init__(self):
        self.agent_metrics = {
            'story_agent': {'requests': 0, 'avg_response_time': 0},
            'search_agent': {'requests': 0, 'avg_response_time': 0},
            'tts_agent': {'requests': 0, 'avg_response_time': 0},
            'cultural_agent': {'requests': 0, 'avg_response_time': 0}
        }
    
    def track_workflow(self, workflow_id, agent_name, operation, duration):
        """Track agent performance in real-time"""
        self.agent_metrics[agent_name]['requests'] += 1
        current_avg = self.agent_metrics[agent_name]['avg_response_time']
        new_avg = (current_avg + duration) / 2
        self.agent_metrics[agent_name]['avg_response_time'] = new_avg
    
    def health_check(self):
        """Generate system health report"""
        return {
            'mongodb_status': self.check_mongodb(),
            'tts_service_status': self.check_google_tts(),
            'agent_health': self.agent_metrics,
            'overall_status': 'healthy' if all(self.service_checks()) else 'degraded'
        }
```

## 7. Agent Workflow Pseudocode

```python
def handle_user_request(request):
    """Main request handler with ADK orchestration"""
    
    orchestrator = ADKOrchestrator()
    workflow_id = orchestrator.start_workflow(request.type)
    
    try:
        if request.type == "story":
            return handle_story_request(orchestrator, request)
        elif request.type == "search":
            return handle_search_request(orchestrator, request)
        elif request.type == "tts":
            return handle_tts_request(orchestrator, request)
    except Exception as error:
        return orchestrator.handle_error(workflow_id, error)

def handle_story_request(orchestrator, request):
    """Story workflow with multi-agent coordination"""
    
    # Step 1: Story Agent fetches content
    orchestrator.log_step("StoryAgent", "fetch_content", "started")
    story_result = story_agent.get_story(request.story_id)
    
    if story_result.status == "success":
        # Step 2: Parallel processing
        parallel_tasks = [
            lambda: tts_agent.generate_audio(story_result.content),
            lambda: cultural_agent.validate_content(story_result.content)
        ]
        
        parallel_results = orchestrator.execute_parallel(parallel_tasks)
        
        # Step 3: Aggregate results
        final_result = orchestrator.aggregate_results(
            story_result, 
            parallel_results
        )
        
        return final_result
    else:
        return orchestrator.fallback_response(request.story_id)
``` 
