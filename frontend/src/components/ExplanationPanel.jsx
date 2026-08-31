import { memo } from 'react'
import Icon from './Icon'

function ExplanationPanel({ explanation, flags }) {
  return (
    <div className="glass-card explanation-panel" id="explanation-section">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="bot" /></span>
          AI-Generated Analysis
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500 }}>
          Powered by Gemini
        </span>
      </div>
      <div className="card-body">
        {explanation ? (
          <div className="explanation-text">{explanation}</div>
        ) : (
          <div className="explanation-text" style={{ fontStyle: 'italic', opacity: 0.6 }}>
            No explanation available. Add a Gemini API key for AI-powered analysis.
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(ExplanationPanel)
