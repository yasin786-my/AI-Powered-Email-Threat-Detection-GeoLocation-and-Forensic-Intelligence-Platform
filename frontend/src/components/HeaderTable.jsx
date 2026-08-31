import { memo, useState } from 'react'
import Icon from './Icon'

function AuthPill({ protocol, result }) {
  const status = result === 'pass' ? 'pass' : result === 'fail' || result === 'softfail' ? 'fail' : 'none'
  const label = status === 'pass' ? 'PASS' : status === 'fail' ? 'FAIL' : 'NONE'

  return (
    <div className={`auth-pill ${status}`}>
      <span className="auth-proto">{protocol}</span>
      <span>{status === 'pass' && <Icon name="check" />} {label}</span>
    </div>
  )
}

function HeaderTable({ headerData, privacyMask }) {
  const [showDetails, setShowDetails] = useState(false)

  if (!headerData) return null

  return (
    <div className="glass-card auth-strip-card" id="header-analysis-section">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="lock" /></span>
          Authentication Status
        </span>
      </div>
      <div className="card-body">
        {/* Compact auth pill badges */}
        <div className="auth-pills">
          <AuthPill protocol="SPF" result={headerData.spf} />
          <AuthPill protocol="DKIM" result={headerData.dkim} />
          <AuthPill protocol="DMARC" result={headerData.dmarc} />
        </div>

        {/* Stats row */}
        <div className="header-stats">
          <span><Icon name="network" /> Hops: <strong>{headerData.num_hops || 0}</strong></span>
          <span><Icon name="location" /> URLs: <strong>{headerData.num_urls || 0}</strong></span>
          <span><Icon name="alert" /> Urgency: <strong>{headerData.urgency_word_count || 0}</strong></span>
          <span><Icon name="file" /> Attachments: <strong>{headerData.has_attachment ? 'Yes' : 'No'}</strong></span>
        </div>

        {/* Collapsible envelope details */}
        <button
          className="envelope-toggle-btn"
          onClick={() => setShowDetails(!showDetails)}
        >
          <Icon name="chevron" className={showDetails ? 'chevron-open' : ''} /> {showDetails ? 'Hide' : 'Show'} Envelope Details
        </button>

        {showDetails && (
          <div className="envelope-details">
            <div className="envelope-row">
              <span className="envelope-label">From</span>
              <span className="envelope-value">{headerData.from || 'N/A'}</span>
            </div>
            <div className="envelope-row">
              <span className="envelope-label">To</span>
              <span className="envelope-value">{headerData.to || 'N/A'}</span>
            </div>
            <div className="envelope-row">
              <span className="envelope-label">Subject</span>
              <span className="envelope-value" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {headerData.subject || 'N/A'}
              </span>
            </div>
            <div className="envelope-row">
              <span className="envelope-label">Date</span>
              <span className="envelope-value">{headerData.date || 'N/A'}</span>
            </div>
            {headerData.reply_to && (
              <div className="envelope-row">
                <span className="envelope-label">Reply-To</span>
                <span className="envelope-value">
                  {headerData.reply_to}
                  {headerData.reply_to_mismatch && (
                    <span className="status-badge fail" style={{ marginLeft: 8 }}><Icon name="alert" /> MISMATCH</span>
                  )}
                </span>
              </div>
            )}
            {headerData.return_path && (
              <div className="envelope-row">
                <span className="envelope-label">Return-Path</span>
                <span className="envelope-value">
                  {headerData.return_path}
                  {headerData.return_path_mismatch && (
                    <span className="status-badge fail" style={{ marginLeft: 8 }}><Icon name="alert" /> MISMATCH</span>
                  )}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(HeaderTable)
