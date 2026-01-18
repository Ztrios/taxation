# Document Upload Feature - Changes Summary

## Overview
Modified the document upload functionality to work like Gemini and Claude chat applications:
- Documents are uploaded and processed but NOT immediately sent to the LLM
- Extracted text is stored in a pending state
- Documents are displayed with PDF icons in the UI
- When the user sends a message, pending documents are included in `<user_document>` tags
- The UI shows the user's message with document indicators, not the raw extracted text

## Backend Changes

### 1. `/backend/main.py`
**Modified `UploadResponse` model:**
- Removed `extracted_text` field
- Added `file_path` field

**Modified `/upload` endpoint:**
- Changed to store documents in pending state using `storage.add_pending_document()`
- No longer adds documents directly to chat history
- Returns file path instead of extracted text preview

### 2. `/backend/services/storage.py`
**Added three new methods:**
- `add_pending_document(session_id, filename, file_path, extracted_text)` - Stores a document in pending state
- `get_pending_documents(session_id)` - Retrieves all pending documents for a session
- `clear_pending_documents(session_id)` - Clears pending documents after they're sent

**Storage structure:**
- Pending documents stored in Redis with key: `pending_docs:{session_id}`
- Each document contains: filename, file_path, extracted_text

### 3. `/backend/services/chat.py`
**Modified `chat()` method:**
- Checks for pending documents before processing user message
- If pending documents exist, wraps their content in `<user_document filename="...">` tags
- Prepends document content to the user's message
- Clears pending documents after including them in the message

**Message format sent to LLM:**
```
<user_document filename="document.pdf">
[extracted text content]
</user_document>

[user's actual message]
```

## Frontend Changes

### 1. `/frontend/src/App.jsx`
**Added state management:**
- New state: `pendingDocuments` - Array of uploaded but not-yet-sent documents
- Clears pending documents when switching sessions or creating new chat

**Modified `handleUploadFile()`:**
- No longer shows system messages with extracted text
- Adds uploaded documents to `pendingDocuments` state
- Shows simple alert on error instead of system message

**Modified `handleSendMessage()`:**
- Clears `pendingDocuments` from UI when message is sent (they're now part of the message)

**Added `handleRemovePendingDocument()`:**
- Allows users to remove pending documents before sending

### 2. `/frontend/src/components/InputArea.jsx`
**Added props:**
- `pendingDocuments` - Array of pending documents to display
- `onRemovePendingDocument` - Callback to remove a pending document

**Added UI elements:**
- Pending documents display area above the input form
- Each pending document shows: PDF icon (📄), filename, and remove button (✕)

### 3. `/frontend/src/components/InputArea.css`
**Added styles:**
- `.pending-documents` - Container for pending documents
- `.pending-document` - Individual document card with hover effects
- `.pdf-icon` - PDF emoji styling
- `.document-name` - Filename with text overflow handling
- `.remove-doc-btn` - Remove button with hover effects

### 4. `/frontend/src/components/ChatMessage.jsx`
**Added document parsing:**
- `parseMessageContent()` function extracts `<user_document>` tags from message content
- Separates document metadata from actual message text
- Displays documents with PDF icons and filenames
- Shows clean message text without document tags

**Display structure:**
```
[Document indicators with PDF icons]
[User's message text]
```

### 5. `/frontend/src/components/ChatMessage.css`
**Added styles:**
- `.message-documents` - Container for documents in messages
- `.message-document` - Individual document display in messages
- Different styling for user vs assistant messages
- `.doc-icon` and `.doc-filename` for document display

## User Flow

### Before (Old Behavior):
1. User uploads PDF → Extracted text shown immediately in chat
2. Text is added to history right away
3. User sees the full extracted text in the UI

### After (New Behavior - Like Gemini/Claude):
1. User uploads PDF → Document processed and stored
2. PDF icon with filename appears in input area (pending state)
3. User types a message and hits send
4. Both document (in `<user_document>` tags) and message sent to LLM
5. UI shows user's message with PDF icon indicator
6. Document content sent to LLM but not displayed as raw text in UI

## Benefits
- ✅ Cleaner UI - No raw extracted text cluttering the chat
- ✅ Better UX - Matches familiar Gemini/Claude behavior
- ✅ More control - Users can remove documents before sending
- ✅ Context preservation - Documents are properly tagged for the LLM
- ✅ Multiple documents - Users can upload multiple PDFs before sending

## Testing Checklist
- [ ] Upload a PDF - should show in pending area
- [ ] Upload multiple PDFs - should show all in pending area
- [ ] Remove a pending document - should disappear from pending area
- [ ] Send message with pending documents - should show in chat with PDF icons
- [ ] Check backend - documents should be in `<user_document>` tags
- [ ] Switch sessions - pending documents should clear
- [ ] Create new chat - pending documents should clear
- [ ] Verify LLM receives document content properly
