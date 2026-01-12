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
from services.query_rewriter import query_rewriter

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


class QueryRewriteRequest(BaseModel):
    query: str
    context: Optional[str] = ""


class QueryRewriteResponse(BaseModel):
    original_query: str
    rewritten_queries: list[str]
    count: int


@app.get("/")
async def root():
    return {"message": "Chatbot API is running"}


@app.post("/test/rewrite", response_model=QueryRewriteResponse)
async def test_query_rewriter(request: QueryRewriteRequest):
    """
    Test endpoint for query rewriter.
    
    Example request:
    {
        "query": "Can I deduct my car?",
        "context": "I use it for work sometimes"
    }
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        rewritten = query_rewriter.rewrite(request.query, request.context)
        return QueryRewriteResponse(
            original_query=request.query,
            rewritten_queries=rewritten,
            count=len(rewritten)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewriter error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat messages with history management and RAG.
    """
    try:
        response = chat_service.chat(
            session_id=request.session_id,
            user_message=request.message,
            include_rag=request.include_rag,
        )
        return ChatResponse(response=response, session_id=request.session_id)
    except RuntimeError as e:
        # LLM upstream errors (OpenRouter/OpenAI compatible)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    Upload and process PDF file with OCR, then store in Weaviate for RAG.
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
        
        # Add extracted text to conversation context (Redis)
        storage.append_message(
            session_id=session_id,
            role="system",
            content=f"[PDF Document: {file.filename}]\n{extracted_text}"
        )
        
        # ✅ NEW: Upload to Weaviate for RAG
        chunks_uploaded = 0
        if chat_service.weaviate_client:
            try:
                collection = chat_service.weaviate_client.collections.get("Document")
                
                # Chunk the text (split into manageable pieces)
                words = extracted_text.split()
                chunk_size = 200  # words per chunk
                chunks = []
                
                for i in range(0, len(words), chunk_size):
                    chunk_text = " ".join(words[i:i + chunk_size])
                    if chunk_text.strip():
                        chunks.append(chunk_text)
                
                # Upload chunks to Weaviate
                with collection.batch.dynamic() as batch:
                    for idx, chunk in enumerate(chunks):
                        batch.add_object(
                            properties={
                                "content": chunk,
                                "source": file.filename,
                                "page": idx // 3,  # Approximate page number
                                "chunk_index": idx
                            }
                        )
                
                chunks_uploaded = len(chunks)
                print(f"✅ Uploaded {chunks_uploaded} chunks to Weaviate for RAG")
            
            except Exception as e:
                print(f"⚠️ Warning: Could not upload to Weaviate: {e}")
                # Continue anyway - text is still in chat history
        
        # Clean up file (optional - comment out if you want to keep uploads)
        # os.remove(file_path)
        
        return UploadResponse(
            message=f"PDF processed successfully. {chunks_uploaded} chunks uploaded to RAG database.",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
