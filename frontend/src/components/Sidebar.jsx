import React, { useState } from 'react';
import './Sidebar.css';

function Sidebar({ sessions, currentSessionId, onNewChat, onSelectSession, onDeleteSession }) {
    const [menuOpen, setMenuOpen] = useState(null);

    const toggleMenu = (sessionId) => {
        setMenuOpen(menuOpen === sessionId ? null : sessionId);
    };

    const handleDelete = (e, sessionId) => {
        e.stopPropagation();
        setMenuOpen(null);
        onDeleteSession(sessionId);
    };

    const formatDate = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp * 1000);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <h2 className="sidebar-title">
                    <span className="gradient-text">AI Chatbot</span>
                </h2>
                <button onClick={onNewChat} className="btn btn-primary new-chat-btn">
                    <span className="plus-icon">+</span> New Chat
                </button>
            </div>

            <div className="sessions-list">
                {sessions.length === 0 ? (
                    <div className="empty-sessions">
                        <p>No chat history yet</p>
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.session_id}
                            className={`session-item ${currentSessionId === session.session_id ? 'active' : ''}`}
                            onClick={() => onSelectSession(session.session_id)}
                        >
                            <div className="session-content">
                                <div className="session-preview">{session.preview}</div>
                                <div className="session-time">{formatDate(session.updated_at)}</div>
                            </div>
                            <div className="session-actions">
                                <button
                                    className="menu-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        toggleMenu(session.session_id);
                                    }}
                                >
                                    ⋮
                                </button>
                                {menuOpen === session.session_id && (
                                    <div className="session-menu">
                                        <button
                                            className="menu-item delete"
                                            onClick={(e) => handleDelete(e, session.session_id)}
                                        >
                                            🗑️ Delete
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

export default Sidebar;
