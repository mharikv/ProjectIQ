import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="card max-w-lg text-center">
            <AlertTriangle className="w-12 h-12 text-warning-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-4">
              The page encountered an error and could not render. Your project data is safe.
            </p>
            {this.state.error && (
              <p className="text-xs text-gray-400 mb-4 font-mono bg-gray-50 p-2 rounded">
                {this.state.error.message}
              </p>
            )}
            <button
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.href = '/?view=in_progress'; }}
              className="btn-primary inline-flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" /> Return to Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
