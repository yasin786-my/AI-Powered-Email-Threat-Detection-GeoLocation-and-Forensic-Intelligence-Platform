import { memo } from 'react'
import Icon from './Icon'

const TIER_COLORS = { Safe: '#29bc9b', Low: '#0070f3', Medium: '#f5a623', High: '#f5a623', Critical: '#ee0000' }

function Card({ title, children, className = '' }) {
  return (
    <section className={`glass-card analytics-card ${className}`}>
      <div className="card-header">
        <span className="card-title">{title}</span>
      </div>
      <div className="card-body">{children}</div>
    </section>
  )
}

function Radar({ analysis }) {
  const h = analysis.header_analysis || {}, g = analysis.geo_trace || {}
  const authFailures = [h.spf, h.dkim, h.dmarc].filter(value => ['fail', 'softfail', 'neutral'].includes(value)).length
  const authRisk = Math.min(100, authFailures * 34 + ([h.spf, h.dkim, h.dmarc].filter(value => value === 'none').length * 8))
  const domainRisk = h.suspicious_domain ? 100 : (g.domain_age_days && g.domain_age_days < 90 ? 75 : 8)
  const axes = [authRisk, Math.min(100, (h.urgency_word_count || 0) * 14), domainRisk, g.is_vpn_or_hosting ? 100 : 5, Math.min(100, (h.url_domain_mismatch || 0) * 45)]
  const points = axes.map((v, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / 5, r = v * .42; return `${50 + Math.cos(a) * r},${50 + Math.sin(a) * r}` }).join(' ')
  return (
    <div className="radar-wrap">
      <svg viewBox="0 0 100 100">
        <polygon points="50,8 90,37 75,88 25,88 10,37" className="radar-grid" />
        <polygon points={points} className="radar-shape" />
      </svg>
      <div className="radar-labels">
        <span>Auth</span><span>Urgency</span><span>Domain</span><span>IP</span><span>URLs</span>
      </div>
    </div>
  )
}

function Histogram({ buckets }) {
  const safeBuckets = Array.isArray(buckets) ? buckets.map(value => Number(value) || 0) : Array(10).fill(0)
  const max = Math.max(1, ...safeBuckets)
  return (
    <svg className="chart-svg" viewBox="0 0 400 170">
      <line x1="36" y1="132" x2="390" y2="132" className="chart-axis" />
      {safeBuckets.map((count, index) => {
        const h = count / max * 100, x = 42 + index * 34
        return (
          <g key={index}>
            <rect x={x} y={132 - h} width="24" height={h} rx="3" className="hist-bar">
              <title>{`${index * 10}-${index * 10 + 9}: ${count} cases`}</title>
            </rect>
            <text x={x + 12} y="150" textAnchor="middle">{index * 10}</text>
            {count > 0 && <text x={x + 12} y={126 - h} textAnchor="middle" className="chart-value">{count}</text>}
          </g>
        )
      })}
      <text x="4" y="18" className="chart-label">Cases</text>
      <text x="212" y="166" textAnchor="middle" className="chart-label">Fraud-score band</text>
    </svg>
  )
}

function ScatterPlot({ points }) {
  const safePoints = Array.isArray(points) ? points.filter(point => Number.isFinite(Number(point?.age)) && Number.isFinite(Number(point?.score))) : []
  const left = 42, bottom = 145, chartWidth = 335, chartHeight = 110
  const xForAge = age => left + Math.min(1, Math.log10(Number(age) + 1) / 4) * chartWidth
  const ageTicks = [1, 30, 365, 3650, 10000]
  return (
    <svg className="chart-svg" viewBox="0 0 400 180">
      <line x1={left} y1={bottom} x2={left + chartWidth} y2={bottom} className="chart-axis" />
      <line x1={left} y1="20" x2={left} y2={bottom} className="chart-axis" />
      {[0, 50, 100].map(v => (
        <g key={v}>
          <line x1={left} y1={bottom - chartHeight * v / 100} x2={left + chartWidth} y2={bottom - chartHeight * v / 100} className="chart-grid" />
          <text x="31" y={bottom - chartHeight * v / 100 + 4} textAnchor="end">{v}</text>
        </g>
      ))}
      {ageTicks.map(age => (
        <g key={age}>
          <line x1={xForAge(age)} y1={bottom} x2={xForAge(age)} y2={bottom + 4} className="chart-axis" />
          <text x={xForAge(age)} y="160" textAnchor="middle">{age >= 1000 ? `${age / 1000}y` : `${age}d`}</text>
        </g>
      ))}
      {safePoints.map((p, i) => {
        const x = xForAge(p.age), y = bottom - p.score / 100 * chartHeight
        const labelOffset = 10 + (i % 3) * 13
        const labelToLeft = x > 300
        return <g key={i}>
          <circle cx={x} cy={y} r="4" className="scatter-point">
            <title>{`${p.age} days · score ${p.score}`}</title>
          </circle>
          <text x={x + (labelToLeft ? -7 : 7)} y={y - labelOffset} textAnchor={labelToLeft ? 'end' : 'start'} className="point-label">{Number(p.age) >= 365 ? `${(Number(p.age) / 365).toFixed(1)}y` : `${p.age}d`}</text>
        </g>
      })}
      <text x="210" y="178" textAnchor="middle" className="chart-label">Domain registration age (log scale)</text>
      <text x="6" y="15" className="chart-label">Score</text>
    </svg>
  )
}

