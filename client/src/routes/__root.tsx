import { createRootRoute, Link, Outlet } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-12">
          <div className="text-center mb-6">
            <Link to="/" className="block">
              <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                Speech2Braille
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-400">
                Offline-First Assistive Communication Platform
              </p>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex justify-center gap-4 mt-6">
            <Link
              to="/"
              className="px-4 py-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors [&.active]:bg-slate-300 dark:[&.active]:bg-slate-600"
              activeProps={{ className: 'bg-slate-300 dark:bg-slate-600' }}
            >
              Text to Braille
            </Link>
            <Link
              to="/speech"
              className="px-4 py-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors [&.active]:bg-slate-300 dark:[&.active]:bg-slate-600"
              activeProps={{ className: 'bg-slate-300 dark:bg-slate-600' }}
            >
              Speech to Braille
            </Link>
          </nav>
        </header>

        <Outlet />
      </div>
    </div>
  ),
})
