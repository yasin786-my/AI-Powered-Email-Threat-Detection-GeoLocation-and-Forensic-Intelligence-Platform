import { useState, useEffect, useCallback, memo } from 'react'
import Icon from './Icon'

function CaseList({ cases, onRefresh, onSelect, apiBase }) {
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    onRefresh()
  }, [onRefresh])

  const handleDelete = useCallback(async (caseId, e) => {
    e.stopPropagation()
    if (!confirm(`Delete case ${caseId}?`)) return

    try {
      await fetch(`${apiBase}/cases/${caseId}`, { method: 'DELETE' })
      onRefresh()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }, [apiBase, onRefresh])

  const filteredCases = cases.filter((c) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      c.id?.toLowerCase().includes(q) ||
      c.filename?.toLowerCase().includes(q) ||
      c.risk_tier?.toLowerCase().includes(q)
    )
  })

  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    try {
      const d = new Date(dateStr)
      return d.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  const getTierClass = (tier) => {
    return (tier || '').toLowerCase()
  }

  return (
    <div id="case-list-section">
      <div className="case-list-header">
        <h1 className="case-list-title"><Icon name="folder" /> Case Management</h1>
        <div className="case-list-actions">
          <input
            type="text"
            className="api-key-input"
            placeholder="Search cases..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: 220 }}
            id="case-search-input"
          />
          <button className="btn-secondary" onClick={onRefresh} id="refresh-cases-btn">
            <Icon name="refresh" /> Refresh
          </button>
        </div>
      </div>

      {filteredCases.length > 0 ? (
        <div className="glass-card">
          <table className="cases-table" id="cases-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>File</th>
                <th>Date</th>
                <th>Score</th>
                <th>Risk Tier</th>
                <th>Flags</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredCases.map((c) => (
                <tr
                  key={c.id}
                  className="case-row"
                  onClick={() => onSelect(c.id)}
                >
                  <td><span className="case-id">{c.id}</span></td>
                  <td>{c.filename || '—'}</td>
                  <td>{formatDate(c.created_at)}</td>
                  <td>
                    <span className={`case-score ${getTierClass(c.risk_tier)}`}>
                      {c.fraud_score}
                    </span>
                  </td>
                  <td>
                    <span className={`risk-tier-badge ${getTierClass(c.risk_tier)}`} style={{ animation: 'none', fontSize: 10, padding: '3px 10px' }}>
                      {c.risk_tier}
                    </span>
                  </td>
                  <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {(c.flags || []).join(', ') || '—'}
                  </td>
                  <td>
                    <button
                      className="btn-secondary"
                      onClick={(e) => handleDelete(c.id, e)}
                      style={{ fontSize: 11, padding: '4px 10px', color: 'var(--danger)' }}
                    >
                      <Icon name="trash" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="glass-card">
          <div className="empty-state">
            <div className="empty-state-icon"><Icon name="inbox" size={36} /></div>
            <div className="empty-state-title">
              {cases.length === 0 ? 'No cases yet' : 'No matching cases'}
            </div>
            <div className="empty-state-text">
              {cases.length === 0
                ? 'Upload .eml files from the Dashboard to start building your case database.'
                : 'Try a different search term.'}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default memo(CaseList)
