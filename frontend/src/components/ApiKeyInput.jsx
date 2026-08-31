import { memo } from 'react'
import Icon from './Icon'

function ApiKeyInput({ value, onChange }) {
  return (
    <div className="glass-card api-key-card" id="api-key-section">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="key" /></span>
          Gemini API Key
        </span>
      </div>
      <div className="card-body">
        <div className="api-key-input-wrapper">
          <input
            id="gemini-key-input"
            type="password"
            className="api-key-input"
            placeholder="Enter your Gemini API key for AI explanations..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className={`api-key-status ${value ? 'connected' : ''}`}>
          {value ? 'Key configured — AI explanations enabled' : 'Optional — fallback explanations will be used'}
        </div>
      </div>
    </div>
  )
}

export default memo(ApiKeyInput)
