# RadioQuest: Interactive AI Storytelling for Goma

Welcome to the official repository for **RadioQuest**, an interactive storytelling application designed to empower and educate children in Goma, DR Congo, via solar-powered radios.

## Live Demo
**[Launch RadioQuest](https://radioquest-17727531746.us-central1.run.app/)**

## Hackathon Demo Video
**[Watch our 3-minute demo on YouTube](https://youtu.be/QEUBqUkb4J8)**

## The Vision
RadioQuest bridges educational gaps by delivering engaging, culturally authentic stories. Listeners vote on story branches, shaping the narrative in real-time. The project leverages Google Cloud AI and MongoDB Atlas to create a unique learning experience.

## Tech Stack
- **Backend**: Flask (Python)
- **Database**: MongoDB Atlas with Vector Search
- **Deployment**: Google Cloud Run
- **AI Services**:
  - Google Cloud Text-to-Speech (with African accents)
  - Sentence-Transformers for embeddings

## Key Features
- Interactive, branching narratives
- Real-time voting via SMS or a simple web interface
- Authentic African-accented TTS audio
- AI-powered story search

## Getting Started

### Prerequisites
- Python 3.8+
- A MongoDB Atlas account
- Google Cloud SDK

### Local Setup
1.  **Clone the repository:**
    ```sh
    git clone https://github.com/asherengos/RadioQuest.git
    cd RadioQuest
    ```
2.  **Create a virtual environment:**
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    - Create a `.env` file by copying `.env.example`.
    - Fill in your `MONGO_URI` and `GOOGLE_APPLICATION_CREDENTIALS` path.
5.  **Run the application:**
    ```sh
    flask run
    ```

## Deployment
This project is designed for Google Cloud Run. See the `Dockerfile` for deployment configuration. For a detailed guide on our deployment struggles and solutions, see our [Workflow & Debugging Notes](workflow-debugging.md).

## Project Roadmap
See our [ROADMAP.md](ROADMAP.md) for future plans. 