import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

import Dashboard from './Dashboard';
import UploadPage from './Upload';
import JobsPage from './Jobs';
import InsightsPage from './Insights';

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