# RAG Chatbot with FastAPI

A Retrieval Augmented Generation (RAG) chatbot that answers questions from PDF and TXT documents using LangChain and FastAPI.

## Features

- 📄 Loads and processes multiple PDF and TXT files
- 🔍 Semantic search using vector embeddings (ChromaDB)
- 🧠 Powered by robust LangChain logic
- 🚀 Fast and scalable FastAPI backend
- 📚 Automatic source document citation

## Project Structure

```
gen/
├── app/
│   ├── api.py           # FastAPI server application
│   └── core/            # Core logic
│       ├── chatbot.py   # RAG chain and LLM interface
│       ├── config.py    # Configuration settings
│       └── loader.py    # Document loading and processing
├── documents/           # Place your PDF and TXT files here
├── vector_store/        # Auto-generated vector store (do not upload to git)
├── run_bot.bat          # Script to start the server
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this file)
└── README.md            # This file
```

## Setup Instructions

### 1. Set Up Environment

This project uses a virtual environment.

#### Windows
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root with your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free key from [Groq Console](https://console.groq.com/).

### 3. Add Documents

Place your files in the `documents/` directory:
- `.pdf` files
- `.txt` files

### 4. Run the Application

Double-click `run_bot.bat` or run:
```bash
.\run_bot.bat
```

Or manually:
```bash
.\venv\Scripts\uvicorn app.api:app --reload
```

## Usage

Access the API documentation at:
**`http://localhost:8000/docs`**

1.  **Initialize**: Call `POST /initialize` to load your documents into the vector store.
2.  **Chat**: Call `POST /chat` with a JSON body `{"question": "Your question here"}`.
3.  **Health Check**: `GET /health` to verify system status.

## Configuration

Modify `app/core/config.py` to change:
- `CHUNK_SIZE`: Text chunk size (default: 1000)
- `GROQ_MODEL`: LLM model (default: "llama3-70b-8192")
- `EMBEDDING_MODEL`: Local embedding model

## Requirements

- Python 3.8+
- Groq API key (Free)

## License

MIT
