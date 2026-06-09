import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';

// Step 19: Dashboard page with system overview cards
// Fetches /metrics, /health, /queue/status and displays summary cards

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);
  const [queue, setQueue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Step 19: Fetch all overview endpoints in parallel
    const fetchData = async () => {
      try {
        setLoading(true);
        const [metricsRes, healthRes, queueRes] = await Promise.all([
          axios.get('/metrics').catch(() => ({ data: { data: null } })),
          axios.get('/health').catch(() => ({ data: { data: null } })),
          axios.get('/queue/status').catch(() => ({ data: { data: null } })),
        ]);

        setMetrics(metricsRes.data.data);
        setHealth(healthRes.data.data);
        setQueue(queueRes.data.data);
        setError(null);
      } catch (err) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Step 19: Auto-refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h1>System Dashboard</h1>
      <p className="last-updated">
        Last updated: {new Date().toLocaleTimeString()}
      </p>

      {/* Step 19: Health status banner */}
      {health && (
        <div className={`health-banner health-${health.status}`}>
          <span className="health-label">System Status:</span>
          <span className="health-value">{health.status.toUpperCase()}</span>
          {health.services && (
            <span className="health-detail">
              DB: {health.services.database?.status} | 
              Redis: {health.services.redis?.status} | 
              Workers: {health.services.workers?.active_workers || 0}/{health.services.workers?.total_workers || 0}
            </span>
          )}
        </div>
      )}

      {/* Step 19: Metrics cards grid */}
      <div className="cards-grid">
        {/* Jobs Card */}
        {metrics?.jobs && (
          <div className="card card-jobs">
            <div className="card-header">
              <h3>Jobs</h3>
              <span className="card-icon">📁</span>
            </div>
            <div className="card-body">
              <div className="metric-row">
                <span className="metric-label">Total</span>
                <span className="metric-value">{metrics.jobs.total}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Completed</span>
                <span className="metric-value success">{metrics.jobs.completed}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Failed</span>
                <span className="metric-value danger">{metrics.jobs.failed}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Success Rate</span>
                <span className={`metric-value ${metrics.jobs.success_rate >= 90 ? 'success' : metrics.jobs.success_rate >= 70 ? 'warning' : 'danger'}`}>
                  {metrics.jobs.success_rate}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Queue Card */}
        {queue && (
          <div className="card card-queue">
            <div className="card-header">
              <h3>Queue</h3>
              <span className="card-icon">📬</span>
            </div>
            <div className="card-body">
              <div className="metric-row">
                <span className="metric-label">Pending</span>
                <span className={`metric-value ${queue.rq_queue?.pending_jobs > 0 ? 'warning' : ''}`}>
                  {queue.rq_queue?.pending_jobs || 0}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Processing</span>
                <span className="metric-value">{queue.database?.processing || 0}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Health</span>
                <span className={`metric-value health-text-${queue.health}`}>
                  {queue.health}
                </span>
              </div>
              {queue.throughput?.completed_last_hour > 0 && (
                <div className="metric-row">
                  <span className="metric-label">Throughput</span>
                  <span className="metric-value">{queue.throughput.completed_last_hour}/hr</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Insights Card */}
        {metrics?.insights && (
          <div className="card card-insights">
            <div className="card-header">
              <h3>Insights</h3>
              <span className="card-icon">📊</span>
            </div>
            <div className="card-body">
              <div className="metric-row">
                <span className="metric-label">Total</span>
                <span className="metric-value">{metrics.insights.total}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Healthy</span>
                <span className="metric-value success">{metrics.insights.healthy}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Unhealthy</span>
                <span className="metric-value danger">{metrics.insights.unhealthy}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Avg Health</span>
                <span className={`metric-value ${(metrics.insights.average_health_score || 0) >= 0.8 ? 'success' : 'warning'}`}>
                  {metrics.insights.average_health_score !== null ? metrics.insights.average_health_score : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Errors Card */}
        {metrics?.errors && (
          <div className="card card-errors">
            <div className="card-header">
              <h3>Errors</h3>
              <span className="card-icon">⚠️</span>
            </div>
            <div className="card-body">
              <div className="metric-row">
                <span className="metric-label">Total</span>
                <span className="metric-value">{metrics.errors.total}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">4xx (Client)</span>
                <span className="metric-value warning">{metrics.errors.client_errors}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">5xx (Server)</span>
                <span className="metric-value danger">{metrics.errors.server_errors}</span>
              </div>
            </div>
          </div>
        )}

        {/* Workers Card */}
        {metrics?.workers && (
          <div className="card card-workers">
            <div className="card-header">
              <h3>Workers</h3>
              <span className="card-icon">⚙️</span>
            </div>
            <div className="card-body">
              <div className="metric-row">
                <span className="metric-label">Total</span>
                <span className="metric-value">{metrics.workers.total}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Active</span>
                <span className="metric-value success">{metrics.workers.alive}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Dead</span>
                <span className="metric-value danger">{metrics.workers.dead}</span>
              </div>
            </div>
          </div>
        )}

        {/* System Card */}
        {metrics?.system && (
          <div className="card card-system">
            <div className="card-header">
              <h3>System</h3>
              <span className="card-icon">🖥️</span>
            </div>
            <div className="card-body">
              <div className="metric-row">
                <span className="metric-label">API Hits</span>
                <span className="metric-value">{metrics.system.api_hits}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Avg Process Time</span>
                <span className="metric-value">
                  {metrics.jobs?.average_processing_time ? `${metrics.jobs.average_processing_time}s` : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;