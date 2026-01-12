import { useRef, useCallback, useImperativeHandle, forwardRef } from 'react'
import Highcharts from 'highcharts'
import HighchartsAnnotations from 'highcharts/modules/annotations'
import HighchartsReact from 'highcharts-react-official'
import type { ChartAnalysisResponse, ExistingAnnotation } from '../types'

// Initialize annotations module
HighchartsAnnotations(Highcharts)

// Set Highcharts theme
Highcharts.setOptions({
    chart: {
        backgroundColor: 'transparent',
    },
    title: {
        style: { color: '#fafafa', fontFamily: 'Sora' }
    },
    xAxis: {
        labels: { style: { color: '#a1a1aa' } },
        gridLineColor: '#27272a',
        lineColor: '#27272a',
    },
    yAxis: {
        labels: { style: { color: '#a1a1aa' } },
        gridLineColor: '#27272a',
    },
    tooltip: {
        backgroundColor: '#10101a',
        borderColor: '#27272a',
        style: { color: '#e4e4e7' }
    },
    legend: {
        itemStyle: { color: '#a1a1aa' }
    }
})

export interface StockChartRef {
    applyAnalysis: (analysis: ChartAnalysisResponse) => void
    clearAIAnnotations: () => void
    getChartData: () => [number, number][]
}

interface StockChartProps {
    data: [number, number][]
    title: string
    existingAnnotations: ExistingAnnotation[]
}

