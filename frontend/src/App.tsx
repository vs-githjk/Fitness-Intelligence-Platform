import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireRole, useAuth } from './auth'
import { LoginPage, RegisterPage } from './pages/AuthPages'
import { CoachDashboard, CoachTraineePage, TraineeDashboard } from './pages/DashboardPages'
import { OnboardingPage } from './pages/OnboardingPage'

function Home() { const { user } = useAuth(); return <Navigate to={!user ? '/login' : user.role === 'coach' ? '/coach/dashboard' : '/trainee/dashboard'} replace /> }
export default function App() { return <Routes><Route path="/" element={<Home/>}/><Route path="/login" element={<LoginPage/>}/><Route path="/register" element={<RegisterPage/>}/><Route path="/onboarding" element={<RequireRole role="trainee"><OnboardingPage/></RequireRole>}/><Route path="/trainee/dashboard" element={<RequireRole role="trainee"><TraineeDashboard/></RequireRole>}/><Route path="/coach/dashboard" element={<RequireRole role="coach"><CoachDashboard/></RequireRole>}/><Route path="/coach/trainees/:traineeId" element={<RequireRole role="coach"><CoachTraineePage/></RequireRole>}/><Route path="*" element={<Home/>}/></Routes> }
