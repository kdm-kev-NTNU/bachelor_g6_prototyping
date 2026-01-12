import { useState, useRef, useCallback, useEffect } from 'react'
import { useChat, fetchServerSentEvents } from '@tanstack/ai-react'
import { BarChart3, Sparkles, Trash2, Zap } from 'lucide-react'
import { StockChart, type StockChartRef } from './components/StockChart'
import { ChatPanel } from './components/ChatPanel'
import { StatusPanel } from './components/StatusPanel'
import { AnnotationsPanel } from './components/AnnotationsPanel'
import type { ChartAnalysisResponse, AnnotationLabel, ExistingAnnotation } from './types'

// Mock data generator for demo
function generateMockData(): [number, number][] {
    const data: [number, number][] = []
    let price = 20
    const start = new Date('2017-01-01').getTime()

    for (let i = 0; i < 2000; i++) {
        const timestamp = start + i * 24 * 60 * 60 * 1000
        price = price * (1 + (Math.random() - 0.48) * 0.03)
        price = Math.max(10, price)
        data.push([timestamp, Math.round(price * 100) / 100])
    }
    return data
}

// Tesla existing annotations
const existingAnnotations: ExistingAnnotation[] = [
    { date: '2020-08-20', y: 133.45, text: '5 for 1 Stock split announcement' },
    { date: '2020-12-21', y: 216.62, text: 'Inclusion to S&P 500 Index' },
    { date: '2021-04-01', y: 220.58, text: 'Record earnings in Q1 2021' },
    { date: '2021-11-01', y: 402.86, text: 'Stock Sale by Elon Musk' },
    { date: '2022-03-22', y: 331.33, text: "Berlin's giga factory opening" },
    { date: '2022-04-12', y: 328.98, text: "Musk's Twitter acquisition" },
    { date: '2023-09-16', y: 265.28, text: '5 million cars produced' },
    { date: '2024-11-05', y: 251.44, text: 'Trump wins elections' },
]

// Helper to extract text content from UIMessage parts
function getMessageText(parts: Array<{ type: string; content?: string }>): string {
    return parts
        .filter(p => p.type === 'text')
        .map(p => p.content || '')
        .join('')
}

// Connection to backend SSE endpoint
const connection = fetchServerSentEvents('/api/chat')

