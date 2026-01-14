import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './components/ChatMessage';
import InputArea from './components/InputArea';
import Sidebar from './components/Sidebar';
import { api } from './api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [sessions, setSessions] = useState([]);
  const [pendingDocuments, setPendingDocuments] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load all sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load history when session changes
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const data = await api.getHistory(sessionId);
        if (data.history && data.history.length > 0) {
          setMessages(data.history);
        } else {
          setMessages([]);
        }
        // Clear pending documents when switching sessions
        setPendingDocuments([]);
      } catch (error) {
        console.error('Failed to load history:', error);
      }
    };
    loadHistory();
  }, [sessionId]);

  const loadSessions = async () => {
    try {
      const data = await api.getAllSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleNewChat = () => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    setMessages([]);
    setPendingDocuments([]);
  };

  const handleSelectSession = (selectedSessionId) => {
    setSessionId(selectedSessionId);
  };

  const handleDeleteSession = async (sessionIdToDelete) => {
    if (window.confirm('Are you sure you want to delete this chat?')) {
      try {
        await api.clearHistory(sessionIdToDelete);

        // Reload sessions
        await loadSessions();

        // If deleted session was current, create new session
        if (sessionIdToDelete === sessionId) {
          handleNewChat();
        }
      } catch (error) {
        console.error('Error deleting session:', error);
        alert('Failed to delete chat');
      }
    }
  };

  const handleSendMessage = async (messageText) => {
    // Build the complete user message with pending documents
    let completeMessageContent = messageText;

    if (pendingDocuments.length > 0) {
      // Add document tags to match backend format
      let docContent = '';
      for (const doc of pendingDocuments) {
        docContent += `\n<user_document filename="${doc.filename}" file_path="${doc.file_path}">\n[Document content will be processed by backend]\n</user_document>\n`;
      }
      completeMessageContent = docContent + '\n' + messageText;
    }

    // Add user message to UI with document tags
    const userMessage = { role: 'user', content: completeMessageContent };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Clear pending documents from UI (they're now part of the message)
    const docsToSend = [...pendingDocuments];
    setPendingDocuments([]);

    try {
      const response = await api.sendMessage(sessionId, messageText);
      console.log('API response in handleSendMessage:', response);

      // Add assistant response to UI
      const assistantMessage = { role: 'assistant', content: response.response };
      console.log('Assistant message to add:', assistantMessage);
      setMessages((prev) => [...prev, assistantMessage]);

      // Reload sessions to update the list
      loadSessions();
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, there was an error processing your message. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadFile = async (file) => {
    setIsLoading(true);

    try {
      const response = await api.uploadPDF(sessionId, file);

      // Add to pending documents (not to messages yet)
      setPendingDocuments((prev) => [
        ...prev,
        {
          filename: response.filename,
          file_path: response.file_path,
        },
      ]);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert(`Failed to upload ${file.name}. Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemovePendingDocument = (index) => {
    setPendingDocuments((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        currentSessionId={sessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
      />

      <div className="main-content">
        <header className="app-header">
          <div className="header-content">
            <h1 className="app-title">
              <span className="gradient-text">Chat</span>
            </h1>
          </div>
        </header>

        <main className="chat-container">
          <div className="messages-area">
            {messages.filter(msg => msg.role !== 'system').length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">💬</div>
                <h2>Start a Conversation</h2>
                <p>Ask me anything or upload a PDF document to get started!</p>
              </div>
            ) : (
              messages
                .filter(msg => msg.role !== 'system') // Don't show system prompts
                .map((msg, index) => (
                  <ChatMessage
                    key={index}
                    message={msg}
                    isUser={msg.role === 'user'}
                  />
                ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        <InputArea
          onSendMessage={handleSendMessage}
          onUploadFile={handleUploadFile}
          isLoading={isLoading}
          pendingDocuments={pendingDocuments}
          onRemovePendingDocument={handleRemovePendingDocument}
        />
      </div>
    </div>
  );
}

export default App;
