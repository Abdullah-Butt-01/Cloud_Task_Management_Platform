import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Insights.css';

// Step 22: Lightweight bar chart component (SVG-based, no external library needed)
function BarChart({ data, title, color = '#3498db', maxValue }) {
  if (!data || data.length === 0) return null;

  const max = maxValue || Math.max(...data.map(d => d.value));
  const chartHeight = 200;
  const barWidth = Math.max(30, 600 / data.length - 10);
  const gap = 10;

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title}</h3>
      <svg viewBox={`0 0 ${data.length * (barWidth + gap) + gap} ${chartHeight + 40}`} className="chart-svg">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
          <line
            key={i}
            x1={gap}
            y1={chartHeight - (ratio * chartHeight) + 20}
            x2={data.length * (barWidth + gap)}
            y2={chartHeight - (ratio * chartHeight) + 20}
            stroke="#e9ecef"
            strokeWidth="1"
          />
        ))}

        {data.map((item, index) => {
          const barHeight = (item.value / max) * chartHeight;
          const x = gap + index * (barWidth + gap);
          const y = chartHeight - barHeight + 20;

          return (
            <g key={index}>
              {/* Bar */}
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={color}
                rx="4"
                className="chart-bar"
              >
                <title>{`${item.label}: ${item.value}`}</title>
              </rect>
              {/* Value label */}
              <text
                x={x + barWidth / 2}
                y={y - 8}
                textAnchor="middle"
                className="chart-value-label"
              >
                {item.value}
              </text>
              {/* X-axis label */}
              <text
                x={x + barWidth / 2}
                y={chartHeight + 35}
                textAnchor="middle"
                className="chart-axis-label"
              >
                {item.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// Step 22: Pie chart component (SVG-based)
function PieChart({ data, title }) {
  if (!data || data.length === 0) return null;

  const total = data.reduce((sum, d) => sum + d.value, 0);
  const radius = 80;
  const centerX = 100;
  const centerY = 100;
  let currentAngle = 0;

  const colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c'];

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title}</h3>
      <div className="pie-chart-wrapper">
        <svg viewBox="0 0 200 200" className="chart-svg pie-svg">
          {data.map((item, index) => {
            const angle = (item.value / total) * 2 * Math.PI;
            const startAngle = currentAngle;
            currentAngle += angle;
            const endAngle = currentAngle;

            const x1 = centerX + radius * Math.cos(startAngle);
            const y1 = centerY + radius * Math.sin(startAngle);
            const x2 = centerX + radius * Math.cos(endAngle);
            const y2 = centerY + radius * Math.sin(endAngle);

            const largeArc = angle > Math.PI ? 1 : 0;

            return (
              <path
                key={index}
                d={`M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`}
                fill={colors[index % colors.length]}
                stroke="white"
                strokeWidth="2"
                className="pie-slice"
              >
                <title>{`${item.label}: ${item.value} (${((item.value / total) * 100).toFixed(1)}%)`}</title>
              </path>
            );
          })}
        </svg>
        <div className="pie-legend">
          {data.map((item, index) => (
            <div key={index} className="legend-item">
              <span
                className="legend-color"
                style={{ backgroundColor: colors[index % colors.length] }}
              />
              <span className="legend-label">{item.label}</span>
              <span className="legend-value">{item.value}</span>
              <span className="legend-percent">
                ({((item.value / total) * 100).toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Step 22: Line chart component (SVG-based) for trends
function LineChart({ data, title, color = '#3498db' }) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data.map(d => d.value));
  const min = Math.min(...data.map(d => d.value));
  const range = max - min || 1;

  const chartWidth = 600;
  const chartHeight = 200;
  const padding = 40;

  const points = data.map((item, index) => {
    const x = padding + (index / (data.length - 1)) * (chartWidth - 2 * padding);
    const y = padding + chartHeight - padding - ((item.value - min) / range) * (chartHeight - 2 * padding);
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title}</h3>
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="chart-svg">
        {/* Grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
          <line
            key={i}
            x1={padding}
            y1={padding + (1 - ratio) * (chartHeight - 2 * padding)}
            x2={chartWidth - padding}
            y2={padding + (1 - ratio) * (chartHeight - 2 * padding)}
            stroke="#e9ecef"
            strokeWidth="1"
          />
        ))}

        {/* Line */}
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          points={points}
          className="chart-line"
        />

        {/* Data points */}
        {data.map((item, index) => {
          const x = padding + (index / (data.length - 1)) * (chartWidth - 2 * padding);
          const y = padding + chartHeight - padding - ((item.value - min) / range) * (chartHeight - 2 * padding);
          return (
            <g key={index}>
              <circle cx={x} cy={y} r="4" fill={color} className="chart-point" />
              <text x={x} y={y - 10} textAnchor="middle" className="chart-point-label">
                {item.value}
              </text>
              <text x={x} y={chartHeight - 5} textAnchor="middle" className="chart-axis-label">
                {item.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function InsightsPage() {
  const [insights, setInsights] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Step 22: Fetch insights and metrics
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [insightsRes, metricsRes] = await Promise.all([
          axios.get('/insights').catch(() => ({ data: { data: [] } })),
          axios.get('/metrics').catch(() => ({ data: { data: null } })),
        ]);

        setInsights(insightsRes.data.data || []);
        setMetrics(metricsRes.data.data);
        setError(null);
      } catch (err) {
        setError('Failed to load insights');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 15000); // Refresh every 15s
    return () => clearInterval(interval);
  }, []);

  // Step 22: Prepare chart data from insights
  const prepareChartData = () => {
    if (!insights || insights.length === 0) return null;

    // Status code distribution (aggregate across all insights)
    const statusCodes = [
      { label: '200', value: insights.reduce((sum, i) => sum + (i.status_200_count || 0), 0) },
      { label: '301', value: insights.reduce((sum, i) => sum + (i.status_301_count || 0), 0) },
      { label: '302', value: insights.reduce((sum, i) => sum + (i.status_302_count || 0), 0) },
      { label: '401', value: insights.reduce((sum, i) => sum + (i.status_401_count || 0), 0) },
      { label: '403', value: insights.reduce((sum, i) => sum + (i.status_403_count || 0), 0) },
      { label: '404', value: insights.reduce((sum, i) => sum + (i.status_404_count || 0), 0) },
      { label: '500', value: insights.reduce((sum, i) => sum + (i.status_500_count || 0), 0) },
      { label: '504', value: insights.reduce((sum, i) => sum + (i.status_504_count || 0), 0) },
    ].filter(d => d.value > 0);

    // Error categories
    const errorCategories = [
      { label: 'Client Errors (4xx)', value: insights.reduce((sum, i) => sum + (i.client_error_count || 0), 0) },
      { label: 'Server Errors (5xx)', value: insights.reduce((sum, i) => sum + (i.server_error_count || 0), 0) },
    ].filter(d => d.value > 0);

    // Health distribution
    const healthDistribution = [
      { label: 'Healthy', value: insights.filter(i => i.health_status === 'healthy').length },
      { label: 'Degraded', value: insights.filter(i => i.health_status === 'degraded').length },
      { label: 'Unhealthy', value: insights.filter(i => i.health_status === 'unhealthy').length },
      { label: 'Unknown', value: insights.filter(i => i.health_status === 'unknown').length },
    ].filter(d => d.value > 0);

    // Top endpoints (aggregate across all insights)
    const endpointMap = {};
    insights.forEach(insight => {
      if (insight.top_endpoints) {
        insight.top_endpoints.forEach(ep => {
          const key = `${ep.method} ${ep.endpoint}`;
          endpointMap[key] = (endpointMap[key] || 0) + ep.count;
        });
      }
    });
    const topEndpoints = Object.entries(endpointMap)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);

    // Requests per upload (line chart data)
    const requestsPerUpload = insights
      .slice(-10) // Last 10 uploads
      .map((insight, index) => ({
        label: `#${insight.file_job_id || index + 1}`,
        value: insight.total_requests || 0,
      }));

    // Health score trend
    const healthTrend = insights
      .slice(-10)
      .map((insight, index) => ({
        label: `#${insight.file_job_id || index + 1}`,
        value: insight.health_score !== null ? Math.round(insight.health_score * 100) : 0,
      }));

    return {
      statusCodes,
      errorCategories,
      healthDistribution,
      topEndpoints,
      requestsPerUpload,
      healthTrend,
    };
  };

  const chartData = prepareChartData();

  if (loading) {
    return (
      <div className="insights-page">
        <div className="loading">Loading insights...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="insights-page">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="insights-page">
      <div className="insights-header">
        <h1>Log Insights</h1>
        <p className="insights-subtitle">
          Visual analytics from processed log files
        </p>
      </div>

      {/* Step 22: Summary cards */}
      {metrics && (
        <div className="insights-summary">
          <div className="summary-card">
            <span className="summary-value">{metrics.insights?.total || 0}</span>
            <span className="summary-label">Total Insights</span>
          </div>
          <div className="summary-card">
            <span className="summary-value">{metrics.jobs?.total || 0}</span>
            <span className="summary-label">Total Jobs</span>
          </div>
          <div className="summary-value">
            {metrics.errors?.total || 0}
          </div>
          <span className="summary-label">Total Errors</span>
          <div className="summary-card">
            <span className="summary-value">
              {metrics.insights?.average_health_score !== null
                ? `${(metrics.insights.average_health_score * 100).toFixed(0)}%`
                : 'N/A'}
            </span>
            <span className="summary-label">Avg Health</span>
          </div>
        </div>
      )}

      {/* Step 22: Charts grid */}
      {chartData && insights.length > 0 ? (
        <div className="charts-grid">
          {/* Status codes bar chart */}
          {chartData.statusCodes.length > 0 && (
            <div className="chart-card">
              <BarChart
                data={chartData.statusCodes}
                title="HTTP Status Codes"
                color="#3498db"
              />
            </div>
          )}

          {/* Error categories pie chart */}
          {chartData.errorCategories.length > 0 && (
            <div className="chart-card">
              <PieChart
                data={chartData.errorCategories}
                title="Error Distribution"
              />
            </div>
          )}

          {/* Health distribution pie chart */}
          {chartData.healthDistribution.length > 0 && (
            <div className="chart-card">
              <PieChart
                data={chartData.healthDistribution}
                title="Health Distribution"
              />
            </div>
          )}

          {/* Top endpoints bar chart */}
          {chartData.topEndpoints.length > 0 && (
            <div className="chart-card">
              <BarChart
                data={chartData.topEndpoints}
                title="Top Endpoints"
                color="#2ecc71"
              />
            </div>
          )}

          {/* Requests per upload line chart */}
          {chartData.requestsPerUpload.length > 1 && (
            <div className="chart-card full-width">
              <LineChart
                data={chartData.requestsPerUpload}
                title="Requests Per Upload (Last 10)"
                color="#9b59b6"
              />
            </div>
          )}

          {/* Health trend line chart */}
          {chartData.healthTrend.length > 1 && (
            <div className="chart-card full-width">
              <LineChart
                data={chartData.healthTrend}
                title="Health Score Trend (Last 10)"
                color="#e74c3c"
              />
            </div>
          )}
        </div>
      ) : (
        <div className="no-insights">
          <p>No insights available yet.</p>
          <a href="/upload" className="upload-link">Upload a log file</a> to generate insights.
        </div>
      )}

      {/* Step 22: Insights table */}
      {insights.length > 0 && (
        <div className="insights-table-section">
          <h2>Recent Insights</h2>
          <div className="table-container">
            <table className="insights-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Requests</th>
                  <th>Errors</th>
                  <th>Clients</th>
                  <th>Endpoints</th>
                  <th>Health Score</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {insights.slice(0, 10).map((insight) => (
                  <tr key={insight.insight_id}>
                    <td className="mono">{insight.file_job_id}</td>
                    <td className="right">{insight.total_requests || 0}</td>
                    <td className="right">
                      {insight.total_error_count > 0 ? (
                        <span className="error-count">{insight.total_error_count}</span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="right">{insight.unique_client_count || 0}</td>
                    <td className="right">{insight.total_endpoints || 0}</td>
                    <td className="right">
                      {insight.health_score !== null ? (
                        <span className={`health-score health-${insight.health_status}`}>
                          {(insight.health_score * 100).toFixed(0)}%
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      <span className={`status-badge status-${insight.health_status}`}>
                        {insight.health_status}
                      </span>
                    </td>
                    <td className="date-cell">
                      {new Date(insight.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="refresh-indicator">
        <span className="refresh-dot"></span>
        Auto-refreshing every 15 seconds
      </div>
    </div>
  );
}

export default InsightsPage;