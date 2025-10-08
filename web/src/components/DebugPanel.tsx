import React from 'react'

const DebugPanel: React.FC<{ requestUrl?: string; rawResponse?: string; error?: string }> = ({ requestUrl, rawResponse, error }) => {
  return (
    <div style={{ marginTop: 12, padding: 8, border: '1px solid #eee', background: '#fafafa' }}>
      <h3 style={{ margin: '0 0 8px 0' }}>Debug</h3>
      <div style={{ fontSize: 12, color: '#333' }}>
        <div><strong>Request URL:</strong> {requestUrl || '-'}</div>
        <div style={{ marginTop: 6 }}><strong>Raw response / error:</strong></div>
        <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12 }}>{error ?? rawResponse ?? '-'}</pre>
      </div>
    </div>
  )
}

export default DebugPanel
