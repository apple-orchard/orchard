import React from 'react';
import Message from './Message';
import '../styles/MessageList.css';

const MessageList = ({ messages }) => {
  if (messages.length === 0) {
    return (
      <div className="message-list empty">
        <div className="empty-state">
          <p>No messages yet. Start by asking a question about your documents!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <Message key={index} message={message} />
      ))}
    </div>
  );
};

export default MessageList; 