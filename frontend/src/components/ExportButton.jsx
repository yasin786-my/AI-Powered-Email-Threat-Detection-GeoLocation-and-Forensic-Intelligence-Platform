import { memo } from 'react'
import Icon from './Icon'

function ExportButton({ caseId, apiBase, mask }) {
  const handleExport = async () => {
    if (!caseId) return

    try {
      const maskParam = mask ? '?mask=true' : ''
      const response = await fetch(`${apiBase}/report/${caseId}${maskParam}`)

      if (!response.ok) {
        let message = 'Report generation failed'
        try {
          const err = await response.json()
          if (err.error) message = err.error
        } catch {
          // response body wasn't JSON
        }
        throw new Error(message)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `forensic_report_${caseId}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed:', err)
      alert(err.message || 'Failed to generate report. Make sure the backend is running.')
    }
  }

  return (
    <button
      className="export-btn"
      onClick={handleExport}
      disabled={!caseId}
      id="export-report-btn"
    >
      <Icon name="file" /> Export Forensic Report (PDF)
    </button>
  )
}

export default memo(ExportButton)
