import React, { useState, useEffect } from 'react';
import { apiUtils } from '../services/api';

interface PromptEditorProps {
  className?: string;
}

const PromptEditor: React.FC<PromptEditorProps> = ({ className = '' }) => {
  const [systemPrompt, setSystemPrompt] = useState<string>('');
  const [originalPrompt, setOriginalPrompt] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  useEffect(() => {
    loadSystemPrompt();
  }, []);

  const loadSystemPrompt = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiUtils.getSystemPrompt();
      setSystemPrompt(response.system_prompt);
      setOriginalPrompt(response.system_prompt);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      await apiUtils.updateSystemPrompt(systemPrompt);
      setOriginalPrompt(systemPrompt);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setSystemPrompt(originalPrompt);
    setError(null);
    setSuccess(false);
  };

  const hasChanges = systemPrompt !== originalPrompt;

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-lg p-4 md:p-5 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-4 md:p-5 ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">System Prompt</h3>
        <p className="text-sm text-gray-600">
          Configure the system prompt used for RAG queries. Use {'{context}'} and {'{question}'} as placeholders.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm">
          System prompt updated successfully!
        </div>
      )}

      <div className="mb-4">
        <textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          className="w-full h-64 p-3 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter your system prompt..."
          disabled={saving}
        />
      </div>

      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-500">
          {hasChanges && <span className="text-orange-600">• Unsaved changes</span>}
        </div>
        <div className="space-x-2">
          <button
            onClick={handleReset}
            disabled={!hasChanges || saving}
            className="px-4 py-2 text-sm text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PromptEditor; 