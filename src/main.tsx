import React from 'react'
import ReactDOM from 'react-dom/client'
import '@fontsource/vazirmatn/arabic-400.css'
import '@fontsource/vazirmatn/arabic-500.css'
import '@fontsource/vazirmatn/arabic-600.css'
import '@fontsource/vazirmatn/arabic-700.css'
import '@fontsource/vazirmatn/arabic-800.css'
import '@fontsource/vazirmatn/latin-400.css'
import App from './App'
import './styles.css'

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    return this.state.failed ? (
      <div className="boot-screen">
        <h1>نمایش صفحه با مشکل روبه‌رو شد</h1>
        <p>اطلاعات ثبت‌شده روی سرور محفوظ است. صفحه را دوباره باز کنید.</p>
        <button className="button primary" onClick={() => location.reload()}>
          بارگذاری دوباره
        </button>
      </div>
    ) : (
      this.props.children
    )
  }
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
)
