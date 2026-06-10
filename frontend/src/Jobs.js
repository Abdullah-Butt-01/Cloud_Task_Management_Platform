import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Jobs.css';

function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');

  // Step 21: Fetch jobs with optional status filter
  const fetchJobs = async () => {
    try {
      const url = filter === 'all' ? '/files' : `/files?status=${filter}`;
      const response = await axios.get(url);
      setJobs(response.data.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    // Step 21: Auto-refresh every 5 seconds
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [filter]);

  // Step 21: Sort handler
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Step 21: Sort jobs
  const sortedJobs = [...jobs].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];

    // Handle null values
    if (aVal === null || aVal === undefined) aVal = '';
    if (bVal === null || bVal === undefined) bVal = '';

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Step 21: Status badge helper
  const getStatusClass = (status) => {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'processing': return 'status-processing';
      case 'queued': return 'status-queued';
      case 'failed': return 'status-failed';
      default: return 'status-default';
    }
  };

  // Step 21: Format date helper
  const formatDate = (isoString) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString();
  };

  // Step 21: Format duration helper
  const formatDuration = (seconds) => {
    if (!seconds) return '-';
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  if (loading) {
    return (
      <div className="jobs-page">
        <div className="loading">Loading jobs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="jobs-page">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="jobs-page">
      <div className="jobs-header">
        <h1>Processing Jobs</h1>
        <div className="jobs-controls">
          {/* Step 21: Status filter */}
          <div className="filter-group">
            <label>Filter:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Status</option>
              <option value="queued">Queued</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <div className="jobs-count">
            {jobs.length} job{jobs.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Step 21: Jobs table */}
      <div className="table-container">
        <table className="jobs-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('file_job_id')} className="sortable">
                ID {sortField === 'file_job_id' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('original_filename')} className="sortable">
                Filename {sortField === 'original_filename' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('status')} className="sortable">
                Status {sortField === 'status' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('line_count')} className="sortable right">
                Lines {sortField === 'line_count' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('status_200_count')} className="sortable right">
                200 {sortField === 'status_200_count' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('total_error_count')} className="sortable right">
                Errors {sortField === 'total_error_count' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('unique_client_count')} className="sortable right">
                Clients {sortField === 'unique_client_count' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('processing_time')} className="sortable right">
                Duration {sortField === 'processing_time' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('created_at')} className="sortable">
                Created {sortField === 'created_at' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedJobs.length === 0 ? (
              <tr>
                <td colSpan="10" className="no-jobs">
                  No jobs found. <a href="/upload">Upload a file</a> to get started.
                </td>
              </tr>
            ) : (
              sortedJobs.map((job) => (
                <tr key={job.file_job_id} className={`job-row status-${job.status}`}>
                  <td className="job-id">{job.file_job_id}</td>
                  <td className="job-filename" title={job.original_filename}>
                    {job.original_filename}
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusClass(job.status)}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="right">{job.line_count ?? '-'}</td>
                  <td className="right">{job.status_200_count ?? '-'}</td>
                  <td className="right">
                    {job.total_error_count > 0 ? (
                      <span className="error-count">{job.total_error_count}</span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="right">{job.unique_client_count ?? '-'}</td>
                  <td className="right">{formatDuration(job.processing_time)}</td>
                  <td className="job-date">{formatDate(job.created_at)}</td>
                  <td>
                    <a
                      href={`/insights/${job.file_job_id}`}
                      className="action-link"
                      onClick={(e) => {
                        e.preventDefault();
                        // Will navigate to insight detail when built
                        alert(`Insight for job ${job.file_job_id} — coming in Step 22`);
                      }}
                    >
                      View
                    </a>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Step 21: Auto-refresh indicator */}
      <div className="refresh-indicator">
        <span className="refresh-dot"></span>
        Auto-refreshing every 5 seconds
      </div>
    </div>
  );
}

export default JobsPage;