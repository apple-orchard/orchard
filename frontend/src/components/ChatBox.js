import React, { useState, useRef, useEffect } from 'react';
import { ragAPI } from '../services/api';
import MessageList from './MessageList';
import InputForm from './InputForm';
import '../styles/ChatBox.css';

const ChatBox = ({ messages, onAddMessage, onClearMessages, isLoading, setIsLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message) => {
    if (!message.trim()) return;

    // Add user message
    const userMessage = {
      type: 'user',
      content: message,
      timestamp: new Date(),
    };
    onAddMessage(userMessage);

    setIsLoading(true);

    try {
      const response = await ragAPI.query(message);
      
      // Add assistant response
      const assistantMessage = {
        type: 'assistant',
        content: response.answer,
        sources: response.sources,
        metadata: response.metadata,
        timestamp: new Date(),
        isLoading: false,
      };

      onAddMessage(assistantMessage);
      
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
        isLoading: false,
      };
      onAddMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-box">
      <div className="chat-header">
        <h3>Chat with your documents</h3>
        <button 
          onClick={onClearMessages}
          className="clear-button"
          disabled={isLoading}
        >
          Clear Chat
        </button>
      </div>
      
      <div className="chat-messages">
        <MessageList messages={messages} />
        {isLoading && (
          <div className="loading-message">
            <div className="loading-indicator">
              <span className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </span>
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <InputForm
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSendMessage}
        isLoading={isLoading}
        placeholder="Ask a question about your documents..."
      />
    </div>
  );
};

export default ChatBox; 