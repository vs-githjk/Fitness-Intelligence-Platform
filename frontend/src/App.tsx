import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireRole, useAuth } from './auth'
import { AppShell } from './components/AppShell'
import { EmptyState, LoadingState } from './components/ui'

const LoginPage = lazy(() => import('./pages/AuthPages').then(module => ({ default: module.LoginPage })))
const RegisterPage = lazy(() => import('./pages/AuthPages').then(module => ({ default: module.RegisterPage })))
const DemoPage = lazy(() => import('./pages/AuthPages').then(module => ({ default: module.DemoPage })))
const OnboardingPage = lazy(() => import('./pages/OnboardingPage').then(module => ({ default: module.OnboardingPage })))
const TodayPage = lazy(() => import('./pages/DailyPages').then(module => ({ default: module.TodayPage })))
const CheckInPage = lazy(() => import('./pages/DailyPages').then(module => ({ default: module.CheckInPage })))
const ProgressPage = lazy(() => import('./pages/DailyPages').then(module => ({ default: module.ProgressPage })))
const CoachDashboard = lazy(() => import('./components/DailyCoach').then(module => ({ default: module.CoachDashboardPage })))
const CoachTraineePage = lazy(() => import('./components/DailyCoach').then(module => ({ default: module.CoachTraineeLongitudinalPage })))
const CoachInvitesPage = lazy(() => import('./pages/CoachInvitesPage').then(module => ({ default: module.CoachInvitesPage })))
const ExerciseLibrary = lazy(() => import('./pages/ProgrammingPages').then(module => ({ default: module.ExerciseLibrary })))
const ExerciseEditor = lazy(() => import('./pages/ProgrammingPages').then(module => ({ default: module.ExerciseEditor })))
const TemplateLibrary = lazy(() => import('./pages/ProgrammingPages').then(module => ({ default: module.TemplateLibrary })))
const TemplateBuilder = lazy(() => import('./pages/ProgrammingPages').then(module => ({ default: module.TemplateBuilder })))

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
  return <Suspense fallback={<div className="mx-auto max-w-4xl p-6"><LoadingState label="Loading page" /></div>}><Routes><Route path="/" element={<Home />} /><Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} /><Route path="/demo" element={<DemoPage />} /><Route path="/onboarding" element={<RequireRole role="trainee"><OnboardingPage /></RequireRole>} /><Route path="/trainee/dashboard" element={<RequireRole role="trainee"><TodayPage /></RequireRole>} /><Route path="/trainee/today" element={<RequireRole role="trainee"><TodayPage /></RequireRole>} /><Route path="/trainee/check-in" element={<RequireRole role="trainee"><CheckInPage /></RequireRole>} /><Route path="/trainee/progress" element={<RequireRole role="trainee"><ProgressPage /></RequireRole>} /><Route path="/coach/dashboard" element={<RequireRole role="coach"><CoachDashboard /></RequireRole>} /><Route path="/coach/invites" element={<RequireRole role="coach"><CoachInvitesPage /></RequireRole>} /><Route path="/coach/programming" element={<Navigate to="/coach/programming/exercises" replace />} /><Route path="/coach/programming/exercises" element={<RequireRole role="coach"><ExerciseLibrary /></RequireRole>} /><Route path="/coach/programming/exercises/:exerciseId" element={<RequireRole role="coach"><ExerciseEditor /></RequireRole>} /><Route path="/coach/programming/templates" element={<RequireRole role="coach"><TemplateLibrary /></RequireRole>} /><Route path="/coach/programming/templates/:templateId" element={<RequireRole role="coach"><TemplateBuilder /></RequireRole>} /><Route path="/coach/trainees/:traineeId" element={<RequireRole role="coach"><CoachTraineePage /></RequireRole>} /><Route path="*" element={<NotFound />} /></Routes></Suspense>
}
