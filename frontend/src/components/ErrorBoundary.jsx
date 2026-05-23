import React from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-4">
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-8 max-w-lg w-full text-center">
            <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-white mb-2">Something went wrong</h1>
            <p className="text-[#94a3b8] mb-6">
              An unexpected error occurred. Please try refreshing the page or report this issue.
            </p>
            {this.state.error && (
              <details className="text-left mb-6">
                <summary className="text-sm text-[#64748b] cursor-pointer hover:text-white transition-colors">
                  Show error details
                </summary>
                <pre className="mt-2 p-3 bg-[#0f172a] rounded-lg text-xs text-red-400 overflow-auto max-h-40">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] hover:bg-[#818cf8] text-white rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="flex items-center gap-2 px-4 py-2 bg-[#334155] hover:bg-[#475569] text-white rounded-lg transition-colors"
              >
                <Home className="w-4 h-4" />
                Reload Page
              </button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
