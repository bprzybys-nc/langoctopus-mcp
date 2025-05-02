import React from 'react';

const RightRobot = ({ isActive, isTyping }) => {
  return (
    <div className={`robot-container right ${isActive ? 'active' : ''}`}>
      <object
        type="image/svg+xml"
        data="/assets/robot-right.svg"
        className="robot"
        aria-label="Right Robot"
        style={{ filter: isActive ? 'brightness(1.2)' : 'brightness(0.8)' }}
      >
        Right Robot
      </object>
      {isTyping && (
        <div className="robot-status terminal-text">PROCESSING...</div>
      )}
    </div>
  );
};

export default RightRobot; 