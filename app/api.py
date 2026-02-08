"""
FastAPI Backend for RAG Chatbot
"""
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import existing logic
from app.core.loader import initialize_rag_system
from app.core.chatbot import create_chatbot

# Global state
app_state = {
    "vector_store": None,
    "chain": None,
    "initialized": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Try to initialize if vector store exists
    try:
        print("Starting up... Attempting to load existing vector store.")
        # We don't force recreate on startup to be faster
        vector_store = initialize_rag_system(force_recreate=False)
        if vector_store:
            app_state["vector_store"] = vector_store
            app_state["chain"] = create_chatbot(vector_store)
            app_state["initialized"] = True
            print("Startup initialization successful.")
        else:
            print("No vector store found or created. System needs initialization.")
    except Exception as e:
        print(f"Startup initialization failed (non-critical): {e}")
        print("System will need explicit initialization via /initialize endpoint.")
    
    yield
    
    # Shutdown logic
    print("Shutting down...")
    app_state["vector_store"] = None
    app_state["chain"] = None
    app_state["initialized"] = False

app = FastAPI(title="Organization Specific Chatbot API", lifespan=lifespan)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Pydantic models
class InitRequest(BaseModel):
    force_recreate: bool = False

class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List] = None

class SourceDocument(BaseModel):
    source: str
    page_content: str
    page: Optional[int] = None
    type: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]

class HealthResponse(BaseModel):
    status: str
    initialized: bool

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chatbot UI."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return {
        "message": "Welcome to the RAG Chatbot API! (UI index.html not found)",
        "documentation": "Go to /docs to interact with the API",
        "steps": [
            "1. Call /initialize to load documents",
            "2. Call /chat to ask questions"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and initialization status."""
    return {
        "status": "healthy", 
        "initialized": app_state["initialized"]
    }

@app.post("/initialize")
async def initialize_system(request: InitRequest = Body(...)):
    """Initialize or re-initialize the RAG system."""
    try:
        vector_store = initialize_rag_system(force_recreate=request.force_recreate)
        if not vector_store:
             raise Exception("Failed to create vector store. Check if documents exist in 'documents' folder.")
             
        app_state["vector_store"] = vector_store
        app_state["chain"] = create_chatbot(vector_store)
        app_state["initialized"] = True
        return {"message": "System initialized successfully", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Ask a question to the chatbot."""
    if not app_state["initialized"] or not app_state["chain"]:
        raise HTTPException(
            status_code=400, 
            detail="System not initialized. Please call /initialize first."
        )
    
    try:
        # Prepare inputs
        inputs = {"question": request.question}
        if request.chat_history:
            inputs["chat_history"] = request.chat_history
            
        # Get response
        result = app_state["chain"].invoke(inputs)
        
        # Process answer and sources
        answer = result["answer"]
        source_docs = result.get("source_documents", [])
        
        formatted_sources = []
        for doc in source_docs:
            formatted_sources.append(SourceDocument(
                source=doc.metadata.get("source", "Unknown"),
                page_content=doc.page_content,
                page=doc.metadata.get("page"),
                type=doc.metadata.get("type", "unknown")
            ))
            
        return {
            "answer": answer,
            "sources": formatted_sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