function TrendChart({ daily, tiers }) {
  const safeDaily = Array.isArray(daily) ? daily.filter(day => day && typeof day === 'object' && typeof day.date === 'string') : []
  const safeTiers = tiers && typeof tiers === 'object' && !Array.isArray(tiers) ? tiers : {}
  if (!safeDaily.length) return <p className="empty-copy">Trend lines appear as you analyze cases on different days.</p>
  const tierNames = Object.keys(safeTiers)
  const max = Math.max(1, ...safeDaily.map(d => tierNames.reduce((sum, tier) => sum + (Number(d[tier]) || 0), 0)))
  const plotWidth = 670, barWidth = Math.min(48, Math.max(14, plotWidth / safeDaily.length - 18)), gap = safeDaily.length > 1 ? (plotWidth - barWidth) / (safeDaily.length - 1) : 0
  return (
    <>
      <svg className="chart-svg trend-svg" viewBox="0 0 760 190">
        <title>Daily fraud volume by risk tier</title>
        <line x1="38" y1="150" x2="720" y2="150" className="chart-axis" />
        {safeDaily.map((d, i) => {
          let offset = 0; const x = 42 + i * gap
          return (
            <g key={d.date}>
              {tierNames.map(tier => {
                const h = (Number(d[tier]) || 0) / max * 115, y = 150 - offset - h; offset += h
                return h ? <rect key={tier} x={x} y={y} width={barWidth} height={h} fill={TIER_COLORS[tier]}><title>{`${d.date} · ${tier}: ${d[tier]}`}</title></rect> : null
              })}
              <text x={x + barWidth / 2} y="168" textAnchor="middle">{d.date.slice(5)}</text>
            </g>
          )
        })}
      </svg>
      <div className="tier-legend">
        {tierNames.map(tier => <span key={tier}><i style={{ background: TIER_COLORS[tier] }} />{tier}</span>)}
      </div>
    </>
  )
}

function Heatmap({ daily, tiers }) {
  const safeDaily = Array.isArray(daily) ? daily.filter(day => day && typeof day === 'object' && /^\d{4}-\d{2}-\d{2}$/.test(day.date || '')) : []
  const tierNames = tiers && typeof tiers === 'object' && !Array.isArray(tiers) ? Object.keys(tiers) : []
  if (!safeDaily.length) return <p className="empty-copy">No dated cases yet.</p>
  const byDay = Object.fromEntries(safeDaily.map(d => [d.date, tierNames.reduce((sum, tier) => sum + (Number(d[tier]) || 0), 0)]))
  const max = Math.max(1, ...Object.values(byDay))
  const end = new Date(`${safeDaily[safeDaily.length - 1].date}T12:00:00`)
  const toDateKey = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  const days = Array.from({ length: 28 }, (_, i) => { const d = new Date(end); d.setDate(end.getDate() - 27 + i); const key = toDateKey(d); return { key, count: byDay[key] || 0 } })
  return (
    <>
      <div className="heatmap-weekdays">
        <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
      </div>
      <div className="heatmap">
        {days.map(day => (
          <i key={day.key} title={`${day.key}: ${day.count} cases`} style={{ opacity: day.count ? .18 + .82 * day.count / max : .06 }}>{day.count || ''}</i>
        ))}
      </div>
      <p className="chart-caption">Last 28 days ending {safeDaily[safeDaily.length - 1].date}</p>
    </>
  )
}

