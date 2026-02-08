@echo off
echo Starting RAG Chatbot Server...
call venv\Scripts\activate.bat
python -m uvicorn app.api:app --reload
pause
