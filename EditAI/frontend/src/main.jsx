import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React ErrorBoundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#101115] text-[#d0d4de] p-6 space-y-4 font-mono select-none">
          <div className="w-12 h-12 rounded-full bg-[#d4483b]/20 border border-[#d4483b]/50 flex items-center justify-center text-[#e85c4f] text-xl font-bold">
            !
          </div>
          <h2 className="text-base font-semibold text-white">Application Render Notice</h2>
          <p className="text-xs text-[#8a91a0] max-w-md text-center">
            {this.state.error?.message || "An unexpected UI error occurred."}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="px-4 py-2 rounded bg-[#202834] hover:bg-[#2b3646] border border-[#3b4c63] text-xs text-[#7ea5dc] transition font-sans"
          >
            Reload Editor
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
