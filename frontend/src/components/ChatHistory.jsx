import React from 'react';

const ChatHistory = ({ messages, isTyping }) => {
  // Format timestamp
  const formatTime = () => {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  };

  return (
    <div className="chat-container">
      <h1 className="app-title">RETRO ROBOT CHAT</h1>
      <div className="chat-messages">
        {isTyping && (
          <div className="typing-indicator robot-right">
            <div className="robot-icon">R2</div>
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div className="message-time">{formatTime()}</div>
          </div>
        )}
        {messages.map((message, index) => (
          <div 
            key={message.id || index} 
            className={`message robot-${message.robot}`}
          >
            <div className="robot-icon">
              {message.robot === 'left' ? 'R1' : 'R2'}
            </div>
            <div className="message-content">
              {message.text}
            </div>
            <div className="message-time">
              {formatTime()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatHistory; 