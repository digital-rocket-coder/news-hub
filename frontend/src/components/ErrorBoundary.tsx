import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error("[ErrorBoundary]", error.message, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="flex items-center justify-center h-full p-8 text-center">
            <div>
              <p className="text-2xl mb-3 text-red-400">Something went wrong</p>
              <p className="text-sm text-gray-500">{this.state.error?.message}</p>
              <pre className="text-xs text-gray-600 mt-2 text-left overflow-auto max-h-40 max-w-xl">{this.state.error?.stack}</pre>
              <button
                className="btn-ghost mt-4 text-sm"
                onClick={() => this.setState({ hasError: false, error: null })}
              >
                Try again
              </button>
            </div>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
