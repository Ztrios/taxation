import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message, isUser }) => {
    const isSystem = message.role === 'system';

    return (
        <div className={`message-wrapper ${isUser ? 'user-message' : isSystem ? 'system-message' : 'assistant-message'}`}>
            <div className="message-content">
                {!isSystem && (
                    <div className="message-avatar">
                        {isUser ? '👤' : '🤖'}
                    </div>
                )}
                <div className="message-bubble">
                    <div className="message-text">{message.content}</div>
                </div>
            </div>
        </div>
    );
};

export default ChatMessage;
