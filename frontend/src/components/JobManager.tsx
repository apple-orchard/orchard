import React, { useState, useEffect } from 'react';
import { jobAPI } from '../services/api';
import { JobInfo, JobListResponse, JobStatsResponse, JobManagerProps } from '../types';

const JobManager: React.FC<JobManagerProps> = ({ className = '' }) => {
  const [jobs, setJobs] = useState<JobInfo[]>([]);
  const [stats, setStats] = useState<JobStatsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const fetchJobs = async () => {
    try {
      const jobList: JobListResponse = await jobAPI.listJobs(selectedStatus || undefined, 100);
      setJobs(jobList.jobs);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fetchStats = async () => {
    try {
      const jobStats: JobStatsResponse = await jobAPI.getJobStats();
      setStats(jobStats);
    } catch (err: any) {
      console.error('Failed to fetch job stats:', err.message);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to cancel this job?')) {
      return;
    }

    try {
      await jobAPI.cancelJob(jobId);
      await fetchJobs(); // Refresh the job list
    } catch (err: any) {
      setError(err.message);
    }
  };

  const formatDuration = (startTime: string, endTime?: string): string => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 60) return `${diffSecs}s`;
    if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ${diffSecs % 60}s`;
    return `${Math.floor(diffSecs / 3600)}h ${Math.floor((diffSecs % 3600) / 60)}m`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'completed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'cancelled': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getJobTypeIcon = (jobType: string): string => {
    switch (jobType) {
      case 'text_ingestion': return '📝';
      case 'file_ingestion': return '📄';
      case 'directory_ingestion': return '📁';
      case 'batch_ingestion': return '📦';
      default: return '⚙️';
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchJobs(), fetchStats()]);
      setLoading(false);
    };

    loadData();
  }, [selectedStatus]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchJobs();
      fetchStats();
    }, 2000); // Refresh every 2 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, selectedStatus]);

  if (loading) {
    return (
      <div className={`${className} p-6`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-600">Loading jobs...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className} p-6 bg-white rounded-lg shadow-lg`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Job Manager</h2>
        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-600">Auto-refresh</span>
          </label>
          <button
            onClick={() => { fetchJobs(); fetchStats(); }}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          Error: {error}
        </div>
      )}

      {/* Job Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">Total Jobs</div>
            <div className="text-xl font-bold text-gray-800">{stats.total_jobs}</div>
          </div>
          <div className="bg-yellow-50 p-3 rounded">
            <div className="text-sm text-yellow-600">Pending</div>
            <div className="text-xl font-bold text-yellow-800">{stats.pending}</div>
          </div>
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-blue-600">Running</div>
            <div className="text-xl font-bold text-blue-800">{stats.running}</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-green-600">Completed</div>
            <div className="text-xl font-bold text-green-800">{stats.completed}</div>
          </div>
          <div className="bg-red-50 p-3 rounded">
            <div className="text-sm text-red-600">Failed</div>
            <div className="text-xl font-bold text-red-800">{stats.failed}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">Cancelled</div>
            <div className="text-xl font-bold text-gray-800">{stats.cancelled}</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-purple-600">Total Chunks</div>
            <div className="text-xl font-bold text-purple-800">{stats.total_chunks_created.toLocaleString()}</div>
          </div>
        </div>
      )}

      {/* Status Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Status:
        </label>
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All Jobs</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {jobs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No jobs found {selectedStatus && `with status "${selectedStatus}"`}
          </div>
        ) : (
          jobs.map((job) => (
            <div key={job.job_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getJobTypeIcon(job.job_type)}</span>
                  <div>
                    <div className="font-medium text-gray-900">
                      {job.job_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                    <div className="text-sm text-gray-500">ID: {job.job_id.slice(0, 8)}...</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                    {job.status.toUpperCase()}
                  </span>
                  {job.status === 'pending' && (
                    <button
                      onClick={() => handleCancelJob(job.job_id)}
                      className="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>

              {/* Progress Bar for Running Jobs */}
              {job.status === 'running' && (
                <div className="mb-2">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{Math.round(job.progress * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Job Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Created:</span>
                  <div className="font-medium">{new Date(job.created_at).toLocaleString()}</div>
                </div>
                {job.started_at && (
                  <div>
                    <span className="text-gray-600">Duration:</span>
                    <div className="font-medium">{formatDuration(job.started_at, job.completed_at)}</div>
                  </div>
                )}
                <div>
                  <span className="text-gray-600">Progress:</span>
                  <div className="font-medium">{job.processed_items}/{job.total_items} items</div>
                </div>
                {job.status === 'completed' && (
                  <div>
                    <span className="text-gray-600">Chunks Created:</span>
                    <div className="font-medium text-green-600">{job.chunks_created}</div>
                  </div>
                )}
              </div>

              {/* Job Message */}
              <div className="mt-3 p-2 bg-gray-50 rounded text-sm">
                <span className="text-gray-600">Status: </span>
                <span className="text-gray-800">{job.message}</span>
              </div>

              {/* Error Message */}
              {job.error_message && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm">
                  <span className="text-red-600 font-medium">Error: </span>
                  <span className="text-red-800">{job.error_message}</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default JobManager;