function AnalyticsDashboard({ analysis, analytics }) {
  const contributions = Array.isArray(analysis?.risk_contributions) ? analysis.risk_contributions : []
  const tiers = analytics?.tier_distribution && typeof analytics.tier_distribution === 'object' && !Array.isArray(analytics.tier_distribution) ? analytics.tier_distribution : {}
  const histogram = Array.isArray(analytics?.score_distribution) ? analytics.score_distribution : []
  const senders = Array.isArray(analytics?.top_senders) ? analytics.top_senders : []
  const total = Math.max(1, Object.values(tiers).reduce((sum, n) => sum + n, 0))
  const maxContribution = Math.max(1, ...contributions.map(x => x.points))
  const stops = Object.entries(tiers).reduce((a, [tier, count]) => {
    const start = a.end || 0, end = start + count / total * 100
    a.parts.push(`${TIER_COLORS[tier] || '#5b6b82'} ${start}% ${end}%`)
    a.end = end
    return a
  }, { parts: [], end: 0 }).parts.join(', ')
  const daily = Array.isArray(analytics?.daily) ? analytics.daily : []

  // Phrase cloud follows the selected email
  const tokens = `${analysis?.header_analysis?.subject || ''} ${analysis?.header_analysis?.body_preview || ''}`.toLowerCase().match(/[a-z]{4,}/g) || []
  const stopWords = new Set(['your', 'with', 'from', 'that', 'this', 'have', 'will', 'please', 'http', 'https', 'com', 'click'])
  const wordCounts = tokens.filter(word => !stopWords.has(word)).reduce((all, word) => ({ ...all, [word]: (all[word] || 0) + 1 }), {})
  const words = Object.entries(wordCounts).sort((a, b) => b[1] - a[1]).slice(0, 18)
  const maxWord = Math.max(1, ...words.map(([, n]) => n))

  return (
    <div className="analytics-grid" id="analytics-dashboard">
      {analysis && (
        <Card title={<><Icon name="alert" /> Flag Contribution</>} className="analytics-wide">
          {contributions.length ? (
            <div className="bar-list">
              {contributions.map(x => (
                <div className="bar-row" key={x.signal}>
                  <span>{x.signal}</span>
                  <div className="bar-track"><i style={{ width: `${x.points / maxContribution * 100}%` }} /></div>
                  <b>+{x.points}</b>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-copy">No high-risk evidence was triggered — all clear.</p>
          )}
        </Card>
      )}

      <Card title={<><Icon name="target" /> Risk Tier Distribution</>}>
        <div className="tier-donut" style={{ background: `conic-gradient(${stops || '#334155 0 100%'})` }}>
          <span>{analytics?.total_cases || 0}<small>cases</small></span>
        </div>
        <div className="tier-legend">
          {Object.entries(tiers).map(([tier, count]) => (
            <span key={tier}><i style={{ background: TIER_COLORS[tier] }} />{tier} {count}</span>
          ))}
        </div>
      </Card>

      <Card title={<><Icon name="bars" /> Score Distribution</>}>
        <Histogram buckets={histogram} />
      </Card>

      {analysis && (
        <Card title={<><Icon name="radar" /> Threat Profile Radar</>}>
          <Radar analysis={analysis} />
        </Card>
      )}

      <Card title={<><Icon name="chart" /> Domain Age vs Fraud Score · all cases</>}>
        <p className="chart-summary">Current email: <b>{analysis?.geo_trace?.domain_age_days != null ? `${Number(analysis.geo_trace.domain_age_days).toLocaleString()} days old` : 'registration age unavailable'}</b></p>
        {(analytics?.domain_age_points || []).length ? (
          <ScatterPlot points={analytics.domain_age_points} />
        ) : (
          <p className="empty-copy">Enable optional WHOIS enrichment to plot domain age.</p>
        )}
      </Card>

      <Card title={<><Icon name="chart" /> Fraud Volume & Tier Trend · all cases</>} className="analytics-wide">
        <TrendChart daily={daily} tiers={tiers} />
      </Card>

      <Card title={<><Icon name="dashboard" /> Activity Heatmap · all cases</>}>
        <Heatmap daily={daily} tiers={tiers} />
      </Card>

      <Card title={<><Icon name="location" /> Original Public Relay · current email</>}>
        <div className="country-bubbles">
          {analysis?.geo_trace?.country ? (
            <span className="current-country-bubble">
              {analysis.geo_trace.country}
              <b>{analysis.geo_trace.city ? ` · ${analysis.geo_trace.city}` : ''}</b>
              <small>{analysis.geo_trace.earliest_hop_ip || 'IP unavailable'}</small>
            </span>
          ) : (
            <p className="empty-copy">ip-api has not resolved a public relay IP for this email.</p>
          )}
        </div>
      </Card>

      <Card title={<><Icon name="cloud" /> Suspicious Phrase Cloud · current email</>} className="analytics-wide">
        <div className="word-cloud">
          {words.length ? words.map(([word, count]) => (
            <span key={word} style={{ fontSize: `${12 + count / maxWord * 20}px` }}>{word}</span>
          )) : (
            <p className="empty-copy">No readable subject or body text was found in this email.</p>
          )}
        </div>
      </Card>

      <Card title={<><Icon name="users" /> Top Flagged Senders</>} className="analytics-wide">
        {senders.length ? (
          <div className="bar-list">
            {senders.map(([sender, count]) => (
              <div className="bar-row" key={sender}>
                <span>{sender}</span>
                <div className="bar-track"><i style={{ width: `${count / senders[0][1] * 100}%` }} /></div>
                <b>{count}</b>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-copy">Analyze emails to build the threat intelligence view.</p>
        )}
      </Card>
    </div>
  )
}

export default memo(AnalyticsDashboard)
