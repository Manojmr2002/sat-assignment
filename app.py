import os
import sys
import subprocess
import threading
from flask import Flask, render_template, jsonify, request, redirect, url_for

# Base configuration
import config
from shared.llm_provider import llm

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Information about all 4 projects
PROJECTS = [
    {
        "id": "01_quiz_generator",
        "number": "01",
        "title": "AI Quiz Generator",
        "badge": "LangChain & Vector DB",
        "description": "Uploads candidate assessment documents or text, generates validated MCQs with 4 options, correct answer keys, detailed explanations, and PDF assessment sheet export.",
        "technologies": ["Ollama LLM", "LangChain", "Vector DB", "Flask", "HTML/CSS", "ReportLab"],
        "icon": "fa-brain",
        "port": config.PORT_QUIZ,
        "entry": "01_quiz_generator/app.py",
        "color": "#4f46e5"
    },
    {
        "id": "02_rag_chatbot",
        "number": "02",
        "title": "RAG Chatbot",
        "badge": "FAISS & Hybrid Synthesis",
        "description": "Uploads PDF documents into a FAISS vector index and answers queries synthesizing both retrieved document citations and broader LLM knowledge.",
        "technologies": ["Ollama LLM", "LangChain", "FAISS / Vector DB", "Flask", "HTML/CSS/JS"],
        "icon": "fa-comments",
        "port": config.PORT_RAG,
        "entry": "02_rag_chatbot/app.py",
        "color": "#2563eb"
    },
    {
        "id": "03_multi_agent_it_service_desk",
        "number": "03",
        "title": "Multi-Agent IT Service Desk",
        "badge": "5-Agent Collaborative Pipeline",
        "description": "Automated IT service management with 5 specialized agents (Manager, Troubleshooting, Knowledge, Database, Response). Features live workflow visualization and SQLite helpdesk backend.",
        "technologies": ["Ollama LLM", "Multi-Agent Orchestration", "SQLite", "Flask", "HTML/CSS/JS"],
        "icon": "fa-headset",
        "port": config.PORT_IT_DESK,
        "entry": "03_multi_agent_it_service_desk/app.py",
        "color": "#0284c7"
    },
    {
        "id": "04_ai_study_assistant",
        "number": "04",
        "title": "AI Study Assistant",
        "badge": "CrewAI & Pinecone",
        "description": "Upload study materials and engage a 3-agent Crew (Research Agent, Analysis Agent, Review Agent) to synthesize verified study guides and interactive 3D flashcards.",
        "technologies": ["CrewAI", "Pinecone / Vector DB", "Sentence Transformers", "Flask", "HTML/CSS/JS"],
        "icon": "fa-graduation-cap",
        "port": config.PORT_STUDY,
        "entry": "04_ai_study_assistant/app.py",
        "color": "#7c3aed"
    }
]

# Track running child sub-processes
SUBPROCESSES = {}

def start_sub_apps():
    """Start all 4 sub-applications on their dedicated ports in background threads."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    for p in PROJECTS:
        p_id = p["id"]
        entry_path = os.path.join(base_dir, p["entry"])
        if os.path.exists(entry_path):
            try:
                # Launch child process
                proc = subprocess.Popen(
                    [sys.executable, entry_path],
                    cwd=os.path.dirname(entry_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                SUBPROCESSES[p_id] = proc
                print(f"[*] Started {p['title']} on port {p['port']}")
            except Exception as e:
                print(f"[!] Failed to launch {p_id}: {e}")

@app.route('/')
def master_hub():
    ollama_info = llm.check_connection()
    return render_template('master_hub.html', projects=PROJECTS, ollama_info=ollama_info)

@app.route('/api/status')
def system_status():
    return jsonify({
        "ollama": llm.check_connection(),
        "projects": [{
            "id": p["id"],
            "title": p["title"],
            "port": p["port"],
            "running": p["id"] in SUBPROCESSES and SUBPROCESSES[p["id"]].poll() is None
        } for p in PROJECTS]
    })

if __name__ == '__main__':
    # Launch sub-apps on their respective ports
    start_sub_apps()
    print(f"================================================================")
    print(f"[*] AI ASSIGNMENT MASTER SUITE RUNNING ON http://localhost:{config.PORT_MASTER}")
    print(f"[*] 01 - Quiz Generator:        http://localhost:{config.PORT_QUIZ}")
    print(f"[*] 02 - RAG Chatbot:          http://localhost:{config.PORT_RAG}")
    print(f"[*] 03 - Multi-Agent IT Desk:  http://localhost:{config.PORT_IT_DESK}")
    print(f"[*] 04 - AI Study Assistant:   http://localhost:{config.PORT_STUDY}")
    print(f"================================================================")
    app.run(host='0.0.0.0', port=config.PORT_MASTER, debug=False)
