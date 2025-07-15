import React from 'react';
import { MessageProps } from '../types';

const Message: React.FC<MessageProps> = ({ message }) => {
  const { type, content, sources, metadata, timestamp, isLoading } = message;

  const formatTime = (date: Date): string => {
    return new Date(date).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getMessageStyles = (): string => {
    const baseStyles = "flex flex-col max-w-[80%] md:max-w-[90%] mb-4";
    
    switch (type) {
      case 'user':
        return `${baseStyles} self-end`;
      case 'assistant':
        return `${baseStyles} self-start`;
      case 'system':
        return `${baseStyles} self-center`;
      case 'error':
        return `${baseStyles} self-start`;
      default:
        return baseStyles;
    }
  };

  const getContentStyles = (): string => {
    const baseStyles = "px-3 py-2 md:px-4 md:py-3 border border-gray-200 shadow-sm";
    
    switch (type) {
      case 'user':
        return `${baseStyles} bg-blue-500 text-white rounded-2xl rounded-br-sm border-blue-500`;
      case 'assistant':
        return `${baseStyles} bg-gray-50 text-gray-800 rounded-2xl rounded-bl-sm`;
      case 'system':
        return `${baseStyles} bg-green-500 text-white rounded-2xl border-green-500 italic`;
      case 'error':
        return `${baseStyles} bg-red-500 text-white rounded-2xl rounded-bl-sm border-red-500`;
      default:
        return `${baseStyles} bg-gray-50 text-gray-800 rounded-2xl`;
    }
  };

  const getTimestampStyles = (): string => {
    const baseStyles = "text-xs md:text-xs mt-1";
    
    switch (type) {
      case 'user':
        return `${baseStyles} text-right text-white/80`;
      default:
        return `${baseStyles} text-right text-gray-500`;
    }
  };

  return (
    <div className={getMessageStyles()}>
      <div className={getContentStyles()}>
        <div className="text-sm md:text-sm leading-relaxed break-words whitespace-pre-wrap">
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-1 h-1 rounded-full bg-current animate-pulse" style={{ animationDelay: '-0.32s' }}></span>
                <span className="w-1 h-1 rounded-full bg-current animate-pulse" style={{ animationDelay: '-0.16s' }}></span>
                <span className="w-1 h-1 rounded-full bg-current animate-pulse"></span>
              </div>
              <div className="w-full text-wrap px-2">{content}</div>
            </div>
          ) : (
            content
          )}
        </div>
        
        {sources && sources.length > 0 && (
          <div className={`mt-3 pt-3 ${type === 'assistant' ? 'border-t border-gray-200' : 'border-t border-white/20'}`}>
            <h4 className="text-xs font-semibold mb-2 opacity-90">Sources:</h4>
            <ul className="list-none p-0 m-0">
              {sources.map((source, index) => (
                <li key={index} className="text-xs mb-1 opacity-90">
                  <strong>{source.filename}</strong>
                  {source.chunk_index !== undefined && (
                    <span className="font-normal opacity-70"> (chunk {source.chunk_index})</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {metadata && (
          <div className={`mt-2 pt-2 ${type === 'assistant' ? 'border-t border-gray-200' : 'border-t border-white/20'} text-xs opacity-80 flex gap-3 flex-wrap`}>
            <span>
              {metadata.chunks_retrieved} chunks retrieved
            </span>
            {metadata.model && (
              <span>
                Model: {metadata.model}
              </span>
            )}
          </div>
        )}
      </div>
      
      <div className={getTimestampStyles()}>
        {formatTime(timestamp)}
      </div>
    </div>
  );
};

export default Message; 