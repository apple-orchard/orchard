import React, { useState } from 'react';
import ChatBox from './components/ChatBox';
import DocumentUpload from './components/DocumentUpload';
import PluginDashboard from './components/PluginDashboard';
import JobManager from './components/JobManager';
import { Message, FileUploadResponse } from './types';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeView, setActiveView] = useState<'chat' | 'plugins' | 'jobs'>('chat');

  const addMessage = (message: Message): void => {
    setMessages(prev => [...prev, message]);
  };

  const updateMessage = (message: Message): void => {
    setMessages(prev => prev.map(m => m.timestamp === message.timestamp ? message : m));
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
    <div className="h-screen flex flex-col bg-gray-100">
      <header className="sticky top-0 z-10 bg-gray-800 text-white shadow-lg">
        <div className="max-w-6xl mx-auto p-4 md:p-5">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-xl md:text-2xl font-bold">Orchard RAG System</h1>
              <p className="text-sm md:text-base opacity-90">Knowledge Base & Query System</p>
            </div>
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveView('chat')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  activeView === 'chat'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setActiveView('plugins')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  activeView === 'plugins'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Plugins
              </button>
              <button
                onClick={() => setActiveView('jobs')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  activeView === 'jobs'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Jobs
              </button>
            </nav>
          </div>
        </div>
      </header>

      {activeView === 'chat' ? (
        <main className="flex-1 flex flex-col md:flex-row gap-4 md:gap-5 p-4 md:p-5 max-w-6xl mx-auto w-full min-h-0">
          <div className="order-2 md:order-1 flex-1 bg-white rounded-lg shadow-lg overflow-hidden flex flex-col min-h-0">
            <ChatBox
              messages={messages}
              onAddMessage={addMessage}
              onUpdateMessage={updateMessage}
              onClearMessages={clearMessages}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
            />
          </div>

          <div className="order-1 md:order-2 w-full md:w-80 bg-white rounded-lg shadow-lg p-4 md:p-5 h-fit max-h-full overflow-y-auto">
            <DocumentUpload onUploadComplete={handleUploadComplete} />
          </div>
        </main>
      ) : activeView === 'plugins' ? (
        <main className="flex-1 min-h-0">
          <PluginDashboard />
        </main>
      ) : (
        <main className="flex-1 min-h-0 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-4 md:p-5">
            <JobManager />
          </div>
        </main>
      )}
    </div>
  );
};

export default App;