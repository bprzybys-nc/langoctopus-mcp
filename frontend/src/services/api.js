import io from 'socket.io-client';

// Socket.IO connection
const socket = io();

// API URLs
const API_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000';

// Get sample questions
export const getSampleQuestions = async () => {
  try {
    const response = await fetch(`${API_URL}/api/sample_questions`);
    if (!response.ok) {
      throw new Error('Failed to fetch sample questions');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching sample questions:', error);
    return [];
  }
};

// Send a question through the HTTP API
export const sendQuestion = async (question) => {
  try {
    const response = await fetch(`${API_URL}/api/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to send question');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error sending question:', error);
    throw error;
  }
};

// Send a message via Socket.IO
export const sendMessage = (robot, text) => {
  socket.emit('message', { robot, text });
};

// Subscribe to Socket.IO events
export const subscribeToMessages = (callback) => {
  socket.on('message', (data) => {
    callback('message', data);
  });
  
  socket.on('typing', (data) => {
    callback('typing', data);
  });
  
  socket.on('ready', () => {
    callback('ready');
  });
  
  return () => {
    socket.off('message');
    socket.off('typing');
    socket.off('ready');
  };
};

export default {
  getSampleQuestions,
  sendQuestion,
  sendMessage,
  subscribeToMessages,
}; 