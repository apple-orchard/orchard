import React, { useState } from 'react';
import { ragAPI } from '../services/api';
import { DocumentUploadProps, FileUploadResponse } from '../types';

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadComplete }) => {
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [dragActive, setDragActive] = useState<boolean>(false);

  const handleFileUpload = async (files: FileList): Promise<void> => {
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);
    setUploadStatus('Uploading...');

    try {
      const result: FileUploadResponse = await ragAPI.uploadFile(file, {
        uploaded_by: 'user',
        upload_time: new Date().toISOString(),
      });

      setUploadStatus(`Success! ${result.chunks_created} chunks created`);
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (error: any) {
      setUploadStatus(`Error: ${error.message}`);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadStatus(''), 5000);
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files);
    }
  };

  return (
    <div className="mb-6">
      <h3 className="mb-4 text-gray-800 text-lg md:text-xl font-semibold">Upload Documents</h3>
      
      <div
        className={`border-2 border-dashed ${dragActive ? 'border-blue-500 bg-blue-50 scale-105' : 'border-gray-300 bg-gray-50 hover:border-blue-500 hover:bg-blue-50'} rounded-lg p-6 md:p-8 text-center transition-all duration-300 cursor-pointer`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept=".pdf,.docx,.doc,.txt"
          onChange={handleChange}
          disabled={isUploading}
          className="hidden"
        />
        <label htmlFor="file-upload" className="block cursor-pointer text-gray-600">
          {isUploading ? (
            <div className="flex flex-col items-center gap-3">
              <span className="text-gray-700">Uploading...</span>
              <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <span className="text-4xl md:text-5xl opacity-60">📁</span>
              <span className="text-base md:text-lg font-medium text-gray-800">
                Drop files here or click to upload
              </span>
              <span className="text-xs md:text-sm text-gray-600 opacity-80">
                Supports PDF, DOCX, DOC, TXT
              </span>
            </div>
          )}
        </label>
      </div>

      {uploadStatus && (
        <div className={`mt-3 px-3 py-2 rounded text-sm md:text-base font-medium text-center ${
          uploadStatus.includes('Error') 
            ? 'bg-red-100 text-red-800 border border-red-200' 
            : 'bg-green-100 text-green-800 border border-green-200'
        }`}>
          {uploadStatus}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload; 