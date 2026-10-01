import { Component } from 'react'

/**
 * Catches render-time errors so a crash shows a readable message instead of a
 * blank page. It also offers a way back without a full reload.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null, info: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    this.setState({ info })
    console.error('Application error:', error, info)
  }

  render() {
    const { error, info } = this.state
    if (!error) return this.props.children

    return (
      <div className="error-screen">
        <div className="error-card">
          <h1 className="error-title">Something went wrong</h1>
          <p className="error-text">
            The app ran into a problem and could not keep rendering.
          </p>

          <div className="error-detail">
            <span className="error-detail-label">Error</span>
            <pre className="error-detail-body">{String(error.message || error)}</pre>
          </div>

          {info?.componentStack && (
            <details className="error-stack">
              <summary>Where it happened</summary>
              <pre className="error-detail-body">{info.componentStack}</pre>
            </details>
          )}

          <div className="error-actions">
            <button className="btn btn-primary" onClick={() => this.setState({ error: null, info: null })}>
              Try again
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => window.location.assign('/login')}
            >
              Back to sign in
            </button>
          </div>
        </div>
      </div>
    )
  }
}
