
"""
Configuration settings for the RAG Chatbot
"""
import os
from dotenv import load_dotenv

# Get the project root directory
# app/core/config.py -> app/core -> app -> root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file in root
load_dotenv(os.path.join(ROOT_DIR, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Directory paths
DOCUMENT_DIRECTORY = os.path.join(ROOT_DIR, "documents")
VECTOR_STORE_DIRECTORY = os.path.join(ROOT_DIR, "vector_store")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 3
