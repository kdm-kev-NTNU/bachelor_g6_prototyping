import { Activity, Database, Cpu } from 'lucide-react'

interface StatusPanelProps {
    backendConnected: boolean
    dataPoints: number
    confidence: number | null
    isAnalyzing: boolean
}

export function StatusPanel({
    backendConnected,
    dataPoints,
    confidence,
    isAnalyzing
}: StatusPanelProps) {
    return (
        <div className="panel">
            <div className="panel__header">
                <Activity className="panel__header-icon" />
                <span>Status</span>
            </div>
            <div className="panel__content">
                <div className="status-grid">
                    <div className="status-item">
                        <span className="status-item__label">
                            <Database size={14} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                            Backend
                        </span>
                        <span className={`status-item__value ${backendConnected ? 'success' : 'error'}`}>
                            {backendConnected ? 'Tilkoblet ✓' : 'Frakoblet'}
                        </span>
                    </div>

                    <div className="status-item">
                        <span className="status-item__label">
                            <Cpu size={14} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                            Data lastet
                        </span>
                        <span className={`status-item__value ${dataPoints > 0 ? 'success' : 'warning'}`}>
                            {dataPoints > 0 ? `${dataPoints} punkter` : 'Venter...'}
                        </span>
                    </div>

                    <div className="status-item">
                        <span className="status-item__label">AI Status</span>
                        <span className={`status-item__value ${isAnalyzing ? 'warning' : ''}`}>
                            {isAnalyzing ? 'Analyserer...' : 'Klar'}
                        </span>
                    </div>
                </div>

                {confidence !== null && (
                    <div className="confidence-section">
                        <div className="confidence-label">
                            <span style={{ color: 'var(--text-secondary)' }}>Konfidensgrad</span>
                            <span style={{ color: 'var(--accent-mint)', fontFamily: 'var(--font-mono)' }}>
                                {Math.round(confidence * 100)}%
                            </span>
                        </div>
                        <div className="confidence-bar">
                            <div
                                className="confidence-fill"
                                style={{ width: `${confidence * 100}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
