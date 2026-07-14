import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireRole, useAuth } from './auth'
import { AppShell } from './components/AppShell'
import { EmptyState, LoadingState } from './components/ui'

const LoginPage = lazy(() => import('./pages/AuthPages').then(module => ({ default: module.LoginPage })))
const RegisterPage = lazy(() => import('./pages/AuthPages').then(module => ({ default: module.RegisterPage })))
const OnboardingPage = lazy(() => import('./pages/OnboardingPage').then(module => ({ default: module.OnboardingPage })))
const TodayPage = lazy(() => import('./pages/DailyPages').then(module => ({ default: module.TodayPage })))
const CheckInPage = lazy(() => import('./pages/DailyPages').then(module => ({ default: module.CheckInPage })))
const ProgressPage = lazy(() => import('./pages/DailyPages').then(module => ({ default: module.ProgressPage })))
const CoachDashboard = lazy(() => import('./components/DailyCoach').then(module => ({ default: module.CoachDashboardPage })))
const CoachTraineePage = lazy(() => import('./components/DailyCoach').then(module => ({ default: module.CoachTraineeLongitudinalPage })))

function Home() {
  const { user } = useAuth()
  return <Navigate to={!user ? '/login' : user.role === 'coach' ? '/coach/dashboard' : '/trainee/today'} replace />
}

function NotFound() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <AppShell><EmptyState title="Page not found" description="This destination is not available in the current milestone." action={<a href={user.role === 'coach' ? '/coach/dashboard' : '/trainee/today'} className="inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-sm font-semibold text-white">Return to overview</a>} /></AppShell>
}

export default function App() {
  return <Suspense fallback={<div className="mx-auto max-w-4xl p-6"><LoadingState label="Loading page" /></div>}><Routes><Route path="/" element={<Home />} /><Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} /><Route path="/onboarding" element={<RequireRole role="trainee"><OnboardingPage /></RequireRole>} /><Route path="/trainee/dashboard" element={<RequireRole role="trainee"><TodayPage /></RequireRole>} /><Route path="/trainee/today" element={<RequireRole role="trainee"><TodayPage /></RequireRole>} /><Route path="/trainee/check-in" element={<RequireRole role="trainee"><CheckInPage /></RequireRole>} /><Route path="/trainee/progress" element={<RequireRole role="trainee"><ProgressPage /></RequireRole>} /><Route path="/coach/dashboard" element={<RequireRole role="coach"><CoachDashboard /></RequireRole>} /><Route path="/coach/trainees/:traineeId" element={<RequireRole role="coach"><CoachTraineePage /></RequireRole>} /><Route path="*" element={<NotFound />} /></Routes></Suspense>
}
