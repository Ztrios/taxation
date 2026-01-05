const API_BASE_URL = 'http://localhost:8000';

export const api = {
  async sendMessage(sessionId, message, includeRag = true) {
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
      throw new Error('Failed to send message');
    }

    return response.json();
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
};
