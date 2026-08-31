import { memo } from 'react'
import Icon from './Icon'

function Navbar({ activeView, onViewChange, caseCount }) {
  return (
    <nav className="navbar" id="main-navbar">
      <div className="navbar-brand">
        <div className="navbar-logo"><Icon name="shield" size={18} /></div>
        <div>
          <div className="navbar-title">The Royal coder</div>
          <div className="navbar-subtitle">AI-Powered Email Threat Detection, GeoLocation &amp; Forensic Intelligence Platform</div>
        </div>
      </div>

      <div className="navbar-nav">
        <button
          id="nav-dashboard"
          className={`nav-btn ${activeView === 'dashboard' ? 'active' : ''}`}
          onClick={() => onViewChange('dashboard')}
        >
          <Icon name="dashboard" /> Dashboard
        </button>
        <button
          id="nav-analytics"
          className={`nav-btn ${activeView === 'analytics' ? 'active' : ''}`}
          onClick={() => onViewChange('analytics')}
        >
          <Icon name="chart" /> Analytics
        </button>
        <button
          id="nav-cases"
          className={`nav-btn ${activeView === 'cases' ? 'active' : ''}`}
          onClick={() => onViewChange('cases')}
        >
          <Icon name="folder" /> Cases
          {caseCount > 0 && <span className="nav-badge">{caseCount}</span>}
        </button>
      </div>
    </nav>
  )
}

export default memo(Navbar)
