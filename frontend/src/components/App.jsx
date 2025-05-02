import React, { useState, useEffect } from 'react';
import { getSampleQuestions, sendMessage, subscribeToMessages } from '../services/api';
import LeftRobot from './LeftRobot';
import RightRobot from './RightRobot';
import ChatHistory from './ChatHistory';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [isLeftActive, setIsLeftActive] = useState(false);
  const [isRightActive, setIsRightActive] = useState(false);
  const [isRightTyping, setIsRightTyping] = useState(false);
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [autoQuestioningEnabled, setAutoQuestioningEnabled] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState(null);

  // Fetch sample questions on mount and trigger first question
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const questions = await getSampleQuestions();
        setSampleQuestions(questions);
        
        // Automatically set ready state to true to trigger first question
        setTimeout(() => {
          setIsReady(true);
        }, 1000);
      } catch (error) {
        console.error('Error fetching sample questions:', error);
      }
    };
    fetchQuestions();
  }, []);

  // Subscribe to Socket.IO events
  useEffect(() => {
    const unsubscribe = subscribeToMessages((event, data) => {
      switch (event) {
        case 'message':
          // Add message to chat history
          setMessages(prev => [
            {
              id: Date.now().toString(),
              robot: data.robot,
              text: data.text
            },
            ...prev
          ]);
          
          // Update robot states
          if (data.robot === 'left') {
            setIsLeftActive(true);
            setTimeout(() => setIsLeftActive(false), 1000);
            setCurrentQuestion(data.text);
          } else if (data.robot === 'right') {
            setIsRightActive(true);
            setIsRightTyping(false);
            setTimeout(() => setIsRightActive(false), 1000);
            setCurrentQuestion(null);
          }
          break;
          
        case 'typing':
          if (data.robot === 'right') {
            setIsRightTyping(true);
          }
          break;
          
        case 'ready':
          setIsReady(true);
          break;
      }
    });
    
    return () => unsubscribe();
  }, []);

  // Handle auto questioning
  useEffect(() => {
    if (!autoQuestioningEnabled || !isReady || sampleQuestions.length === 0) return;
    
    if (questionIndex < sampleQuestions.length) {
      const askNextQuestion = async () => {
        setIsReady(false);
        
        // Slight delay before asking
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const nextQuestion = sampleQuestions[questionIndex];
        console.log(`Asking question ${questionIndex + 1}/${sampleQuestions.length}: ${nextQuestion}`);
        
        setIsLeftActive(true);
        setTimeout(() => setIsLeftActive(false), 1000);
        
        sendMessage('left', nextQuestion);
        setQuestionIndex(prev => prev + 1);
      };
      
      askNextQuestion();
    } else if (questionIndex >= sampleQuestions.length) {
      console.log('All questions have been asked');
      // Reset after a delay to start over
      setTimeout(() => {
        setQuestionIndex(0);
        setIsReady(true);
      }, 5000);
    }
  }, [isReady, sampleQuestions, questionIndex, autoQuestioningEnabled]);

  // Toggle auto questioning
  const toggleAutoQuestioning = () => {
    setAutoQuestioningEnabled(prev => !prev);
  };

  // Status indicators
  const getStatusText = () => {
    if (isRightTyping) return "Right robot is thinking...";
    if (currentQuestion) return `Processing: ${currentQuestion}`;
    if (questionIndex >= sampleQuestions.length) return "All questions completed";
    return autoQuestioningEnabled ? "Auto-questioning enabled" : "Auto-questioning paused";
  };

  return (
    <div className="retro-container">
      <div className="scanlines"></div>
      <div className="status-bar">
        <span>{getStatusText()}</span>
        <button className="toggle-button" onClick={toggleAutoQuestioning}>
          {autoQuestioningEnabled ? "Pause" : "Resume"}
        </button>
        {questionIndex >= sampleQuestions.length && 
          <button className="reset-button" onClick={() => setQuestionIndex(0)}>
            Restart
          </button>
        }
        <span className="progress-indicator">
          Question: {sampleQuestions.length > 0 ? `${Math.min(questionIndex, sampleQuestions.length)}/${sampleQuestions.length}` : "Loading..."}
        </span>
      </div>
      <LeftRobot isActive={isLeftActive} />
      <ChatHistory 
        messages={messages} 
        isTyping={isRightTyping} 
      />
      <RightRobot isActive={isRightActive} isTyping={isRightTyping} />
    </div>
  );
};

export default App; 