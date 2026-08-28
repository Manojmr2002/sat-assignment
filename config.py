import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Upload and storage directories
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Secret Key
SECRET_KEY = os.environ.get('SECRET_KEY', 'sat-assignment-super-secret-key-2026')

# Ollama LLM Configuration
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')  # or mistral, phi3, gemma, etc.

# Optional Pinecone Configuration
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', '')
PINECONE_ENV = os.environ.get('PINECONE_ENV', 'us-east-1')
PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME', 'study-assistant')

# App Ports
PORT_MASTER = 5000
PORT_QUIZ = 5001
PORT_RAG = 5002
PORT_IT_DESK = 5003
PORT_STUDY = 5004
