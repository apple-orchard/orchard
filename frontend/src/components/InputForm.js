import React, { useState } from 'react';
import '../styles/InputForm.css';

const InputForm = ({ value, onChange, onSend, isLoading, placeholder }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSend(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="input-form" onSubmit={handleSubmit}>
      <div className="input-container">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={isLoading}
          rows="1"
          className="message-input"
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className="send-button"
        >
          {isLoading ? (
            <span className="loading-spinner">⏳</span>
          ) : (
            <span>Send</span>
          )}
        </button>
      </div>
    </form>
  );
};

export default InputForm; 