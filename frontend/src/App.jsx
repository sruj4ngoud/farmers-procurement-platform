import AppRoutes from './routes/AppRoutes.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import { LanguageProvider } from './context/LanguageContext.jsx'

export default function App() {
  return (
    <ErrorBoundary>
      <LanguageProvider>
        <AppRoutes />
      </LanguageProvider>
    </ErrorBoundary>
  )
}