export const StockChart = forwardRef<StockChartRef, StockChartProps>(
    ({ data, title, existingAnnotations }, ref) => {
        const chartRef = useRef<HighchartsReact.RefObject>(null)
        const aiAnnotationIds = useRef<string[]>([])

        const getChart = useCallback(() => chartRef.current?.chart, [])

        const applyAnalysis = useCallback((analysis: ChartAnalysisResponse) => {
            const chart = getChart()
            if (!chart) return

            // Clear previous AI annotations
            aiAnnotationIds.current.forEach(id => {
                try {
                    if (id === 'ai-annotations') {
                        // Find and destroy the annotation
                        const annotations = (chart as unknown as { annotations?: Array<{ options: { id?: string }, destroy: () => void }> }).annotations
                        const ann = annotations?.find(a => a.options.id === id)
                        if (ann) ann.destroy()
                    } else if (id.includes('plotband')) {
                        chart.xAxis[0].removePlotBand(id)
                    } else if (id.includes('plotline')) {
                        chart.xAxis[0].removePlotLine(id)
                    }
                } catch (e) {
                    console.warn('Failed to remove annotation:', id, e)
                }
            })
            aiAnnotationIds.current = []

            // Add new annotations
            if (analysis.annotations && analysis.annotations.length > 0) {
                const annotationId = 'ai-annotations'
                try {
                    chart.addAnnotation({
                        id: annotationId,
                        draggable: '' as Highcharts.AnnotationDraggableValue,
                        labelOptions: {
                            shape: 'connector',
                            style: { fontSize: '10px', fontWeight: 'bold' },
                            backgroundColor: 'rgba(99, 102, 241, 0.9)',
                            borderColor: '#6366f1'
                        },
                        labels: analysis.annotations.map(ann => ({
                            point: {
                                xAxis: 0,
                                yAxis: 0,
                                x: new Date(ann.point.x).getTime(),
                                y: ann.point.y
                            },
                            text: ann.text,
                            x: ann.xOffset || -50,
                            y: ann.yOffset || -30
                        }))
                    })
                    aiAnnotationIds.current.push(annotationId)
                } catch (e) {
                    console.warn('Failed to add annotations:', e)
                }
            }

            // Add plotBands
            if (analysis.plotBands && analysis.plotBands.length > 0) {
                analysis.plotBands.forEach((band, i) => {
                    const bandId = `ai-plotband-${i}`
                    try {
                        chart.xAxis[0].addPlotBand({
                            id: bandId,
                            from: new Date(band.from).getTime(),
                            to: new Date(band.to).getTime(),
                            color: band.color || 'rgba(99, 102, 241, 0.1)',
                            label: {
                                text: band.label || '',
                                style: { color: '#6366f1', fontSize: '10px' }
                            }
                        })
                        aiAnnotationIds.current.push(bandId)
                    } catch (e) {
                        console.warn('Failed to add plotBand:', e)
                    }
                })
            }

            // Add plotLines
            if (analysis.plotLines && analysis.plotLines.length > 0) {
                analysis.plotLines.forEach((line, i) => {
                    const lineId = `ai-plotline-${i}`
                    try {
                        chart.xAxis[0].addPlotLine({
                            id: lineId,
                            value: new Date(line.value).getTime(),
                            color: line.color || '#6366f1',
                            width: line.width || 2,
                            dashStyle: (line.dashStyle as Highcharts.DashStyleValue) || 'Solid',
                            label: {
                                text: line.label || '',
                                style: { color: '#6366f1', fontSize: '10px' }
                            }
                        })
                        aiAnnotationIds.current.push(lineId)
                    } catch (e) {
                        console.warn('Failed to add plotLine:', e)
                    }
                })
            }
        }, [getChart])

        const clearAIAnnotations = useCallback(() => {
            const chart = getChart()
            if (!chart) return

            aiAnnotationIds.current.forEach(id => {
                try {
                    if (id === 'ai-annotations') {
                        const annotations = (chart as unknown as { annotations?: Array<{ options: { id?: string }, destroy: () => void }> }).annotations
                        const ann = annotations?.find(a => a.options.id === id)
                        if (ann) ann.destroy()
                    } else if (id.includes('plotband')) {
                        chart.xAxis[0].removePlotBand(id)
                    } else if (id.includes('plotline')) {
                        chart.xAxis[0].removePlotLine(id)
                    }
                } catch (e) {
                    console.warn('Failed to remove:', id, e)
                }
            })
            aiAnnotationIds.current = []
        }, [getChart])

        useImperativeHandle(ref, () => ({
            applyAnalysis,
            clearAIAnnotations,
            getChartData: () => data
        }), [applyAnalysis, clearAIAnnotations, data])

        // Build existing annotations for Highcharts
        const highchartsAnnotations: Highcharts.AnnotationsOptions[] = existingAnnotations.length > 0 ? [{
            draggable: '' as Highcharts.AnnotationDraggableValue,
            labelOptions: {
                shape: 'connector',
                style: { fontSize: '11px' }
            },
            labels: existingAnnotations.slice(0, 8).map((ann, i) => ({
                point: {
                    xAxis: 0,
                    yAxis: 0,
                    x: new Date(ann.date).getTime(),
                    y: ann.y
                },
                text: ann.text,
                x: (i % 2 === 0) ? -80 : 80,
                y: -30
            }))
        }] : []

        const options: Highcharts.Options = {
            chart: {
                type: 'area',
                zooming: { type: 'x' },
                panning: { enabled: true, type: 'x' },
                panKey: 'shift',
                height: 460
            },
            title: {
                text: title,
                align: 'left'
            },
            credits: { enabled: false },
            annotations: highchartsAnnotations,
            xAxis: {
                type: 'datetime'
            },
            yAxis: {
                title: { text: null },
                labels: { format: '{value} USD' }
            },
            tooltip: {
                pointFormat: '{point.y:.2f} USD',
                shared: true
            },
            legend: { enabled: false },
            series: [{
                type: 'area',
                data: data,
                color: '#6366f1',
                fillColor: {
                    linearGradient: { x1: 0, x2: 0, y1: 0, y2: 1 },
                    stops: [
                        [0, 'rgba(99, 102, 241, 0.3)'],
                        [1, 'rgba(99, 102, 241, 0.02)']
                    ]
                },
                name: 'TSLA',
                marker: { enabled: false },
                threshold: null
            }]
        }

        return (
            <HighchartsReact
                ref={chartRef}
                highcharts={Highcharts}
                options={options}
            />
        )
    }
)

StockChart.displayName = 'StockChart'
