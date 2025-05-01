import React from 'react';

const LeftRobot = ({ isActive }) => {
  return (
    <div className={`robot-container left ${isActive ? 'active' : ''}`}>
      <object
        type="image/svg+xml"
        data="/assets/robot-left.svg"
        className="robot"
        aria-label="Left Robot"
        style={{ filter: isActive ? 'brightness(1.2)' : 'brightness(0.8)' }}
      >
        Left Robot
      </object>
      {isActive && (
        <div className="robot-status terminal-text">SENDING...</div>
      )}
    </div>
  );
};

export default LeftRobot; 