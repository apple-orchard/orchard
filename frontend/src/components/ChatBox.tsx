import React, { useState, useRef, useEffect } from 'react';
import { ragAPI } from '../services/api';
import MessageList from './MessageList';
import InputForm from './InputForm';
import { ChatBoxProps, Message } from '../types';

const ChatBox: React.FC<ChatBoxProps> = ({ 
  messages, 
  onAddMessage, 
  onClearMessages, 
  isLoading, 
  setIsLoading 
}) => {
  const [inputValue, setInputValue] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message: string): Promise<void> => {
    if (!message.trim()) return;

    // Add user message
    const userMessage: Message = {
      type: 'user',
      content: message,
      timestamp: new Date(),
    };
    onAddMessage(userMessage);

    setIsLoading(true);

    try {
      const response = await ragAPI.query(message);
      
      // Add assistant response
      const assistantMessage: Message = {
        type: 'assistant',
        content: response.answer,
        sources: response.sources,
        metadata: response.metadata,
        timestamp: new Date(),
        isLoading: false,
      };

      onAddMessage(assistantMessage);
      
    } catch (error: any) {
      const errorMessage: Message = {
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

  const handleInputChange = (value: string): void => {
    setInputValue(value);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-5 md:p-6 border-b border-gray-200 flex justify-between items-center bg-gray-50">
        <h3 className="m-0 text-gray-800 text-lg md:text-xl font-semibold">Chat with your documents</h3>
        <button 
          onClick={onClearMessages}
          className="bg-red-500 hover:bg-red-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white border-none px-3 py-2 md:px-4 md:py-2 rounded text-sm md:text-base transition-colors duration-200"
          disabled={isLoading}
        >
          Clear Chat
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 md:p-5 flex flex-col gap-4 custom-scrollbar">
        <MessageList messages={messages} />
        {isLoading && (
          <div className="flex self-start max-w-[80%] md:max-w-[90%] mb-4">
            <div className="bg-gray-50 text-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-200 shadow-sm flex items-center gap-2 text-sm">
              <div className="flex gap-1">
                <span className="w-1 h-1 rounded-full bg-gray-600 animate-pulse" style={{ animationDelay: '-0.32s' }}></span>
                <span className="w-1 h-1 rounded-full bg-gray-600 animate-pulse" style={{ animationDelay: '-0.16s' }}></span>
                <span className="w-1 h-1 rounded-full bg-gray-600 animate-pulse"></span>
              </div>
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <InputForm
        value={inputValue}
        onChange={handleInputChange}
        onSend={handleSendMessage}
        isLoading={isLoading}
        placeholder="Ask a question about your documents..."
      />
    </div>
  );
};

export default ChatBox; 