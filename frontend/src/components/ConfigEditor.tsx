import React, { useState, useEffect } from 'react';
import { pluginAPI } from '../services/api';
import { FullConfig, GlobalSettings, GitHubRepository } from '../types';

const ConfigEditor: React.FC = () => {
  const [config, setConfig] = useState<FullConfig | null>(null);
  const [editedConfig, setEditedConfig] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'visual' | 'json'>('visual');
  const [expandedPlugin, setExpandedPlugin] = useState<string | null>('github');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await pluginAPI.getFullConfig();
      setConfig(response);
      setEditedConfig(JSON.stringify(response, null, 2));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      setError(null);

      // In visual mode, save the current state
      if (activeTab === 'visual' && config) {
        // Update global settings
        await pluginAPI.updateGlobalSettings(config.global_settings);

        // Update each plugin config
        for (const [pluginName, pluginConfig] of Object.entries(config.plugins || {})) {
          await pluginAPI.updatePluginConfig(pluginName, pluginConfig as any);
        }
      } else {
        // In JSON mode, parse and save
        const parsed = JSON.parse(editedConfig);

        // Update global settings
        if (parsed.global_settings) {
          await pluginAPI.updateGlobalSettings(parsed.global_settings);
        }

        // Update each plugin config
        for (const [pluginName, pluginConfig] of Object.entries(parsed.plugins || {})) {
          await pluginAPI.updatePluginConfig(pluginName, pluginConfig as any);
        }
      }

      // Reload to get the saved config
      await loadConfig();
      setError(null);
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format');
      } else {
        setError(`Failed to save: ${err.message}`);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleAddRepository = () => {
    if (!config) return;

    const newRepo: GitHubRepository = {
      id: `repo-${Date.now()}`,
      owner: '',
      repo: '',
      branch: 'main',
      paths: [],
      exclude_patterns: [],
      sync_mode: 'full'
    };

    const githubConfig = config.plugins.github?.config || { repositories: [] };
    const repositories = [...((githubConfig as any).repositories || []), newRepo];

    setConfig({
      ...config,
      plugins: {
        ...config.plugins,
        github: {
          ...config.plugins.github,
          config: {
            ...githubConfig,
            repositories
          }
        }
      }
    });
  };

  const handleUpdateRepository = (index: number, field: string, value: any) => {
    if (!config) return;

    const githubConfig = config.plugins.github?.config || { repositories: [] };
    const repositories = [...((githubConfig as any).repositories || [])];
    repositories[index] = { ...repositories[index], [field]: value };

    setConfig({
      ...config,
      plugins: {
        ...config.plugins,
        github: {
          ...config.plugins.github,
          config: {
            ...githubConfig,
            repositories
          }
        }
      }
    });
  };

  const handleRemoveRepository = (index: number) => {
    if (!config) return;

    const githubConfig = config.plugins.github?.config || { repositories: [] };
    const repositories = ((githubConfig as any).repositories || []).filter((_: any, i: number) => i !== index);

    setConfig({
      ...config,
      plugins: {
        ...config.plugins,
        github: {
          ...config.plugins.github,
          config: {
            ...githubConfig,
            repositories
          }
        }
      }
    });
  };

  const handleTogglePlugin = (pluginName: string, enabled: boolean) => {
    if (!config) return;

    setConfig({
      ...config,
      plugins: {
        ...config.plugins,
        [pluginName]: {
          ...config.plugins[pluginName],
          enabled
        }
      }
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!config) {
    return <div>No configuration loaded</div>;
  }

  const githubRepos = (config.plugins.github?.config as any)?.repositories || [];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Configuration Editor</h2>
        <button
          onClick={loadConfig}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Tab switcher */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('visual')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'visual'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Visual Editor
          </button>
          <button
            onClick={() => {
              setActiveTab('json');
              // Update JSON when switching to JSON tab
              setEditedConfig(JSON.stringify(config, null, 2));
            }}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'json'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            JSON Editor
          </button>
        </nav>
      </div>

      {activeTab === 'visual' ? (
        <div className="space-y-6">
          {/* Plugin Configurations */}
          <div className="space-y-4">
            {/* GitHub Plugin */}
            <div className="bg-white rounded-lg border border-gray-200">
              <button
                onClick={() => setExpandedPlugin(expandedPlugin === 'github' ? null : 'github')}
                className="w-full px-6 py-4 flex justify-between items-center hover:bg-gray-50"
              >
                <div className="flex items-center space-x-3">
                  <h3 className="text-lg font-semibold">GitHub Plugin</h3>
                  <label className="flex items-center space-x-2" onClick={e => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={config.plugins.github?.enabled || false}
                      onChange={(e) => handleTogglePlugin('github', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600">Enabled</span>
                  </label>
                </div>
                <svg
                  className={`w-5 h-5 transform transition-transform ${expandedPlugin === 'github' ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {expandedPlugin === 'github' && (
                <div className="px-6 pb-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium">Repositories</h4>
                    <button
                      onClick={handleAddRepository}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      Add Repository
                    </button>
                  </div>

                  {githubRepos.length === 0 ? (
                    <p className="text-gray-500 text-sm">No repositories configured. Click "Add Repository" to get started.</p>
                  ) : (
                    <div className="space-y-4">
                      {githubRepos.map((repo: any, index: number) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-3">
                          <div className="flex justify-between items-start">
                            <h5 className="font-medium">Repository {index + 1}</h5>
                            <button
                              onClick={() => handleRemoveRepository(index)}
                              className="text-red-600 hover:text-red-800 text-sm"
                            >
                              Remove
                            </button>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Repository ID
                              </label>
                              <input
                                type="text"
                                value={repo.id || ''}
                                onChange={(e) => handleUpdateRepository(index, 'id', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="unique-id"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Owner
                              </label>
                              <input
                                type="text"
                                value={repo.owner || ''}
                                onChange={(e) => handleUpdateRepository(index, 'owner', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="username or org"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Repository Name
                              </label>
                              <input
                                type="text"
                                value={repo.repo || ''}
                                onChange={(e) => handleUpdateRepository(index, 'repo', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="repository-name"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Branch
                              </label>
                              <input
                                type="text"
                                value={repo.branch || 'main'}
                                onChange={(e) => handleUpdateRepository(index, 'branch', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="main"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Sync Mode
                              </label>
                              <select
                                value={repo.sync_mode || 'full'}
                                onChange={(e) => handleUpdateRepository(index, 'sync_mode', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              >
                                <option value="full">Full</option>
                                <option value="incremental">Incremental</option>
                              </select>
                            </div>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Paths (comma separated, optional)
                            </label>
                            <input
                              type="text"
                              value={(repo.paths || []).join(', ')}
                              onChange={(e) => {
                                const paths = e.target.value.split(',').map(p => p.trim()).filter(p => p);
                                handleUpdateRepository(index, 'paths', paths);
                              }}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder="src/, docs/, README.md"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Exclude Patterns (comma separated)
                            </label>
                            <input
                              type="text"
                              value={(repo.exclude_patterns || []).join(', ')}
                              onChange={(e) => {
                                const patterns = e.target.value.split(',').map(p => p.trim()).filter(p => p);
                                handleUpdateRepository(index, 'exclude_patterns', patterns);
                              }}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder="*.pyc, __pycache__/, *.test.py"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      GitHub Token
                    </label>
                    <input
                      type="text"
                      value={config.plugins.github?.config?.github_token || ''}
                      onChange={(e) => {
                        const githubConfig = config.plugins.github?.config || {};
                        setConfig({
                          ...config,
                          plugins: {
                            ...config.plugins,
                            github: {
                              ...config.plugins.github,
                              config: {
                                ...githubConfig,
                                github_token: e.target.value
                              }
                            }
                          }
                        });
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      placeholder="${GITHUB_TOKEN}"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Use {'${GITHUB_TOKEN}'} to reference environment variable
                    </p>
                    {config.plugins.github?.config?.github_token &&
                     !config.plugins.github.config.github_token.startsWith('${') && (
                      <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                        <p className="text-xs text-yellow-800">
                          <strong>Security Warning:</strong> It looks like you've entered your token directly.
                          For security, use <code className="bg-yellow-100 px-1 rounded">${'{GITHUB_TOKEN}'}</code> and
                          set the token in your .env file instead.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Global Settings */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Global Settings</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Chunk Size
                </label>
                <input
                  type="number"
                  value={config.global_settings.chunk_size}
                  onChange={(e) => {
                    const newSettings = { ...config.global_settings, chunk_size: parseInt(e.target.value) || 1024 };
                    setConfig({ ...config, global_settings: newSettings });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="128"
                  max="4096"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Chunk Overlap
                </label>
                <input
                  type="number"
                  value={config.global_settings.chunk_overlap}
                  onChange={(e) => {
                    const newSettings = { ...config.global_settings, chunk_overlap: parseInt(e.target.value) || 200 };
                    setConfig({ ...config, global_settings: newSettings });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="1024"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Batch Size
                </label>
                <input
                  type="number"
                  value={config.global_settings.batch_size}
                  onChange={(e) => {
                    const newSettings = { ...config.global_settings, batch_size: parseInt(e.target.value) || 100 };
                    setConfig({ ...config, global_settings: newSettings });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="1000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sync Interval (hours)
                </label>
                <input
                  type="number"
                  value={config.global_settings.sync_interval_hours}
                  onChange={(e) => {
                    const newSettings = { ...config.global_settings, sync_interval_hours: parseInt(e.target.value) || 24 };
                    setConfig({ ...config, global_settings: newSettings });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="168"
                />
              </div>

              <div className="md:col-span-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.global_settings.auto_sync}
                    onChange={(e) => {
                      const newSettings = { ...config.global_settings, auto_sync: e.target.checked };
                      setConfig({ ...config, global_settings: newSettings });
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Enable Auto Sync
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-2">
              Edit the configuration JSON below. This directly represents your rag_config.yaml file.
            </p>
            <textarea
              value={editedConfig}
              onChange={(e) => setEditedConfig(e.target.value)}
              className="w-full h-96 px-4 py-3 font-mono text-sm bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              spellCheck={false}
            />
          </div>
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          onClick={loadConfig}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          Cancel
        </button>
        <button
          onClick={handleSaveConfig}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
};

export default ConfigEditor;