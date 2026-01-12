import { Tag } from 'lucide-react'
import type { AnnotationLabel } from '../types'

interface AnnotationsPanelProps {
    annotations: AnnotationLabel[]
}

export function AnnotationsPanel({ annotations }: AnnotationsPanelProps) {
    return (
        <div className="panel">
            <div className="panel__header">
                <Tag className="panel__header-icon" />
                <span>AI-genererte annotasjoner</span>
                {annotations.length > 0 && (
                    <span style={{
                        marginLeft: 'auto',
                        background: 'var(--accent-electric)',
                        color: 'var(--bg-void)',
                        padding: '0.125rem 0.5rem',
                        borderRadius: '10px',
                        fontSize: '0.7rem',
                        fontWeight: 600
                    }}>
                        {annotations.length}
                    </span>
                )}
            </div>
            <div className="panel__content">
                <div className="annotations-list">
                    {annotations.length === 0 ? (
                        <div className="annotation-item">
                            <div className="annotation-marker inactive"></div>
                            <span className="annotation-text">
                                Klikk "Analyser med AI" for å generere
                            </span>
                        </div>
                    ) : (
                        annotations.map((ann, index) => (
                            <div key={index} className="annotation-item">
                                <div className="annotation-marker"></div>
                                <div>
                                    <div className="annotation-date">{ann.point.x}</div>
                                    <div className="annotation-text">{ann.text}</div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}
