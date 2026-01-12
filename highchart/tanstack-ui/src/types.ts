// Types matching the Python backend schema

export interface AnnotationPoint {
    x: string // ISO date YYYY-MM-DD
    y: number
}

export interface AnnotationLabel {
    point: AnnotationPoint
    text: string
    xOffset?: number
    yOffset?: number
}

export interface PlotBand {
    from: string
    to: string
    color: string
    label?: string
}

export interface PlotLine {
    value: string
    color: string
    width: number
    label?: string
    dashStyle?: string
}

export interface ChartAnalysisResponse {
    annotations: AnnotationLabel[]
    plotBands: PlotBand[]
    plotLines: PlotLine[]
    summary: string
    confidence: number
}

export interface ChartStateInput {
    seriesData: [number, number][]
    title?: string
    timeRange: {
        start: string
        end: string
    }
    yAxisLabel?: string
    existingAnnotations?: Array<{
        date: string
        y: number
        text: string
    }>
}

export interface BackendStatus {
    status: string
    openai_available: boolean
    version: string
}

export type MessageRole = 'system' | 'user' | 'assistant' | 'error'

export interface ChatMessage {
    id: string
    role: MessageRole
    content: string
    timestamp: Date
}
export interface ExistingAnnotation {
    date: string
    y: number
    text: string
}

