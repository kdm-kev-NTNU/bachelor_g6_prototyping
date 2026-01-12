import { useRef, useEffect, useState } from 'react'
import { MessageSquare, Send, Trash2, Sparkles } from 'lucide-react'

interface Message {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
}

interface ChatPanelProps {
    messages: Message[]
    isLoading: boolean
    onSendMessage: (message: string) => void
    onClearChat: () => void
}

export function ChatPanel({ messages, isLoading, onSendMessage, onClearChat }: ChatPanelProps) {
    const [input, setInput] = useState('')
    const messagesEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (input.trim() && !isLoading) {
            onSendMessage(input.trim())
            setInput('')
        }
    }

    return (
        <div className="panel chat-panel">
            <div className="panel__header">
                <MessageSquare className="panel__header-icon" />
                <span>AI Analyse</span>
                <button
                    className="btn btn--ghost"
                    onClick={onClearChat}
                    style={{ marginLeft: 'auto', padding: '0.25rem 0.5rem' }}
                    title="Tøm chat"
                >
                    <Trash2 size={14} />
                </button>
            </div>

            <div className="chat-messages">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`chat-message chat-message--${message.role}`}
                    >
                        {message.role === 'assistant' && (
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                marginBottom: '0.5rem',
                                color: 'var(--accent-electric)',
                                fontSize: '0.75rem',
                                fontWeight: 600
                            }}>
                                <Sparkles size={14} />
                                AI Analyse
                            </div>
                        )}
                        <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
                    </div>
                ))}

                {isLoading && (
                    <div className="chat-message chat-message--system">
                        <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
                <form onSubmit={handleSubmit} className="chat-input-wrapper">
                    <textarea
                        className="chat-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Still et spørsmål om chartet..."
                        disabled={isLoading}
                        rows={1}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                handleSubmit(e)
                            }
                        }}
                    />
                    <button
                        type="submit"
                        className="btn btn--primary"
                        disabled={!input.trim() || isLoading}
                    >
                        <Send size={16} />
                    </button>
                </form>
            </div>
        </div>
    )
}
