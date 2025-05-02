import io from 'socket.io-client';

// Get the backend port from environment variables or default to 5001
const DEFAULT_BACKEND_PORT = 5001;
let BACKEND_PORT = process.env.REACT_APP_BACKEND_PORT || DEFAULT_BACKEND_PORT;
let socket = null;
let API_URL = '';

// Function to detect the actual backend port by trying a health check
const detectBackendPort = async () => {
  // Try the specified port first
  const initialPort = BACKEND_PORT;
  console.log(`Trying to connect to backend at port ${initialPort}`);
  
  try {
    const response = await fetch(`http://localhost:${initialPort}/api/health`, { timeout: 2000 });
    if (response.ok) {
      const data = await response.json();
      if (data.port && data.port !== parseInt(initialPort)) {
        console.log(`Backend detected at different port: ${data.port}`);
        return data.port;
      }
      return initialPort;
    }
  } catch (e) {
    console.warn(`Could not connect to backend at port ${initialPort}`);
  }
  
  // If the specified port failed, try a range of ports
  for (let port = initialPort; port < initialPort + 100; port++) {
    if (port === initialPort) continue; // We already tried this one
    
    try {
      console.log(`Trying port ${port}...`);
      const response = await fetch(`http://localhost:${port}/api/health`, { timeout: 1000 });
      if (response.ok) {
        console.log(`Backend detected at port ${port}`);
        return port;
      }
    } catch (e) {
      // Silently continue trying
    }
  }
  
  console.error('Could not detect backend port. Using default.');
  return initialPort;
};

// Initialize the connection
const initializeConnection = async () => {
  try {
    BACKEND_PORT = await detectBackendPort();
    API_URL = process.env.NODE_ENV === 'production' ? '' : `http://localhost:${BACKEND_PORT}`;
    
    console.log(`Connecting to backend at ${API_URL}`);
    
    // Initialize Socket.IO with the detected port
    socket = io(`http://localhost:${BACKEND_PORT}`);
    
    socket.on('connect', () => {
      console.log('Socket.IO connected');
    });
    
    socket.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error);
    });
    
    return true;
  } catch (error) {
    console.error('Error initializing connection:', error);
    return false;
  }
};

// Initialize connection when this module is imported
initializeConnection();

// Get sample questions
export const getSampleQuestions = async () => {
  if (!API_URL) await initializeConnection();
  
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
  if (!API_URL) await initializeConnection();
  
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
  if (!socket) {
    console.error('Socket not initialized');
    return;
  }
  socket.emit('message', { robot, text });
};

// Subscribe to Socket.IO events
export const subscribeToMessages = (callback) => {
  if (!socket) {
    console.error('Socket not initialized');
    setTimeout(() => {
      if (socket) {
        subscribeToMessages(callback);
      }
    }, 1000);
    return () => {};
  }
  
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