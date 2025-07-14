import React, { useState } from 'react';
import ChatBox from './components/ChatBox';
import DocumentUpload from './components/DocumentUpload';
import './styles/App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>RAG System Chat</h1>
        <p>Ask questions about your documents</p>
      </header>
      
      <main className="App-main">
        <div className="chat-container">
          <ChatBox 
            messages={messages}
            onAddMessage={addMessage}
            onClearMessages={clearMessages}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        </div>
        
        <div className="sidebar">
          <DocumentUpload onUploadComplete={() => {
            addMessage({
              type: 'system',
              content: 'Document uploaded successfully!',
              timestamp: new Date()
            });
          }} />
        </div>
      </main>
    </div>
  );
}

export default App; 