import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import ErrorBoundary from './components/ErrorBoundary';
import { BusyProvider } from './context/BusyContext';
import { Skeleton } from './components/ui';

// Auth is on the critical path; everything else splits per route.
import Login from './pages/Login';

const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ImportData = lazy(() => import('./pages/ImportData'));
const FeedbackList = lazy(() => import('./pages/FeedbackList'));
const InsightsDashboard = lazy(() => import('./pages/InsightsDashboard'));
const PRDWorkspace = lazy(() => import('./pages/PRDWorkspace'));
const UserStoriesWorkspace = lazy(() => import('./pages/UserStoriesWorkspace'));
const PrioritizationHub = lazy(() => import('./pages/PrioritizationHub'));
const CopilotChat = lazy(() => import('./pages/CopilotChat'));

const hasToken = () => Boolean(localStorage.getItem('pm_copilot_token'));

/** Sends anyone without a session back to sign-in. */
function RequireAuth({ children }) {
  if (!hasToken()) return <Navigate to="/" replace />;
  return children;
}

function AuthFallback() {
  return (
    <div className="auth-container">
      <div className="auth-card stack stack-md" role="status" aria-label="Loading">
        <Skeleton className="skeleton-title" style={{ height: 26, width: 180 }} />
        <Skeleton className="skeleton-line w-75" />
        <Skeleton className="skeleton-block" style={{ height: 40 }} />
        <Skeleton className="skeleton-block" style={{ height: 40 }} />
        <Skeleton className="skeleton-block" style={{ height: 40 }} />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BusyProvider>
        <Router>
          <Routes>
            {/* Public */}
            <Route
              path="/"
              element={hasToken() ? <Navigate to="/dashboard" replace /> : <Login />}
            />
            <Route
              path="/register"
              element={
                <Suspense fallback={<AuthFallback />}>
                  <Register />
                </Suspense>
              }
            />

            {/* Authenticated shell */}
            <Route
              element={
                <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }
            >
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/import" element={<ImportData />} />
              <Route path="/feedback" element={<FeedbackList />} />
              <Route path="/insights" element={<InsightsDashboard />} />
              <Route path="/prds" element={<PRDWorkspace />} />
              <Route path="/prds/:prdId" element={<PRDWorkspace />} />
              <Route path="/user-stories" element={<UserStoriesWorkspace />} />
              <Route path="/prioritization" element={<PrioritizationHub />} />
              <Route path="/copilot" element={<CopilotChat />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </BusyProvider>
    </ErrorBoundary>
  );
}
