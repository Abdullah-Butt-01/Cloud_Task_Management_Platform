import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Step 19: Real Dashboard page (replaces placeholder)
import Dashboard from './Dashboard';

// Step 18: Placeholder pages — will be built in Steps 19-22
const UploadPage = () => (
  <div className="page">
    <h1>Upload Log File</h1>
    <p>File upload interface will appear here (Step 20).</p>
  </div>
);

const JobsPage = () => (
  <div className="page">
    <h1>Processing Jobs</h1>
    <p>Jobs table will appear here (Step 21).</p>
  </div>
);

const InsightsPage = () => (
  <div className="page">
    <h1>Log Insights</h1>
    <p>Insights and charts will appear here (Step 22).</p>
  </div>
);

function App() {
  return (
    <Router>
      <div className="app">
        {/* Step 18: Navigation layout — will be styled in Step 19 */}
        <nav className="navbar">
          <div className="nav-brand">
            <Link to="/">Log Processing</Link>
          </div>
          <ul className="nav-links">
            <li><Link to="/">Dashboard</Link></li>
            <li><Link to="/upload">Upload</Link></li>
            <li><Link to="/jobs">Jobs</Link></li>
            <li><Link to="/insights">Insights</Link></li>
          </ul>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/insights" element={<InsightsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;