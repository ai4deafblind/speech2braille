import './App.css'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrailleTranslator } from './components/BrailleTranslator'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className="container mx-auto px-4 py-8">
          <header className="text-center mb-12">
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2">
              Speech2Braille
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-400">
              Offline-First Braille Translation System
            </p>
          </header>

          <BrailleTranslator />
        </div>
      </div>
    </QueryClientProvider>
  )
}

export default App
