import React, { useState, useRef, useEffect } from 'react';
import { ragAPI, apiUtils } from '../services/api';
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
  const [isLoadingSummary, setIsLoadingSummary] = useState<boolean>(false);
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

  const handleShowDataSummary = async (): Promise<void> => {
    setIsLoadingSummary(true);
    
    try {
      const info = await apiUtils.getKnowledgeBaseInfo();
      
      // Format the summary as a readable message
      const summary = info.data_summary || {};
      const totalChunks = info.total_chunks || 0;
      const totalDocs = summary.total_documents || 0;
      const estimatedSize = summary.estimated_size_mb || 0;
      
      let summaryText = `📊 **Knowledge Base Summary**\n\n`;
      summaryText += `• **Total Chunks**: ${totalChunks.toLocaleString()}\n`;
      summaryText += `• **Estimated Documents**: ${totalDocs.toLocaleString()}\n`;
      summaryText += `• **Estimated Size**: ${estimatedSize} MB\n\n`;
      
      if (summary.file_types && Object.keys(summary.file_types).length > 0) {
        summaryText += `**File Types**:\n`;
        Object.entries(summary.file_types).forEach(([type, count]) => {
          summaryText += `• ${type}: ${(count as number).toLocaleString()} chunks\n`;
        });
        summaryText += `\n`;
      }
      
      if (summary.sources && Object.keys(summary.sources).length > 0) {
        summaryText += `**Sources**:\n`;
        Object.entries(summary.sources).forEach(([source, count]) => {
          summaryText += `• ${source}: ${(count as number).toLocaleString()} chunks\n`;
        });
        summaryText += `\n`;
      }
      
      if (summary.categories && Object.keys(summary.categories).length > 0) {
        summaryText += `**Categories**:\n`;
        Object.entries(summary.categories).forEach(([category, count]) => {
          summaryText += `• ${category}: ${(count as number).toLocaleString()} chunks\n`;
        });
        summaryText += `\n`;
      }
      
      if (summary.recent_ingestions && summary.recent_ingestions.length > 0) {
        summaryText += `**Recent Ingestions**:\n`;
        summary.recent_ingestions.slice(0, 5).forEach((ingestion: any) => {
          const timestamp = new Date(ingestion.timestamp).toLocaleDateString();
          summaryText += `• ${ingestion.source} (${ingestion.file_type}) - ${timestamp}\n`;
        });
      }
      
      // Add the summary as a system message
      const summaryMessage: Message = {
        type: 'system',
        content: summaryText,
        timestamp: new Date(),
        isLoading: false,
      };
      
      onAddMessage(summaryMessage);
      
    } catch (error: any) {
      const errorMessage: Message = {
        type: 'error',
        content: `Error loading data summary: ${error.message}`,
        timestamp: new Date(),
        isLoading: false,
      };
      onAddMessage(errorMessage);
    } finally {
      setIsLoadingSummary(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-5 md:p-6 border-b border-gray-200 flex justify-between items-center bg-gray-50">
        <h3 className="m-0 text-gray-800 text-lg md:text-xl font-semibold">Chat with your documents</h3>
        <div className="flex gap-2">
          <button 
            onClick={handleShowDataSummary}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white border-none px-3 py-2 md:px-4 md:py-2 rounded text-sm md:text-base transition-colors duration-200"
            disabled={isLoading || isLoadingSummary}
          >
            {isLoadingSummary ? 'Loading...' : '📊 Data Summary'}
          </button>
          <button 
            onClick={onClearMessages}
            className="bg-red-500 hover:bg-red-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white border-none px-3 py-2 md:px-4 md:py-2 rounded text-sm md:text-base transition-colors duration-200"
            disabled={isLoading}
          >
            Clear Chat
          </button>
        </div>
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