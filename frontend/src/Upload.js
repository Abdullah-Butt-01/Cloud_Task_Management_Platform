import React, { useState, useCallback } from 'react';
import axios from 'axios';
import './Upload.css';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Step 20: Handle drag events
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  // Step 20: Handle drop
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  }, []);

  // Step 20: Handle file input change
  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  // Step 20: Validate file type
  const validateAndSetFile = (selectedFile) => {
    const allowedTypes = ['text/plain', 'text/x-log', 'application/octet-stream'];
    const allowedExtensions = ['.txt', '.log'];

    const fileName = selectedFile.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension && !allowedTypes.includes(selectedFile.type)) {
      setError('Only .txt and .log files are allowed');
      setFile(null);
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size must be under 10MB');
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError(null);
    setResult(null);
  };

  // Step 20: Submit upload to API
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data.data);
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Upload failed';
      setError(message);
    } finally {
      setUploading(false);
    }
  };

  // Step 20: Clear file selection
  const handleClear = () => {
    setFile(null);
    setError(null);
    setResult(null);
  };

  return (
    <div className="upload-page">
      <h1>Upload Log File</h1>
      <p className="upload-subtitle">
        Upload .txt or .log files for background processing and analysis.
      </p>

      {/* Step 20: Drag-and-drop zone */}
      <form
        className={`upload-form ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onSubmit={handleSubmit}
      >
        <input
          type="file"
          id="file-input"
          className="file-input"
          accept=".txt,.log"
          onChange={handleChange}
          disabled={uploading}
        />

        <label htmlFor="file-input" className="upload-label">
          {!file ? (
            <div className="upload-prompt">
              <span className="upload-icon">📁</span>
              <p><strong>Click to select</strong> or drag and drop</p>
              <p className="upload-hint">Supported: .txt, .log (max 10MB)</p>
            </div>
          ) : (
            <div className="file-selected">
              <span className="file-icon">📄</span>
              <div className="file-info">
                <p className="file-name">{file.name}</p>
                <p className="file-size">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              {!uploading && (
                <button type="button" className="clear-btn" onClick={handleClear}>
                  ✕
                </button>
              )}
            </div>
          )}
        </label>

        {/* Step 20: Upload button */}
        {file && !result && (
          <button
            type="submit"
            className="upload-btn"
            disabled={uploading}
          >
            {uploading ? (
              <>
                <span className="spinner">⟳</span>
                Uploading...
              </>
            ) : (
              'Upload and Process'
            )}
          </button>
        )}
      </form>

      {/* Step 20: Error display */}
      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Step 20: Success result */}
      {result && (
        <div className="upload-result">
          <div className="alert alert-success">
            <span className="alert-icon">✅</span>
            File uploaded and queued successfully!
          </div>

          <div className="result-card">
            <h3>Job Details</h3>
            <div className="result-grid">
              <div className="result-item">
                <span className="result-label">Job ID</span>
                <span className="result-value">{result.file_job?.file_job_id}</span>
              </div>
              <div className="result-item">
                <span className="result-label">Filename</span>
                <span className="result-value">{result.file_job?.original_filename}</span>
              </div>
              <div className="result-item">
                <span className="result-label">Status</span>
                <span className={`result-value status-${result.file_job?.status}`}>
                  {result.file_job?.status}
                </span>
              </div>
              <div className="result-item">
                <span className="result-label">RQ Job ID</span>
                <span className="result-value mono">{result.file_job?.rq_job_id}</span>
              </div>
            </div>

            <div className="result-actions">
              <a
                href={`/jobs`}
                className="action-btn"
                onClick={(e) => {
                  e.preventDefault();
                  // Navigate to jobs page (will be built in Step 21)
                  window.location.href = '/jobs';
                }}
              >
                View Jobs →
              </a>
            </div>
          </div>

          <button className="upload-another-btn" onClick={handleClear}>
            Upload Another File
          </button>
        </div>
      )}
    </div>
  );
}

export default UploadPage;