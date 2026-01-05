import React, { useState, useRef } from 'react';
import './InputArea.css';

const InputArea = ({ onSendMessage, onUploadFile, isLoading }) => {
    const [message, setMessage] = useState('');
    const fileInputRef = useRef(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !isLoading) {
            onSendMessage(message);
            setMessage('');
        }
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            onUploadFile(file);
            // Reset file input
            e.target.value = '';
        } else {
            alert('Please select a PDF file');
        }
    };

    return (
        <div className="input-area">
            <form onSubmit={handleSubmit} className="input-form">
                <button
                    type="button"
                    className="btn-icon upload-btn"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    title="Upload PDF"
                >
                    📎
                </button>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept=".pdf"
                    style={{ display: 'none' }}
                />
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="message-input"
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    className="btn btn-primary send-btn"
                    disabled={isLoading || !message.trim()}
                >
                    {isLoading ? (
                        <div className="loading-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    ) : (
                        '➤'
                    )}
                </button>
            </form>
        </div>
    );
};

export default InputArea;
