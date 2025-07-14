import React, { useState } from 'react';
import ChatBox from './components/ChatBox';
import DocumentUpload from './components/DocumentUpload';
import { Message, FileUploadResponse } from './types';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const addMessage = (message: Message): void => {
    setMessages(prev => [...prev, message]);
  };

  const clearMessages = (): void => {
    setMessages([]);
  };

  const handleUploadComplete = (result: FileUploadResponse): void => {
    addMessage({
      type: 'system',
      content: 'Document uploaded successfully!',
      timestamp: new Date()
    });
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-800 text-white p-4 md:p-5 text-center shadow-lg">
        <h1 className="text-xl md:text-2xl font-bold mb-2">RAG System Chat</h1>
        <p className="text-sm md:text-base opacity-90 m-0">Ask questions about your documents</p>
      </header>
      
      <main className="flex-1 flex flex-col md:flex-row gap-4 md:gap-5 p-4 md:p-5 max-w-6xl mx-auto w-full">
        <div className="order-2 md:order-1 flex-1 bg-white rounded-lg shadow-lg overflow-hidden flex flex-col min-h-[500px] md:min-h-[600px]">
          <ChatBox 
            messages={messages}
            onAddMessage={addMessage}
            onClearMessages={clearMessages}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        </div>
        
        <div className="order-1 md:order-2 w-full md:w-80 bg-white rounded-lg shadow-lg p-4 md:p-5 h-fit">
          <DocumentUpload onUploadComplete={handleUploadComplete} />
        </div>
      </main>
    </div>
  );
};

export default App; 