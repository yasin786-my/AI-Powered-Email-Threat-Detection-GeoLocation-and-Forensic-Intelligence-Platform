import { useState, useEffect, memo } from 'react'
import Icon from './Icon'

const TIER_COLORS = {
  Critical: 'var(--error)',
  High: 'var(--warning)',
  Medium: 'var(--warning)',
  Low: 'var(--link)',
  Safe: '#29bc9b',
}

function FraudScoreCard({ score, tier, flags, contributions }) {
  const [animatedScore, setAnimatedScore] = useState(0)
  const color = TIER_COLORS[tier] || 'var(--text-muted)'

  // Animated score counter
  useEffect(() => {
    setAnimatedScore(0)
    const duration = 1500
    const startTime = performance.now()

    function animate(currentTime) {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setAnimatedScore(Math.round(eased * score))

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [score])

  // SVG circle math — larger ring
  const radius = 72
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference - (animatedScore / 100) * circumference

  // Top contributions to show inline
  const topContributions = (contributions || []).slice(0, 4)
  const maxPoints = Math.max(1, ...topContributions.map((c) => c.points))

  return (
    <div
      className="glass-card fraud-score-card"
      style={{ '--score-glow': color }}
      id="fraud-score-section"
    >
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="target" /></span>
          Fraud Assessment
        </span>
      </div>
      <div className="card-body">
        <div className="score-circle">
          <svg viewBox="0 0 180 180">
            <circle className="score-track" cx="90" cy="90" r={radius} />
            <circle
              className="score-fill"
              cx="90"
              cy="90"
              r={radius}
              stroke={color}
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
            />
          </svg>
          <div className="score-value">
            <div className="score-number" style={{ color }}>{animatedScore}</div>
            <div className="score-label">/ 100</div>
          </div>
        </div>

        <div className={`risk-tier-badge ${tier?.toLowerCase()}`}>
          {tier} Risk
        </div>

        {/* Feature contribution bars integrated below score */}
        {topContributions.length > 0 && (
          <div className="score-contributions">
            <div className="bar-list">
              {topContributions.map((c) => (
                <div className="bar-row" key={c.signal}>
                  <span>{c.signal}</span>
                  <div className="bar-track">
                    <i style={{ width: `${(c.points / maxPoints) * 100}%` }} />
                  </div>
                  <b>+{c.points}</b>
                </div>
              ))}
            </div>
          </div>
        )}

        {flags && flags.length > 0 && (
          <div className="flags-list">
            {flags.map((flag, i) => (
              <div className="flag-item" key={i}>
                <span className="flag-dot" style={{ background: color }} />
                {flag}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(FraudScoreCard)
