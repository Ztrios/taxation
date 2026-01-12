const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
console.log('API_BASE_URL:', API_BASE_URL);

export const api = {
  async sendMessage(sessionId, message, includeRag = true) {
    console.log('Sending message to:', `${API_BASE_URL}/chat`);
    console.log('Request body:', { session_id: sessionId, message, include_rag: includeRag });

    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        include_rag: includeRag,
      }),
    });

    if (!response.ok) {
      console.error('Response not OK:', response.status, response.statusText);
      throw new Error('Failed to send message');
    }

    const data = await response.json();
    console.log('Received response:', data);
    return data;
  },

  async uploadPDF(sessionId, file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload PDF');
    }

    return response.json();
  },

  async getHistory(sessionId) {
    const response = await fetch(`${API_BASE_URL}/history/${sessionId}`);

    if (!response.ok) {
      throw new Error('Failed to get history');
    }

    return response.json();
  },

  async clearHistory(sessionId) {
    const response = await fetch(`${API_BASE_URL}/history/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to clear history');
    }

    return response.json();
  },

  async getAllSessions() {
    const response = await fetch(`${API_BASE_URL}/sessions`);

    if (!response.ok) {
      throw new Error('Failed to get sessions');
    }

    return response.json();
  },
};