export default function App() {
    const [chartData, setChartData] = useState<[number, number][]>([])
    const [backendConnected, setBackendConnected] = useState(false)
    const [confidence, setConfidence] = useState<number | null>(null)
    const [aiAnnotations, setAiAnnotations] = useState<AnnotationLabel[]>([])
    const chartRef = useRef<StockChartRef>(null)

    // TanStack AI Chat hook
    const { messages, sendMessage, isLoading, clear, error } = useChat({
        connection,
        onFinish: (message) => {
            // Parse the response when finished
            if (message.role === 'assistant') {
                const text = getMessageText(message.parts)
                try {
                    const jsonMatch = text.match(/\{[\s\S]*\}/)
                    if (jsonMatch) {
                        const analysis = JSON.parse(jsonMatch[0]) as ChartAnalysisResponse
                        setConfidence(analysis.confidence)
                        setAiAnnotations(analysis.annotations || [])
                        chartRef.current?.applyAnalysis(analysis)
                    }
                } catch (parseError) {
                    console.error('Failed to parse AI response:', parseError)
                }
            }
        },
        onError: (err) => {
            console.error('Chat error:', err)
        }
    })

    // Check backend status
    useEffect(() => {
        const checkBackend = async () => {
            try {
                const response = await fetch('/api/')
                if (response.ok) {
                    const data = await response.json()
                    setBackendConnected(data.openai_available || false)
                } else {
                    setBackendConnected(false)
                }
            } catch {
                setBackendConnected(false)
            }
        }
        checkBackend()
        const interval = setInterval(checkBackend, 30000)
        return () => clearInterval(interval)
    }, [])

    // Load chart data
    useEffect(() => {
        const data = generateMockData()
        setChartData(data)
    }, [])

    const analyzeWithAI = useCallback(async () => {
        if (chartData.length === 0) return

        // Sample data for token efficiency
        const sampleSize = Math.min(100, chartData.length)
        const step = Math.floor(chartData.length / sampleSize) || 1
        const sampledData = chartData.filter((_, i) => i % step === 0).slice(0, sampleSize)

        // Calculate statistics
        const values = chartData.map(d => d[1]).filter(v => v != null)
        const stats = {
            total_points: chartData.length,
            sampled_points: sampledData.length,
            min_value: Math.round(Math.min(...values) * 100) / 100,
            max_value: Math.round(Math.max(...values) * 100) / 100,
            start_value: Math.round(values[0] * 100) / 100,
            end_value: Math.round(values[values.length - 1] * 100) / 100,
            change_percent: values[0] !== 0
                ? Math.round(((values[values.length - 1] - values[0]) / values[0]) * 10000) / 100
                : 0
        }

        // Format data for AI
        const formattedData = sampledData.slice(0, 50).map(([ts, val]) => {
            const date = new Date(ts).toISOString().split('T')[0]
            return `${date}: ${Math.round(val * 100) / 100}`
        })

        const prompt = `Analyser følgende TSLA aksjedata:

STATISTIKK:
${JSON.stringify(stats, null, 2)}

DATA (samplet fra ${stats.total_points} punkter):
${formattedData.join('\n')}

EKSISTERENDE ANNOTASJONER (ikke dupliser):
${JSON.stringify(existingAnnotations.slice(0, 4), null, 2)}

Gi meg en analyse med forslag til NYE annotasjoner, plotBands og en tekstlig oppsummering.
Returner BARE gyldig JSON, ingen annen tekst.`

        await sendMessage(prompt)
    }, [chartData, sendMessage])

    const clearAIAnalysis = useCallback(() => {
        chartRef.current?.clearAIAnnotations()
        setAiAnnotations([])
        setConfidence(null)
    }, [])

    const handleSendMessage = useCallback(async (message: string) => {
        await sendMessage(message)
    }, [sendMessage])

    const handleClearChat = useCallback(() => {
        clear()
        clearAIAnalysis()
    }, [clear, clearAIAnalysis])

    // Convert UIMessages to simple format for ChatPanel
    const chatMessages = messages.map((m, i) => ({
        id: m.id || String(i),
        role: m.role as 'user' | 'assistant' | 'system',
        content: getMessageText(m.parts)
    }))

    return (
        <div className="app">
            <header className="header">
                <div className="header__brand">
                    <div className="header__logo">
                        <Zap size={18} />
                    </div>
                    <h1 className="header__title">Highcharts AI Analyzer</h1>
                    <span className="header__badge">TanStack AI</span>
                </div>
                <div className="header__status">
                    <div className={`status-dot ${backendConnected ? 'connected' : 'error'}`} />
                    <span>{backendConnected ? 'Backend tilkoblet' : 'Venter på backend...'}</span>
                </div>
            </header>

            <main className="main">
                <section className="chart-section">
                    <div className="chart-card">
                        <div className="chart-toolbar">
                            <div className="chart-toolbar__title">
                                <BarChart3 className="chart-toolbar__icon" />
                                TSLA Stock Price (Demo Data)
                            </div>
                            <div className="chart-toolbar__actions">
                                <button
                                    className="btn btn--secondary"
                                    onClick={clearAIAnalysis}
                                >
                                    <Trash2 size={16} />
                                    Fjern AI-analyser
                                </button>
                                <button
                                    className="btn btn--primary"
                                    onClick={analyzeWithAI}
                                    disabled={isLoading || chartData.length === 0 || !backendConnected}
                                >
                                    {isLoading ? (
                                        <>
                                            <div className="spinner" />
                                            Analyserer...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles size={16} />
                                            Analyser med AI
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                        <div className="chart-container">
                            {chartData.length > 0 && (
                                <StockChart
                                    ref={chartRef}
                                    data={chartData}
                                    title="TSLA Stock Price 2017 - 2025"
                                    existingAnnotations={existingAnnotations}
                                />
                            )}
                        </div>
                    </div>

                    {error && (
                        <div className="chat-message chat-message--error" style={{ margin: '1rem' }}>
                            Feil: {error.message}
                        </div>
                    )}
                </section>

                <aside className="sidebar">
                    <StatusPanel
                        backendConnected={backendConnected}
                        dataPoints={chartData.length}
                        confidence={confidence}
                        isAnalyzing={isLoading}
                    />

                    <AnnotationsPanel annotations={aiAnnotations} />

                    <ChatPanel
                        messages={chatMessages}
                        isLoading={isLoading}
                        onSendMessage={handleSendMessage}
                        onClearChat={handleClearChat}
                    />
                </aside>
            </main>
        </div>
    )
}
