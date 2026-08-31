import { memo, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import Icon from './Icon'

const NODE_COLORS = {
  email: '#0070f3',
  ip: '#ee0000',
  domain: '#7928ca',
  registrar: '#f59e0b',
  unknown: '#888888',
}

const NODE_SIZES = {
  email: 9,
  ip: 7,
  domain: 7,
  registrar: 6,
  unknown: 4,
}

function CampaignGraph({ graphData, campaignData, onRefresh }) {
  const containerRef = useRef(null)
  const [dimensions, setDimensions] = useState({ width: 600, height: 420 })

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const updateSize = () => {
      setDimensions({ width: container.clientWidth || 600, height: 420 })
    }

    updateSize()
    const observer = new ResizeObserver(updateSize)
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  const formattedGraph = useMemo(() => ({
    nodes: (graphData?.nodes || []).map((n) => ({ ...n })),
    links: (graphData?.edges || []).map((e) => ({
      source: e.source,
      target: e.target,
    })),
  }), [graphData])

  const hasLinks = campaignData?.linked_emails?.length > 0
  const hasNodes = graphData?.nodes?.length > 0

  return (
    <div className="glass-card" id="campaign-graph-section">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="network" /></span>
          Campaign Correlation
        </span>
        <button className="btn-secondary" onClick={onRefresh} id="refresh-graph-btn">
          <Icon name="refresh" /> Refresh
        </button>
      </div>
      <div className="card-body">
        {hasNodes ? (
          <>
            <div className="campaign-graph-container" ref={containerRef}>
              <ForceGraph2D
                width={dimensions.width}
                height={dimensions.height}
                graphData={formattedGraph}
                backgroundColor="rgba(0,0,0,0)"
                nodeColor={(node) => NODE_COLORS[node.type] || NODE_COLORS.unknown}
                nodeRelSize={1}
                nodeVal={(node) => NODE_SIZES[node.type] || 4}
                nodeLabel={(node) => {
                  const typeLabel = node.type ? node.type.toUpperCase() : '?'
                  return `[${typeLabel}] ${node.label || node.id}`
                }}
                nodeCanvasObjectMode={() => 'after'}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  // ForceGraph renders once before d3 assigns node coordinates.
                  // Canvas gradients reject undefined/NaN positions, so skip that
                  // initial frame; the node is painted normally on the next tick.
                  if (!Number.isFinite(node.x) || !Number.isFinite(node.y) || !Number.isFinite(globalScale) || globalScale <= 0) {
                    return
                  }
                  const size = NODE_SIZES[node.type] || 4
                  const color = NODE_COLORS[node.type] || NODE_COLORS.unknown

                  // Label
                  const label = String(node.label || node.id || '')
                  const fontSize = Math.max(10 / globalScale, 3)
                  ctx.font = `${fontSize}px Inter, sans-serif`
                  ctx.textAlign = 'center'
                  ctx.textBaseline = 'top'
                  ctx.fillStyle = '#4d4d4d'

                  const maxLen = 20
                  const displayLabel = label.length > maxLen ? `${label.slice(0, maxLen)}...` : label
                  ctx.fillText(displayLabel, node.x, node.y + size + 3)
                }}
                linkColor={() => 'rgba(23,23,23,0.16)'}
                linkWidth={1.5}
                linkDirectionalParticles={2}
                linkDirectionalParticleWidth={2.5}
                linkDirectionalParticleColor={() => 'rgba(0, 112, 243, 0.6)'}
              />
            </div>

            <div className="graph-legend">
              {Object.entries(NODE_COLORS).filter(([k]) => k !== 'unknown').map(([type, color]) => (
                <span key={type} className="graph-legend-item">
                  <span
                    className="graph-legend-dot"
                    style={{ background: color, '--dot-color': color }}
                  />
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </span>
              ))}
            </div>

            {hasLinks && (
              <div className="campaign-stats">
                <div className="campaign-stat">
                  <div className="campaign-stat-value">{campaignData.campaign_size}</div>
                  <div className="campaign-stat-label">Campaign Size</div>
                </div>
                <div className="campaign-stat">
                  <div className="campaign-stat-value">{campaignData.confidence}%</div>
                  <div className="campaign-stat-label">Confidence</div>
                </div>
                <div className="campaign-stat">
                  <div className="campaign-stat-value">{campaignData.shared_infra?.length || 0}</div>
                  <div className="campaign-stat-label">Shared Infra</div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="no-campaign">
            <div className="no-campaign-icon"><Icon name="network" size={36} /></div>
            <div className="no-campaign-text">No campaign detected</div>
            <div className="no-campaign-hint">
              Upload multiple related emails to discover shared infrastructure and campaign patterns.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(CampaignGraph)
