import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { MapPage } from './pages/MapPage'
import { MethodPage } from './pages/MethodPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { ReportPage } from './pages/ReportPage'
import { TermsPage } from './pages/TermsPage'
import { Link, RouterProvider } from './router'
import { useRouter } from './routerContext'

function PageRouter() {
  const { path } = useRouter()

  switch (path) {
    case '/':
      return <HomePage />
    case '/map':
      return <MapPage />
    case '/report':
      return <ReportPage />
    case '/method':
      return <MethodPage />
    case '/terms':
      return <TermsPage />
    case '/privacy':
      return <PrivacyPage />
    default:
      return (
        <div className="py-12 text-left space-y-4">
          <span className="font-mono text-small text-accent font-medium block">
            404 • Page Not Found
          </span>
          <h1 className="text-h1 font-semibold text-text">Page not found</h1>
          <p className="text-body text-text-muted">
            The page you requested does not exist or has been moved.
          </p>
          <Link href="/" className="text-accent underline text-small font-medium">
            ← Return to Home
          </Link>
        </div>
      )
  }
}

export default function App() {
  return (
    <RouterProvider>
      <Layout>
        <PageRouter />
      </Layout>
    </RouterProvider>
  )
}
