import { useState, useCallback, useEffect } from 'react'
import Navbar from './components/Navbar'
import ApiKeyInput from './components/ApiKeyInput'
import UploadPanel from './components/UploadPanel'
import FraudScoreCard from './components/FraudScoreCard'
import HeaderTable from './components/HeaderTable'
import TraceMap from './components/TraceMap'
import CampaignGraph from './components/CampaignGraph'
import ExplanationPanel from './components/ExplanationPanel'
import PrivacyToggle from './components/PrivacyToggle'
import CaseList from './components/CaseList'
import ExportButton from './components/ExportButton'
import AnalyticsDashboard from './components/AnalyticsDashboard'
import Icon from './components/Icon'
import './App.css'

const API_BASE = 'http://localhost:5000/api'

function App() {
  const [geminiKey, setGeminiKey] = useState(
    () => sessionStorage.getItem('gemini_key') || ''
  )
  const [analysisResult, setAnalysisResult] = useState(null)
  const [cases, setCases] = useState([])
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [analytics, setAnalytics] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [privacyMask, setPrivacyMask] = useState(false)
  const [activeView, setActiveView] = useState('dashboard') // 'dashboard' | 'cases' | 'analytics'
  const [error, setError] = useState(null)

  const handleKeyChange = useCallback((key) => {
    setGeminiKey(key)
    sessionStorage.setItem('gemini_key', key)
  }, [])

  const handleAnalyze = useCallback(async (file) => {
    setIsAnalyzing(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('email_file', file)

      const headers = {}
      if (geminiKey) {
        headers['X-Gemini-Key'] = geminiKey
      }

      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers,
        body: formData,
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.error || 'Analysis failed')
      }

      const result = await response.json()
      if (!result || typeof result !== 'object') throw new Error('The analysis server returned an invalid response')
      setAnalysisResult(result)

      if (result.graph_data) {
        setGraphData(result.graph_data)
      }

      // Analytics data is supplemental; it must not block a completed analysis.
      void fetchCases()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsAnalyzing(false)
    }
  }, [geminiKey])

  const fetchCases = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/cases`)
      if (response.ok) {
        const data = await response.json()
        setCases(data)
      }
      const analyticsResponse = await fetch(`${API_BASE}/analytics`)
      if (analyticsResponse.ok) setAnalytics(await analyticsResponse.json())
    } catch (err) {
      // silently fail — case list is non-critical
    }
  }, [])

  useEffect(() => { fetchCases() }, [fetchCases])

  const handleCaseSelect = useCallback(async (caseId) => {
    try {
      const mask = privacyMask ? '?mask=true' : ''
      const response = await fetch(`${API_BASE}/cases/${caseId}${mask}`)
      if (response.ok) {
        const data = await response.json()
        setAnalysisResult(data)
        setActiveView('dashboard')
      }
    } catch (err) {
      setError('Failed to load case')
    }
  }, [privacyMask])

  const handleRefreshGraph = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/graph`)
      if (response.ok) {
        const data = await response.json()
        setGraphData(data)
      }
    } catch (err) {
      // silently fail
    }
  }, [])

  return (
    <div className="app">
      <Navbar
        activeView={activeView}
        onViewChange={setActiveView}
        caseCount={cases.length}
      />

      <main className="main-content">
        {activeView === 'dashboard' ? (
          <>
            {/* Top Bar: API Key + Privacy */}
            <div className="top-bar">
              <ApiKeyInput value={geminiKey} onChange={handleKeyChange} />
              <PrivacyToggle enabled={privacyMask} onToggle={setPrivacyMask} />
            </div>

            {/* Upload Panel */}
            <UploadPanel
              onUpload={handleAnalyze}
              isAnalyzing={isAnalyzing}
            />

            {error && (
              <div className="error-banner">
                <span className="error-icon"><Icon name="alert" /></span>
                {error}
                <button onClick={() => setError(null)} className="error-dismiss" aria-label="Dismiss error"><Icon name="close" /></button>
              </div>
            )}

            {analysisResult && (
              <div className="results-grid">
                {/* Row 1 HERO: Fraud Score (left ~30%) + AI Explanation & Auth (right ~70%) */}
                <div className="results-row-hero">
                  <FraudScoreCard
                    score={analysisResult.fraud_score}
                    tier={analysisResult.risk_tier}
                    flags={analysisResult.flags}
                    contributions={analysisResult.risk_contributions}
                  />
                  <div className="hero-right-stack">
                    <ExplanationPanel
                      explanation={analysisResult.llm_explanation}
                      flags={analysisResult.flags}
                    />
                    <HeaderTable
                      headerData={analysisResult.header_analysis}
                      privacyMask={privacyMask}
                    />
                  </div>
                </div>

                {/* Row 2: Geo Trace Map + Campaign Graph */}
                <div className="results-row-intel">
                  <TraceMap
                    key={analysisResult.case_id || analysisResult.evidence_hash}
                    geoTrace={analysisResult.geo_trace}
                    relayHops={analysisResult.header_analysis?.relay_hops || []}
                  />
                  <CampaignGraph
                    graphData={graphData}
                    campaignData={analysisResult.campaign_data}
                    onRefresh={handleRefreshGraph}
                  />
                </div>

                {/* Row 3: Analytics Section */}
                <div className="results-row-analytics">
                  <div className="section-divider">
                    <h2><Icon name="chart" /> Intelligence Analytics</h2>
                  </div>
                  <AnalyticsDashboard analysis={analysisResult} analytics={analytics} />
                </div>

                {/* Export */}
                <div className="results-actions">
                  <ExportButton
                    caseId={analysisResult.case_id}
                    apiBase={API_BASE}
                    mask={privacyMask}
                  />
                </div>
              </div>
            )}
          </>
        ) : activeView === 'analytics' ? (
          <>
            <div className="section-divider" style={{ marginTop: 8 }}>
              <h2><Icon name="chart" /> Intelligence Analytics</h2>
            </div>
            <AnalyticsDashboard analysis={analysisResult} analytics={analytics} />
          </>
        ) : (
          <CaseList
            cases={cases}
            onRefresh={fetchCases}
            onSelect={handleCaseSelect}
            apiBase={API_BASE}
          />
        )}
      </main>
    </div>
  )
}

export default App
