# Highcharts AI Analyzer - TanStack AI

Modern React-grensesnitt for chart-analyse med **TanStack AI** streaming.

## Teknologi

- **@tanstack/ai-react** - React hooks for AI chat med SSE streaming
- **@tanstack/react-query** - Data fetching og caching
- **React 18** - UI framework
- **Highcharts** - Interaktive charts
- **Vite** - Build tool
- **FastAPI** - Python backend med SSE streaming

## Oppsett

### 1. Installer frontend avhengigheter

```bash
cd highchart/tanstack-ui
npm install
```

### 2. Installer backend avhengigheter

```bash
cd server
pip install -r requirements.txt
```

### 3. Konfigurer OpenAI API-nøkkel

Lag en `.env` fil i `server/` mappen:

```
OPENAI_API_KEY=sk-din-api-nokkel-her
```

### 4. Start backend

```bash
cd server
python server.py
```

Backend starter på `http://localhost:8001`

### 5. Start frontend

```bash
npm run dev
```

Frontend starter på `http://localhost:5173`

## Arkitektur

```
tanstack-ui/
├── src/
│   ├── components/
│   │   ├── StockChart.tsx    # Highcharts wrapper
│   │   ├── ChatPanel.tsx     # AI chat interface
│   │   ├── StatusPanel.tsx   # Backend/AI status
│   │   └── AnnotationsPanel.tsx
│   ├── App.tsx             # Hovedkomponent med useChat
│   ├── main.tsx            # Entry point
│   ├── types.ts            # TypeScript types
│   └── index.css           # Global styles
├── server/
│   ├── server.py           # FastAPI SSE backend
│   └── requirements.txt
├── package.json
└── vite.config.ts
```

## TanStack AI Bruk

```typescript
import { useChat, fetchServerSentEvents } from '@tanstack/ai-react'

// Koble til backend SSE endpoint
const connection = fetchServerSentEvents('/api/chat')

function App() {
  const { messages, sendMessage, isLoading, clear } = useChat({
    connection,
    onFinish: (message) => {
      // Prosesser ferdig melding
    }
  })

  // Send melding
  await sendMessage('Analyser disse dataene...')

  // Messages har parts array
  messages.forEach(m => {
    const text = m.parts
      .filter(p => p.type === 'text')
      .map(p => p.content)
      .join('')
  })
}
```

## API Endepunkter

| Endepunkt | Metode | Beskrivelse |
|-----------|--------|-------------|
| `/` | GET | Helse-sjekk |
| `/api/chat` | POST | SSE streaming chat |

## Funksjoner

- ✅ TanStack AI med `useChat` hook
- ✅ SSE streaming fra backend
- ✅ Highcharts annotasjoner
- ✅ Real-time chat interface
- ✅ Konfidensgrad-indikator
