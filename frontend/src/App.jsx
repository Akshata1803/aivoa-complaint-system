import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setActiveModule } from './store/slices/complaintSlice';
import LogComplaintForm from './components/LogComplaintForm';
import AICopilotPanel from './components/AICopilotPanel';
import { ShieldCheck, Layers, Pill } from 'lucide-react';
import { API_BASE } from './config';

export function App() {
  const dispatch = useDispatch();
  const { activeModule } = useSelector((state) => state.complaint);
  const [backendHealth, setBackendHealth] = useState({ status: 'checking' });

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => setBackendHealth(data))
      .catch(() => setBackendHealth({ status: 'offline' }));
  }, []);

  return (
    <div className="app-wrapper">
      {/* Top Navbar */}
      <header className="top-navbar">
        <div className="brand-container">
          <div className="brand-icon">
            <ShieldCheck size={22} />
          </div>
          <div>
            <h1 className="brand-title">AIVOA Complaint Management System</h1>
            <p className="brand-tag">Pharmaceutical Manufacturing QA Module (API &amp; FDF)</p>
          </div>
        </div>

        <div className="navbar-right">
          {/* Module Selector */}
          <div className="module-toggle">
            <button
              type="button"
              className={`module-btn ${activeModule === 'API_QA' ? 'active' : ''}`}
              onClick={() => dispatch(setActiveModule('API_QA'))}
            >
              <Layers size={14} />
              <span>API QA</span>
            </button>
            <button
              type="button"
              className={`module-btn ${activeModule === 'FDF_QA' ? 'active' : ''}`}
              onClick={() => dispatch(setActiveModule('FDF_QA'))}
            >
              <Pill size={14} />
              <span>FDF QA</span>
            </button>
          </div>

          {/* Backend Status */}
          <div className="server-status">
            <span
              className="status-indicator-dot"
              style={{
                backgroundColor: backendHealth.status === 'healthy' ? '#10b981' : '#f59e0b',
                boxShadow: `0 0 6px ${backendHealth.status === 'healthy' ? '#10b981' : '#f59e0b'}`,
              }}
            />
            <span>
              Backend: <strong>{backendHealth.status}</strong>
            </span>
          </div>
        </div>
      </header>

      {/* Main Two-Column Workspace Layout */}
      <main className="workspace-container">
        {/* Left Panel: Log Customer Complaint Form Component (Read-Only) */}
        <section aria-label="Customer Complaint Form" className="panel-col">
          <LogComplaintForm />
        </section>

        {/* Right Panel: AIVOA Co-pilot AI Assistant (Upload & Chat Intake) */}
        <section aria-label="AI Complaint Intake Assistant" className="panel-col">
          <AICopilotPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
