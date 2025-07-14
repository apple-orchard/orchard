import React, { useState } from 'react';
import { ragAPI } from '../services/api';
import '../styles/DocumentUpload.css';

const DocumentUpload = ({ onUploadComplete }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);
    setUploadStatus('Uploading...');

    try {
      const result = await ragAPI.uploadFile(file, {
        uploaded_by: 'user',
        upload_time: new Date().toISOString(),
      });

      setUploadStatus(`Success! ${result.chunks_created} chunks created`);
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (error) {
      setUploadStatus(`Error: ${error.message}`);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadStatus(''), 5000);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files);
    }
  };

  return (
    <div className="document-upload">
      <h3>Upload Documents</h3>
      
      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''}`}
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
          className="file-input"
        />
        <label htmlFor="file-upload" className="file-label">
          {isUploading ? (
            <div className="upload-progress">
              <span>Uploading...</span>
              <div className="spinner"></div>
            </div>
          ) : (
            <div className="upload-content">
              <span className="upload-icon">📁</span>
              <span className="upload-text">
                Drop files here or click to upload
              </span>
              <span className="upload-hint">
                Supports PDF, DOCX, DOC, TXT
              </span>
            </div>
          )}
        </label>
      </div>

      {uploadStatus && (
        <div className={`upload-status ${uploadStatus.includes('Error') ? 'error' : 'success'}`}>
          {uploadStatus}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload; 