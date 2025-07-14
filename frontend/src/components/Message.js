import React from 'react';
import '../styles/Message.css';

const Message = ({ message }) => {
  const { type, content, sources, metadata, timestamp, isLoading } = message;

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`message ${type}`}>
      <div className="message-content">
        <div className="message-text">
          {isLoading ? (
            <div className="loading-indicator">
              <span className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </span>
              {content}
            </div>
          ) : (
            content
          )}
        </div>
        
        {sources && sources.length > 0 && (
          <div className="message-sources">
            <h4>Sources:</h4>
            <ul>
              {sources.map((source, index) => (
                <li key={index}>
                  <strong>{source.filename}</strong>
                  {source.chunk_index !== undefined && (
                    <span className="chunk-info"> (chunk {source.chunk_index})</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {metadata && (
          <div className="message-metadata">
            <span className="chunks-retrieved">
              {metadata.chunks_retrieved} chunks retrieved
            </span>
            {metadata.model && (
              <span className="model-info">
                Model: {metadata.model}
              </span>
            )}
          </div>
        )}
      </div>
      
      <div className="message-timestamp">
        {formatTime(timestamp)}
      </div>
    </div>
  );
};

export default Message; 