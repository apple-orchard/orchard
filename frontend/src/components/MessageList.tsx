import React from 'react';
import Message from './Message';
import { MessageListProps } from '../types';

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  if (messages.length === 0) {
    return (
      <div className="h-full flex justify-center items-center">
        <div className="text-center text-gray-500 text-base p-10">
          <p className="m-0 opacity-80">No messages yet. Start by asking a question about your documents!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 w-full">
      {messages.map((message, index) => (
        <Message key={index} message={message} />
      ))}
    </div>
  );
};

export default MessageList; 