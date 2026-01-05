import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message, isUser }) => {
    return (
        <div className={`message-wrapper ${isUser ? 'user-message' : 'assistant-message'}`}>
            <div className="message-content">
                <div className="message-avatar">
                    {isUser ? '👤' : '🤖'}
                </div>
                <div className="message-bubble">
                    <div className="message-text">{message.content}</div>
                </div>
            </div>
        </div>
    );
};

export default ChatMessage;
