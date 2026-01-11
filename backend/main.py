from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from pathlib import Path

from config import settings
from services.chat import chat_service
from services.pdf_handler import pdf_handler
from services.storage import storage

app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    include_rag: bool = True


class ChatResponse(BaseModel):
    response: str
    session_id: str


class UploadResponse(BaseModel):
    message: str
    extracted_text: str
    filename: str


@app.get("/")
async def root():
    return {"message": "Chatbot API is running"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat messages with history management and RAG.
    """
    try:
        response = chat_service.chat(
            session_id=request.session_id,
            user_message=request.message,
            include_rag=request.include_rag
        )
        return ChatResponse(response=response, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    Upload and process PDF file with OCR.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.upload_dir, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text
        extracted_text = pdf_handler.extract_text(file_path)
        
        # Add extracted text to conversation context
        storage.append_message(
            session_id=session_id,
            role="system",
            content=f"[PDF Document: {file.filename}]\n{extracted_text}"
        )
        
        # Clean up file (optional - comment out if you want to keep uploads)
        # os.remove(file_path)
        
        return UploadResponse(
            message="PDF processed successfully",
            extracted_text=extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            filename=file.filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Clear chat history for a session.
    """
    storage.clear_history(session_id)
    return {"message": "History cleared successfully"}


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Retrieve chat history for a session.
    """
    history = storage.get_history(session_id)
    return {"session_id": session_id, "history": history}


@app.get("/sessions")
async def get_all_sessions():
    """
    Get all chat sessions with metadata.
    """
    try:
        sessions = storage.get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
