import { useState, useRef, useCallback, memo } from 'react'
import Icon from './Icon'

function UploadPanel({ onUpload, isAnalyzing }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      if (file.name.endsWith('.eml')) {
        onUpload(file)
      }
    }
  }, [onUpload])

  const handleClick = useCallback(() => {
    if (!isAnalyzing) {
      fileInputRef.current?.click()
    }
  }, [isAnalyzing])

  const handleFileChange = useCallback((e) => {
    const file = e.target.files?.[0]
    if (file) {
      onUpload(file)
      e.target.value = '' // Reset to allow re-uploading same file
    }
  }, [onUpload])

  return (
    <div className="upload-panel glass-card" id="upload-section">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="mail" /></span>
          Email Analysis
        </span>
      </div>
      <div className="card-body">
        {isAnalyzing ? (
          <div className="upload-analyzing">
            <div className="analyzing-spinner" />
            <span className="analyzing-text">Analyzing email — parsing headers, tracing origin, running ML model...</span>
          </div>
        ) : (
          <div
            className={`upload-dropzone ${isDragOver ? 'drag-over' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleClick}
            id="upload-dropzone"
          >
            <div className="upload-content">
              <div className="upload-icon"><Icon name="upload" size={38} /></div>
              <div className="upload-title">Drop .eml file here or click to browse</div>
              <div className="upload-subtitle">
                Supports standard .eml email files for forensic analysis
              </div>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".eml"
              className="upload-file-input"
              onChange={handleFileChange}
              id="file-input"
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(UploadPanel)
