# AI Chatbot Application

A modern chatbot application with RAG (Retrieval-Augmented Generation), PDF processing, and persistent chat history.

## Features

- 🤖 **LLM Integration**: Connect to fine-tuned models via vLLM (OpenAI-compatible API)
- 📚 **RAG Support**: Weaviate vector database integration for context retrieval
- 📄 **PDF Processing**: Upload PDFs with intelligent text extraction (PyMuPDF + OCR fallback)
- 💬 **Continuous Conversation**: Automatic token management with 30K token limit
- 💾 **Persistent Storage**: Redis-backed chat history with local persistence
- 🎨 **Modern UI**: Beautiful dark theme with glassmorphism and smooth animations

## Architecture

### Backend (FastAPI)
- **Services**:
  - `chat.py`: LLM communication, RAG integration, token management
  - `pdf_handler.py`: PDF text extraction with PyMuPDF and Pytesseract fallback
  - `storage.py`: Redis session management
  - `tokenizer.py`: Token counting (placeholder for AutoTokenizer)

### Frontend (React + Vite)
- Modern chat interface with real-time messaging
- PDF upload with drag-and-drop support
- Session-based conversation history
- Responsive design

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis server
- Tesseract OCR (`brew install tesseract` on macOS)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Start Redis (if not running):
```bash
redis-server
```

6. Run the backend:
```bash
python main.py
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Configuration

Edit `backend/.env` with your settings:

```env
# OpenAI/vLLM Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://your-vllm-endpoint.com/v1
MODEL_NAME=your-fine-tuned-model-name

# Weaviate Configuration
WEAVIATE_URL=https://your-weaviate-instance.weaviate.network
WEAVIATE_API_KEY=your_weaviate_api_key

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Token Configuration
MAX_TOKENS=30000
MODEL_HF_PATH=your-huggingface-model-path
```

## Token Counting

The `backend/services/tokenizer.py` contains a placeholder function for token counting. Implement it using Hugging Face's AutoTokenizer:

```python
from transformers import AutoTokenizer
from config import settings

tokenizer = AutoTokenizer.from_pretrained(settings.model_hf_path)

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))
```

## API Endpoints

- `POST /chat`: Send a message
- `POST /upload`: Upload PDF document
- `GET /history/{session_id}`: Get chat history
- `DELETE /history/{session_id}`: Clear chat history

## Development

### Project Structure
```
.
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   └── services/
│       ├── chat.py
│       ├── pdf_handler.py
│       ├── storage.py
│       └── tokenizer.py
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    │       ├── ChatMessage.jsx
    │       └── InputArea.jsx
    └── package.json
```

## License

MIT



{redis-server 

 cd /home/junaid/Legal/LegalApptesting/taxation/backend && uvicorn main:app --host 0.0.0.0 --port 8000

 npm run devv
}