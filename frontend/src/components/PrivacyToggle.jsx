import { memo } from 'react'
import Icon from './Icon'

function PrivacyToggle({ enabled, onToggle }) {
  return (
    <div className="glass-card privacy-card" id="privacy-section">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="lock" /></span>
          Privacy
        </span>
      </div>
      <div className="card-body">
        <div className="toggle-wrapper">
          <label className="toggle" id="privacy-toggle">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => onToggle(e.target.checked)}
            />
            <span className="toggle-slider" />
          </label>
          <span className="toggle-label">
            {enabled ? 'PII Masking Active' : 'PII Masking Off'}
          </span>
        </div>
      </div>
    </div>
  )
}

export default memo(PrivacyToggle)
