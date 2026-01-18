import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message, isUser }) => {
    const isSystem = message.role === 'system';

    // Parse message content to extract documents
    const parseMessageContent = (content) => {
        const docRegex = /<user_document filename="([^"]+)"(?:\s+file_path="([^"]+)")?>([\s\S]*?)<\/user_document>/g;
        const documents = [];
        let match;

        while ((match = docRegex.exec(content)) !== null) {
            documents.push({
                filename: match[1],
                file_path: match[2] || null,
                content: match[3]
            });
        }

        // Remove document tags from the displayed message
        const cleanedContent = content.replace(docRegex, '').trim();

        return { documents, cleanedContent };
    };

    // Handle document click - open PDF in new tab
    const handleDocumentClick = (filePath) => {
        if (!filePath) return;

        // Extract filename from path
        const filename = filePath.split('/').pop();

        // Construct URL to backend document endpoint
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const documentUrl = `${API_BASE_URL}/documents/${filename}`;

        // Open in new tab
        window.open(documentUrl, '_blank');
    };

    const { documents, cleanedContent } = parseMessageContent(message.content);

    return (
        <div className={`message-wrapper ${isUser ? 'user-message' : isSystem ? 'system-message' : 'assistant-message'}`}>
            <div className="message-content">
                {!isSystem && (
                    <div className="message-avatar">
                        {isUser ? '👤' : '🤖'}
                    </div>
                )}
                <div className="message-bubble">
                    {/* Display attached documents */}
                    {documents.length > 0 && (
                        <div className="message-documents">
                            {documents.map((doc, index) => (
                                <div
                                    key={index}
                                    className="message-document"
                                    onClick={() => handleDocumentClick(doc.file_path)}
                                    style={{ cursor: doc.file_path ? 'pointer' : 'default' }}
                                    title={doc.file_path ? 'Click to open document' : ''}
                                >
                                    <span className="doc-icon">📄</span>
                                    <span className="doc-filename">{doc.filename}</span>
                                </div>
                            ))}
                        </div>
                    )}
                    {/* Display the actual message text */}
                    {cleanedContent && (
                        <div className="message-text">{cleanedContent}</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChatMessage;
