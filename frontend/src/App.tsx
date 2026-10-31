import { useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

type QueryResponse = {
  question: string
  sql: string
  results: Record<string, unknown>[]
  count: number
}

type Message = {
  id: number
  role: 'user' | 'assistant'
  text: string
  response?: QueryResponse
}

const suggestions = [
  'Show me all female customers from Mumbai',
  'List every customer in Delhi',
  'How many customers are from Bengaluru?',
]

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || isLoading) return

    setQuestion('')
    setError('')
    setMessages((current) => [
      ...current,
      { id: Date.now(), role: 'user', text: trimmedQuestion },
    ])
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmedQuestion }),
      })
      const payload = (await response.json()) as QueryResponse & {
        detail?: { message?: string }
      }

      if (!response.ok) {
        throw new Error(payload.detail?.message ?? 'The query could not be completed.')
      }

      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: 'assistant',
          text: `The query returned ${payload.count} row${payload.count === 1 ? '' : 's'}.`,
          response: payload,
        },
      ])
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Queryly home">
          <span className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>queryly</span>
        </a>
        <div className="connection-status">
          <span className="status-dot" />
          Database connected
        </div>
      </header>

      <section className={`chat-panel ${messages.length ? 'has-messages' : ''}`}>
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="welcome-icon" aria-hidden="true">
              <span>✦</span>
            </div>
            <p className="eyebrow">YOUR DATA, SIMPLIFIED</p>
            <h1>Ask your database<br /><em>anything.</em></h1>
            <p className="welcome-copy">
              Turn natural language into clear answers from your customer data.
            </p>
            <div className="suggestions">
              {suggestions.map((suggestion) => (
                <button
                  type="button"
                  className="suggestion"
                  key={suggestion}
                  onClick={() => setQuestion(suggestion)}
                >
                  <span>{suggestion}</span>
                  <span aria-hidden="true">↗</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages" aria-live="polite">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <div className="avatar">{message.role === 'user' ? 'Y' : '✦'}</div>
                <div className="message-content">
                  <span className="message-label">
                    {message.role === 'user' ? 'You' : 'Queryly'}
                  </span>
                  <p>{message.text}</p>
                  {message.response && (
                    <div className="result-card">
                      <div className="result-heading">
                        <strong>Results</strong>
                        <span>{message.response.count} rows</span>
                      </div>
                      {message.response.results.length > 0 ? (
                        <div className="table-wrap">
                          <table>
                            <thead>
                              {Object.keys(message.response.results[0]).map((column) => (
                                <th key={column}>{column.replaceAll('_', ' ')}</th>
                              ))}
                            </thead>
                            <tbody>
                              {message.response.results.map((row, rowIndex) => (
                                <tr key={rowIndex}>
                                  {Object.values(row).map((value, valueIndex) => (
                                    <td key={valueIndex}>{String(value ?? '')}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : <p className="empty-results">No matching customers found.</p>}
                      <details>
                        <summary>View generated SQL</summary>
                        <code>{message.response.sql}</code>
                      </details>
                    </div>
                  )}
                </div>
              </article>
            ))}
            {isLoading && (
              <article className="message assistant">
                <div className="avatar">✦</div>
                <div className="message-content">
                  <span className="message-label">Queryly</span>
                  <p className="typing"><i /><i /><i /></p>
                </div>
              </article>
            )}
          </div>
        )}
      </section>

      <div className="composer-area">
        {error && <p className="error-message" role="alert">{error}</p>}
        <form className="composer" onSubmit={handleSubmit}>
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question about your customers..."
            aria-label="Ask a question about your customers"
            maxLength={1000}
          />
          <button type="submit" className="send-button" disabled={!question.trim() || isLoading} aria-label="Send question">
            <span>→</span>
          </button>
        </form>
        <p className="composer-hint">Queryly can make mistakes. Check important information.</p>
      </div>
      <footer>Built for exploring your data <span>·</span> <a href="/api/health">API status</a></footer>
    </main>
  )
}

export default App
